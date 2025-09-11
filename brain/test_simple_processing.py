#!/usr/bin/env python3
"""
Teste simples de processamento de documentos
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
import google.generativeai as genai

# Configuração do Django
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from embeddings.models import Embedding

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração do Google Gemini
GOOGLE_GEMINI_API_KEY = os.getenv('GOOGLE_GEMINI_API_KEY')
genai.configure(api_key=GOOGLE_GEMINI_API_KEY)

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
    
    text = text.replace('\ufeff', '').replace('\u200b', '').replace('\u00a0', ' ')
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    text = re.sub(r'[\r\n]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s+[^\w\s]{1,3}\s+', ' ', text)
    text = re.sub(r'[^\w\s]{3,}', ' ', text)
    text = re.sub(r'[-/]{3,}', ' ', text)
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
                    if cleaned_value and len(cleaned_value) > 3:
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
    combined_text = ' | '.join(extracted_texts)

    if not combined_text.strip():
        json_text = json.dumps(doc_source, ensure_ascii=False)[:5000]
        combined_text = clean_text(json_text)

    final_text = clean_text(combined_text)
    return final_text[:5000]

def generate_embedding(text: str):
    """Gera embedding usando Google Gemini"""
    try:
        if len(text) > 2048:
            text = text[:2048] + "..."
        
        result = genai.embed_content(
            model='models/embedding-001',
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        logger.error(f"Erro ao gerar embedding: {e}")
        return None

def test_simple_processing():
    """Testa processamento simples de 1 documento por índice"""
    es_client = Elasticsearch(**es_config)
    
    if not es_client.ping():
        print("❌ Erro conectando ao ES")
        return
        
    print("✅ Conectado ao ES")
    
    processed_count = 0
    error_count = 0
    
    # Testa cada índice
    for index in ['braincomercial', 'consultores', 'unibrain']:
        print(f"\n🔍 Processando 1 documento do índice: {index}")
        
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
        
        try:
            # Extrai texto do documento
            text_content = extract_text_from_document(doc_source)

            if not text_content.strip():
                print(f"❌ Documento {doc_id} sem conteúdo textual")
                continue

            print(f"📝 Texto extraído - Length: {len(text_content)}")

            # Gera embedding
            embedding_vector = generate_embedding(text_content)

            if embedding_vector is None:
                error_count += 1
                print(f"❌ Erro ao gerar embedding para {doc_id}")
                continue

            print(f"🧠 Embedding gerado - Dimensões: {len(embedding_vector)}")

            # Prepara metadados
            metadata = {
                "elasticsearch_id": doc_id,
                "elasticsearch_index": index,
                "elasticsearch_score": doc.get('_score', 0),
                "source_fields": list(doc_source.keys()),
                "processed_at": "2025-09-11T19:00:00Z",
                "text_length": len(text_content),
                "original_source": doc_source
            }

            # Título baseado no índice e ID
            title = f"{index}: {doc_id}"

            # Salva no banco
            embedding = Embedding.objects.create(
                origin='business_brain',
                content=text_content,
                title=title,
                embedding_vector=embedding_vector,
                metadata=metadata
            )

            processed_count += 1
            print(f"✅ Embedding salvo: {embedding.id} - {title}")

        except Exception as e:
            error_count += 1
            print(f"❌ Erro ao processar documento {doc_id}: {e}")

    print(f"\n📊 RESULTADO FINAL:")
    print(f"   Processados: {processed_count}")
    print(f"   Erros: {error_count}")

if __name__ == "__main__":
    test_simple_processing()