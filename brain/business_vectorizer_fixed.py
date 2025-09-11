#!/usr/bin/env python3
"""
Business Vectorizer CORRIGIDO - Processa TODOS os documentos sem deduplicação
"""

import os
import sys
import json
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import django
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError
import google.generativeai as genai
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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent / 'business_brain_fixed.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuração do Google Gemini
GOOGLE_GEMINI_API_KEY = os.getenv('GOOGLE_GEMINI_API_KEY')
if not GOOGLE_GEMINI_API_KEY:
    logger.error("GOOGLE_GEMINI_API_KEY não encontrada no .env")
    sys.exit(1)

genai.configure(api_key=GOOGLE_GEMINI_API_KEY)

# Configuração do Elasticsearch Cloud
ELASTICSEARCH_CONFIG = {
    'cloud_id': os.getenv('ES_CLOUD_ID'),
    'api_id': os.getenv('ES_API_ID'),
    'api_key': os.getenv('ES_API_KEY')
}

class BusinessVectorizerFixed:
    """Versão corrigida que processa TODOS os documentos"""

    def __init__(self):
        self.model_name = 'models/embedding-001'
        self.es_client = None
        self.processed_count = 0
        self.error_count = 0

    def connect_elasticsearch(self) -> bool:
        """Conecta ao Elasticsearch Cloud"""
        try:
            if not all([ELASTICSEARCH_CONFIG['cloud_id'], ELASTICSEARCH_CONFIG['api_id'], ELASTICSEARCH_CONFIG['api_key']]):
                logger.error("Variáveis do Elasticsearch Cloud não configuradas")
                return False

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

            self.es_client = Elasticsearch(**es_config)

            if self.es_client.ping():
                logger.info("Conexão com Elasticsearch Cloud estabelecida com sucesso")
                return True
            else:
                logger.error("Falha no ping do Elasticsearch Cloud")
                return False

        except Exception as e:
            logger.error(f"Erro ao conectar com Elasticsearch Cloud: {e}")
            return False

    def clean_text(self, text: str) -> str:
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

    def extract_text_from_document(self, doc_source: Dict[str, Any]) -> str:
        """Extrai texto relevante de um documento ElasticSearch - TODOS os campos de texto"""
        extracted_texts = []

        def extract_recursive(obj, prefix=''):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    full_key = f"{prefix}.{key}" if prefix else key
                    if isinstance(value, str) and value.strip():
                        cleaned_value = self.clean_text(value)
                        if cleaned_value and len(cleaned_value) > 3:
                            extracted_texts.append(f"{key}: {cleaned_value}")
                    elif isinstance(value, (dict, list)):
                        extract_recursive(value, full_key)
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, (dict, list)):
                        extract_recursive(item, prefix)
                    elif isinstance(item, str) and item.strip():
                        cleaned_item = self.clean_text(item)
                        if cleaned_item and len(cleaned_item) > 3:
                            extracted_texts.append(cleaned_item)
            elif isinstance(obj, str) and obj.strip():
                cleaned_obj = self.clean_text(obj)
                if cleaned_obj and len(cleaned_obj) > 3:
                    extracted_texts.append(cleaned_obj)

        extract_recursive(doc_source)
        combined_text = ' | '.join(extracted_texts)

        if not combined_text.strip():
            json_text = json.dumps(doc_source, ensure_ascii=False)[:5000]
            combined_text = self.clean_text(json_text)

        final_text = self.clean_text(combined_text)
        return final_text[:5000]

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Gera embedding usando Google Gemini"""
        try:
            if len(text) > 2048:
                text = text[:2048] + "..."

            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document"
            )
            return result['embedding']

        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {e}")
            return None

    def process_all_documents_in_index(self, index: str) -> int:
        """Processa TODOS os documentos de um índice usando scroll"""
        logger.info(f"Iniciando processamento completo do índice: {index}")
        
        processed = 0
        
        try:
            # Busca inicial com scroll
            response = self.es_client.search(
                index=index,
                query={"match_all": {}},
                size=100,  # Batch size
                scroll='10m',  # Timeout maior
                sort=[{"_score": {"order": "desc"}}]
            )
            
            scroll_id = response.get('_scroll_id')
            total_hits = response['hits']['total']['value']
            
            logger.info(f"Total de documentos no índice {index}: {total_hits}")
            
            # Processa primeira página
            for hit in response['hits']['hits']:
                if self.process_single_document(hit, index):
                    processed += 1
                    
                # Log progresso a cada 50 documentos
                if processed % 50 == 0:
                    logger.info(f"Progresso {index}: {processed} documentos processados")
            
            # Continua com scroll
            while scroll_id and len(response['hits']['hits']) > 0:
                try:
                    response = self.es_client.scroll(
                        scroll_id=scroll_id,
                        scroll='10m'
                    )
                    
                    for hit in response['hits']['hits']:
                        if self.process_single_document(hit, index):
                            processed += 1
                            
                        # Log progresso a cada 50 documentos
                        if processed % 50 == 0:
                            logger.info(f"Progresso {index}: {processed} documentos processados")
                    
                except Exception as e:
                    logger.error(f"Erro no scroll para {index}: {e}")
                    break
            
            # Limpa scroll
            if scroll_id:
                try:
                    self.es_client.clear_scroll(scroll_id=scroll_id)
                except:
                    pass
                    
            logger.info(f"Concluído processamento do índice {index}: {processed} documentos processados")
            return processed
            
        except Exception as e:
            logger.error(f"Erro ao processar índice {index}: {e}")
            return processed

    def process_single_document(self, hit: Dict[str, Any], index: str) -> bool:
        """Processa um único documento"""
        try:
            doc_id = hit['_id']
            doc_source = hit['_source']
            
            # Extrai texto do documento
            text_content = self.extract_text_from_document(doc_source)

            if not text_content.strip():
                logger.warning(f"Documento {doc_id} sem conteúdo textual - pulando")
                return False

            # Gera embedding
            embedding_vector = self.generate_embedding(text_content)

            if embedding_vector is None:
                self.error_count += 1
                logger.error(f"Erro ao gerar embedding para {doc_id}")
                return False

            # Prepara metadados
            metadata = {
                "elasticsearch_id": doc_id,
                "elasticsearch_index": index,
                "elasticsearch_score": hit.get('_score', 0),
                "source_fields": list(doc_source.keys()),
                "processed_at": datetime.now().isoformat(),
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

            self.processed_count += 1
            
            # Log apenas os primeiros 10 de cada índice para não spam
            if self.processed_count <= 10:
                logger.info(f"Embedding salvo: {embedding.id} - {title}")

            return True

        except Exception as e:
            logger.error(f"Erro ao processar documento {hit.get('_id', 'N/A')}: {e}")
            self.error_count += 1
            return False

    def run(self):
        """Executa o processo completo de vetorização"""
        logger.info("🚀 Iniciando Business Vectorizer CORRIGIDO - Processamento completo sem deduplicação")

        try:
            # Conecta ao Elasticsearch Cloud
            if not self.connect_elasticsearch():
                logger.error("Falha na conexão com Elasticsearch Cloud. Encerrando...")
                return

            # Processa cada índice
            indices = ['braincomercial', 'consultores', 'unibrain']
            
            for index in indices:
                logger.info(f"\n{'='*50}")
                logger.info(f"📊 PROCESSANDO ÍNDICE: {index}")
                logger.info(f"{'='*50}")
                
                processed = self.process_all_documents_in_index(index)
                logger.info(f"✅ CONCLUÍDO {index}: {processed} documentos processados")

            # Estatísticas finais
            logger.info(f"\n{'='*50}")
            logger.info("🎉 Business Vectorizer CONCLUÍDO!")
            logger.info(f"📈 Total processado: {self.processed_count}")
            logger.info(f"❌ Total de erros: {self.error_count}")
            logger.info(f"✅ Taxa de sucesso: {(self.processed_count / (self.processed_count + self.error_count) * 100):.1f}%" if (self.processed_count + self.error_count) > 0 else "N/A")
            logger.info(f"{'='*50}")

        except Exception as e:
            logger.error(f"Erro durante execução: {e}")

def main():
    """Função principal"""
    vectorizer = BusinessVectorizerFixed()
    vectorizer.run()

if __name__ == "__main__":
    main()