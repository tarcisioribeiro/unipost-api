#!/usr/bin/env python3
"""
Debug do processamento de documentos
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

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do Elasticsearch Cloud
es_config = {
    'cloud_id': os.getenv('ES_CLOUD_ID'),
    'api_key': (
        os.getenv('ES_API_ID'),
        os.getenv('ES_API_KEY')
    ),
    'timeout': 30,
    'max_retries': 3,
    'retry_on_timeout': True
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
    """Extrai texto relevante de um documento ElasticSearch - TODOS os campos de texto"""
    extracted_texts = []

    def extract_recursive(obj, prefix=''):
        if isinstance(obj, dict):
            for key, value in obj.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, str) and value.strip():
                    cleaned_value = clean_text(value)
                    if cleaned_value and len(cleaned_value) > 3:  # Limiar menor
                        extracted_texts.append(f"{key}: {cleaned_value}")
                elif isinstance(value, (dict, list)):
                    extract_recursive(value, full_key)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    extract_recursive(item, prefix)
                elif isinstance(item, str) and item.strip():
                    cleaned_item = clean_text(item)
                    if cleaned_item and len(cleaned_item) > 3:
                        extracted_texts.append(cleaned_item)
        elif isinstance(obj, str) and obj.strip():
            cleaned_obj = clean_text(obj)
            if cleaned_obj and len(cleaned_obj) > 3:
                extracted_texts.append(cleaned_obj)

    extract_recursive(doc_source)

    # Combina todos os textos encontrados
    combined_text = ' | '.join(extracted_texts)

    # Se não encontrou texto relevante, usa representação JSON limpa
    if not combined_text.strip():
        json_text = json.dumps(doc_source, ensure_ascii=False)[:5000]
        combined_text = clean_text(json_text)

    # Aplica limpeza final no texto combinado
    final_text = clean_text(combined_text)
    
    return final_text[:5000]  # Limite maior para mais conteúdo

def test_document_processing():
    """Testa o processamento de documentos"""
    es_client = Elasticsearch(**es_config)
    
    if not es_client.ping():
        print("❌ Erro conectando ao ES")
        return
        
    print("✅ Conectado ao ES")
    
    # Testa cada índice
    for index in ['braincomercial', 'consultores', 'unibrain']:
        print(f"\n🔍 Testando processamento do índice: {index}")
        
        # Pega um documento de amostra
        response = es_client.search(
            index=index,
            query={"match_all": {}},
            size=1
        )
        
        if len(response['hits']['hits']) == 0:
            print(f"❌ Nenhum documento encontrado em {index}")
            continue
            
        doc = response['hits']['hits'][0]
        doc_id = doc['_id']
        doc_source = doc['_source']
        
        print(f"📄 Documento ID: {doc_id}")
        print(f"📊 Campos disponíveis: {list(doc_source.keys())}")
        
        # Testa extração de texto
        text_content = extract_text_from_document(doc_source)
        
        print(f"📝 Texto extraído - Length: {len(text_content)}")
        print(f"📝 Conteúdo vazio? {not text_content.strip()}")
        print(f"📝 Sample: {text_content[:200]}...")
        
        if not text_content.strip():
            print(f"❌ PROBLEMA: Documento sem conteúdo textual extraível!")
            print(f"   Campos analisados: {list(doc_source.keys())}")
            for key, value in doc_source.items():
                if isinstance(value, str):
                    print(f"   {key}: [{type(value).__name__}] len={len(value)} sample='{value[:50]}...'")
                else:
                    print(f"   {key}: [{type(value).__name__}] {value}")
        else:
            print(f"✅ Documento processável!")

if __name__ == "__main__":
    test_document_processing()