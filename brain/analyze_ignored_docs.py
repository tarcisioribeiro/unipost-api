#!/usr/bin/env python3
"""
Script para analisar documentos que são ignorados pelo Business Vectorizer
"""

import os
import sys
import json
import logging
import re
from pathlib import Path
import django
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

# Configuração do Django
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from embeddings.models import Embedding

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do Elasticsearch Cloud
ELASTICSEARCH_CONFIG = {
    'cloud_id': os.getenv('ES_CLOUD_ID'),
    'api_id': os.getenv('ES_API_ID'),
    'api_key': os.getenv('ES_API_KEY')
}

def clean_text(text: str) -> str:
    """Limpa e normaliza texto removendo caracteres especiais avulsos"""
    if not text:
        return ""
    
    # Remove BOM (Byte Order Mark) e caracteres invisíveis similares
    text = text.replace('\ufeff', '').replace('\u200b', '').replace('\u00a0', ' ')
    
    # Remove caracteres de controle e não imprimíveis
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    # Normaliza quebras de linha e espaços
    text = re.sub(r'[\r\n]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    
    # Remove caracteres especiais isolados (que não fazem parte de palavras)
    text = re.sub(r'\s+[^\w\s]{1,3}\s+', ' ', text)
    
    # Remove sequências de caracteres especiais repetidos
    text = re.sub(r'[^\w\s]{3,}', ' ', text)
    
    # Remove múltiplas barras ou hifens seguidos
    text = re.sub(r'[-/]{3,}', ' ', text)
    
    # Limpa espaços extras no início e fim
    text = text.strip()
    
    return text

def extract_text_from_document(doc_source):
    """Extrai texto relevante de um documento ElasticSearch"""
    # Campos comuns que contêm texto
    text_fields = [
        'message',
        'content',
        'text',
        'body',
        'description',
        'title',
        'summary',
        'question',
        'answer',
        'info',
        'data'
    ]

    extracted_texts = []

    def extract_recursive(obj, prefix=''):
        if isinstance(obj, dict):
            for key, value in obj.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if key.lower() in text_fields and isinstance(value, str):
                    cleaned_value = clean_text(value)
                    if cleaned_value and len(cleaned_value) > 5:
                        extracted_texts.append(f"{key}: {cleaned_value}")
                elif isinstance(value, (dict, list)):
                    extract_recursive(value, full_key)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    extract_recursive(item, prefix)
                elif isinstance(item, str):
                    cleaned_item = clean_text(item)
                    if cleaned_item and len(cleaned_item) > 5:
                        extracted_texts.append(cleaned_item)
        elif isinstance(obj, str) and len(obj) > 10:
            cleaned_obj = clean_text(obj)
            if cleaned_obj and len(cleaned_obj) > 5:
                extracted_texts.append(cleaned_obj)

    extract_recursive(doc_source)

    # Combina todos os textos encontrados
    combined_text = ' | '.join(extracted_texts)

    # Se não encontrou texto relevante, usa representação JSON limpa
    if not combined_text.strip():
        json_text = json.dumps(doc_source, ensure_ascii=False)[:2000]
        combined_text = clean_text(json_text)

    # Aplica limpeza final no texto combinado
    final_text = clean_text(combined_text)
    
    return final_text[:2000]  # Limita tamanho

def connect_elasticsearch():
    """Conecta ao Elasticsearch Cloud"""
    try:
        if not all([ELASTICSEARCH_CONFIG['cloud_id'], ELASTICSEARCH_CONFIG['api_id'], ELASTICSEARCH_CONFIG['api_key']]):
            logger.error("Variáveis do Elasticsearch Cloud não configuradas")
            return None

        es_config = {
            'cloud_id': ELASTICSEARCH_CONFIG['cloud_id'],
            'api_key': (
                ELASTICSEARCH_CONFIG['api_id'],
                ELASTICSEARCH_CONFIG['api_key']
            ),
            'timeout': 30,
            'max_retries': 3,
            'retry_on_timeout': True
        }

        es_client = Elasticsearch(**es_config)

        if es_client.ping():
            logger.info("Conexão com Elasticsearch Cloud estabelecida")
            return es_client
        else:
            logger.error("Falha no ping do Elasticsearch Cloud")
            return None

    except Exception as e:
        logger.error(f"Erro ao conectar com Elasticsearch Cloud: {e}")
        return None

def analyze_document_metadata():
    """Analisa os metadados dos documentos para entender diferenças de processamento"""
    es_client = connect_elasticsearch()
    if not es_client:
        return

    indices = ['braincomercial', 'consultores', 'unibrain']
    
    for index in indices:
        logger.info(f"\n=== Analisando metadados do índice: {index} ===")
        
        try:
            # Estatísticas básicas
            total_response = es_client.count(index=index)
            total_docs = total_response['count']
            logger.info(f"Total de documentos no índice {index}: {total_docs}")
            
            # Análise de campos mais comuns
            mapping_response = es_client.indices.get_mapping(index=index)
            properties = mapping_response[index]['mappings'].get('properties', {})
            logger.info(f"Campos no mapping: {list(properties.keys())}")
            
            # Busca amostra de documentos focando nos metadados
            response = es_client.search(
                index=index,
                query={"match_all": {}},
                size=50,  # Amostra menor para análise detalhada
                _source=True  # Inclui source completo
            )
            
            field_frequency = {}
            metadata_examples = []
            
            for hit in response['hits']['hits']:
                doc_id = hit['_id']
                doc_source = hit['_source']
                doc_score = hit.get('_score', 0)
                
                # Analisa campos presentes
                for field in doc_source.keys():
                    field_frequency[field] = field_frequency.get(field, 0) + 1
                
                # Coleta exemplo detalhado dos primeiros 5 documentos
                if len(metadata_examples) < 5:
                    # Analisa cada campo em detalhes
                    field_analysis = {}
                    for field, value in doc_source.items():
                        field_type = type(value).__name__
                        if isinstance(value, str):
                            field_analysis[field] = {
                                'type': field_type,
                                'length': len(value),
                                'sample': value[:100] if len(value) > 100 else value,
                                'is_empty': not value.strip()
                            }
                        elif isinstance(value, (dict, list)):
                            field_analysis[field] = {
                                'type': field_type,
                                'size': len(value),
                                'sample': str(value)[:100] if len(str(value)) > 100 else str(value)
                            }
                        else:
                            field_analysis[field] = {
                                'type': field_type,
                                'value': value
                            }
                    
                    metadata_examples.append({
                        'id': doc_id,
                        'score': doc_score,
                        'field_count': len(doc_source.keys()),
                        'fields': field_analysis,
                        'raw_source': doc_source
                    })
            
            # Mostra estatísticas de campos
            logger.info(f"\nFrequência de campos (top 10):")
            sorted_fields = sorted(field_frequency.items(), key=lambda x: x[1], reverse=True)
            for field, count in sorted_fields[:10]:
                percentage = (count / len(response['hits']['hits'])) * 100
                logger.info(f"  {field}: {count}/{len(response['hits']['hits'])} docs ({percentage:.1f}%)")
            
            # Mostra exemplos detalhados
            logger.info(f"\n=== Exemplos Detalhados de Metadados ===")
            for i, example in enumerate(metadata_examples, 1):
                logger.info(f"\nEXEMPLO {i} - DOC ID: {example['id']}")
                logger.info(f"SCORE: {example['score']}")
                logger.info(f"TOTAL DE CAMPOS: {example['field_count']}")
                
                logger.info("ANÁLISE POR CAMPO:")
                for field, analysis in example['fields'].items():
                    if analysis.get('is_empty'):
                        logger.info(f"  {field}: [{analysis['type']}] VAZIO - length: {analysis['length']}")
                    elif analysis['type'] == 'str':
                        logger.info(f"  {field}: [{analysis['type']}] length: {analysis['length']} - '{analysis['sample']}'")
                    else:
                        logger.info(f"  {field}: [{analysis['type']}] {analysis.get('size', 'N/A')} - {analysis.get('sample', analysis.get('value', 'N/A'))}")
                
                # Verifica se seria processado pelo extrator de texto
                text_content = extract_text_from_document(example['raw_source'])
                logger.info(f"TEXTO EXTRAÍDO: {'SIM' if text_content.strip() else 'NÃO'} - Length: {len(text_content)} - Sample: '{text_content[:100]}...'")
                
        except Exception as e:
            logger.error(f"Erro ao analisar metadados {index}: {e}")

def check_database_stats():
    """Verifica estatísticas do banco de dados"""
    logger.info(f"\n=== Estatísticas do Banco ===")
    
    total_embeddings = Embedding.objects.filter(origin='business_brain').count()
    logger.info(f"Total de embeddings business_brain: {total_embeddings}")
    
    # Agrupa por índice
    from django.db.models import Count
    stats_by_index = Embedding.objects.filter(origin='business_brain').values('metadata__elasticsearch_index').annotate(count=Count('id'))
    
    for stat in stats_by_index:
        index = stat['metadata__elasticsearch_index']
        count = stat['count']
        logger.info(f"Índice {index}: {count} embeddings")

if __name__ == "__main__":
    check_database_stats()
    analyze_document_metadata()