#!/usr/bin/env python3
"""
Business Vectorizer - Conecta ao ElasticSearch e gera embeddings
para Business Brain
Executa via crontab a cada 10 minutos para sincronizar dados corporativos
"""

import os
import sys
import json
import hashlib
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

# Agora podemos importar o modelo após configurar o Django
from embeddings.models import Embedding

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent / 'business_brain.log'),
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


class BusinessVectorizer:
    """Classe para vetorizar dados corporativos do ElasticSearch"""

    def __init__(self):
        self.model_name = 'models/embedding-001'
        self.es_client = None
        self.processed_count = 0
        self.error_count = 0
        self.last_run_file = Path(__file__).parent / 'last_run.txt'

    def connect_elasticsearch(self) -> bool:
        """Conecta ao Elasticsearch Cloud"""
        try:
            # Validação das variáveis necessárias
            if not all([ELASTICSEARCH_CONFIG['cloud_id'], ELASTICSEARCH_CONFIG['api_id'], ELASTICSEARCH_CONFIG['api_key']]):
                logger.error(
                    "Variáveis do Elasticsearch Cloud não configuradas"
                )
                return False

            # Configuração da conexão com Elasticsearch Cloud
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

            # Testa a conexão
            if self.es_client.ping():
                logger.info(
                    "Conexão com Elasticsearch Cloud estabelecida com sucesso"
                )
                return True
            else:
                logger.error("Falha no ping do Elasticsearch Cloud")
                return False

        except ConnectionError as e:
            logger.error(f"Erro de conexão com Elasticsearch Cloud: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro ao conectar com Elasticsearch Cloud: {e}")
            return False

    def get_all_indices(self) -> List[str]:
        """Obtém todos os índices disponíveis no Elasticsearch Cloud"""
        try:
            # Lista todos os índices
            indices_response = self.es_client.indices.get_alias()
            all_indices = [
                index for index in indices_response.keys()
                if not index.startswith('.') and not index.startswith('_')
            ]

            logger.info(
                f"Encontrados {len(all_indices)} índices: {all_indices}"
            )
            return all_indices

        except Exception as e:
            logger.error(f"Erro ao obter índices: {e}")
            return []

    def get_last_run_timestamp(self) -> Optional[datetime]:
        """Obtém timestamp da última execução"""
        try:
            if self.last_run_file.exists():
                with open(self.last_run_file, 'r') as f:
                    timestamp_str = f.read().strip()
                    return datetime.fromisoformat(timestamp_str)
            return None
        except Exception as e:
            logger.warning(f"Erro ao ler último timestamp: {e}")
            return None

    def save_last_run_timestamp(self):
        """Salva timestamp da execução atual"""
        try:
            with open(self.last_run_file, 'w') as f:
                f.write(datetime.now().isoformat())
        except Exception as e:
            logger.error(f"Erro ao salvar timestamp: {e}")

    def generate_content_hash(self, content: str) -> str:
        """Gera hash único baseado no conteúdo normalizado"""
        # Normaliza o conteúdo para detectar duplicatas de texto similar
        normalized = re.sub(r'\s+', ' ', content.lower().strip())
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]
    
    def generate_document_hash(self, doc_content: str, doc_id: str, index: str) -> str:
        """Gera hash único para o documento completo"""
        # Combina conteúdo + ID + índice para identificar documento único
        full_content = f"{index}:{doc_id}:{doc_content}"
        return hashlib.sha256(full_content.encode('utf-8')).hexdigest()[:16]

    def search_documents_in_index(
            self,
            index: str,
            last_run: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Busca documentos em um índice específico"""
        try:
            # Query base para buscar todos os documentos
            query = {"match_all": {}}

            # Se há uma última execução, busca apenas documentos modificados
            if last_run:
                query = {
                    "range": {
                        "@timestamp": {
                            "gte": last_run.isoformat()
                        }
                    }
                }

            # Busca com scroll para grandes volumes
            response = self.es_client.search(
                index=index,
                query=query,
                size=100,  # Tamanho do batch
                scroll='2m',  # Tempo de vida do cursor
                sort=[{"_score": {"order": "desc"}}]
            )

            documents = []
            scroll_id = response.get('_scroll_id')

            # Processa primeira página
            for hit in response['hits']['hits']:
                documents.append({
                    'id': hit['_id'],
                    'index': index,
                    'source': hit['_source'],
                    'score': hit.get('_score', 0)
                })

            # Continua com scroll se há mais documentos
            while scroll_id and len(response['hits']['hits']) > 0:
                try:
                    response = self.es_client.scroll(
                        scroll_id=scroll_id,
                        scroll='2m'
                    )

                    for hit in response['hits']['hits']:
                        documents.append({
                            'id': hit['_id'],
                            'index': index,
                            'source': hit['_source'],
                            'score': hit.get('_score', 0)
                        })

                except Exception as e:
                    logger.warning(f"Erro no scroll para índice {index}: {e}")
                    break

            # Limpa o cursor
            if scroll_id:
                try:
                    self.es_client.clear_scroll(scroll_id=scroll_id)
                except:
                    pass

            logger.info(
                f"Encontrados {len(documents)} documentos no índice {index}"
            )
            return documents

        except Exception as e:
            logger.error(f"Erro ao buscar documentos no índice {index}: {e}")
            return []

    def clean_text(self, text: str) -> str:
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

    def extract_text_from_document(self, doc_source: Dict[str, Any]) -> str:
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
                        cleaned_value = self.clean_text(value)
                        if cleaned_value and len(cleaned_value) > 5:
                            extracted_texts.append(f"{key}: {cleaned_value}")
                    elif isinstance(value, (dict, list)):
                        extract_recursive(value, full_key)
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, (dict, list)):
                        extract_recursive(item, prefix)
                    elif isinstance(item, str):
                        cleaned_item = self.clean_text(item)
                        if cleaned_item and len(cleaned_item) > 5:
                            extracted_texts.append(cleaned_item)
            elif isinstance(obj, str) and len(obj) > 10:
                cleaned_obj = self.clean_text(obj)
                if cleaned_obj and len(cleaned_obj) > 5:
                    extracted_texts.append(cleaned_obj)

        extract_recursive(doc_source)

        # Combina todos os textos encontrados
        combined_text = ' | '.join(extracted_texts)

        # Se não encontrou texto relevante, usa representação JSON limpa
        if not combined_text.strip():
            json_text = json.dumps(doc_source, ensure_ascii=False)[:2000]
            combined_text = self.clean_text(json_text)

        # Aplica limpeza final no texto combinado
        final_text = self.clean_text(combined_text)
        
        return final_text[:2000]  # Limita tamanho

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Gera embedding usando Google Gemini"""
        try:
            # Limita tamanho do texto
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

    def content_already_exists(self, content_hash: str) -> bool:
        """Verifica se conteúdo similar já foi processado"""
        return Embedding.objects.filter(
            origin='business_brain',
            metadata__content_hash=content_hash
        ).exists()
    
    def document_already_exists(self, doc_hash: str) -> bool:
        """Verifica se documento específico já foi processado"""
        return Embedding.objects.filter(
            origin='business_brain',
            metadata__document_hash=doc_hash
        ).exists()

    def process_documents(
            self,
            documents: List[Dict[str, Any]],
            index_name: str
    ) -> int:
        """Processa documentos e gera embeddings"""
        processed = 0

        for doc in documents:
            try:
                # Extrai texto do documento
                text_content = self.extract_text_from_document(doc['source'])

                if not text_content.strip():
                    logger.warning(
                        f"Documento {doc['id']} sem conteúdo textual"
                    )
                    continue

                # Gera hashes para detecção de duplicatas
                content_hash = self.generate_content_hash(text_content)
                doc_hash = self.generate_document_hash(text_content, doc['id'], index_name)

                # Verifica se conteúdo similar já existe
                if self.content_already_exists(content_hash):
                    logger.debug(f"Conteúdo similar já processado para documento {doc['id']}")
                    continue

                # Verifica se documento específico já foi processado
                if self.document_already_exists(doc_hash):
                    logger.debug(f"Documento {doc['id']} já processado")
                    continue

                # Gera embedding
                embedding_vector = self.generate_embedding(text_content)

                if embedding_vector is None:
                    self.error_count += 1
                    continue

                # Prepara metadados
                metadata = {
                    "elasticsearch_id": doc['id'],
                    "elasticsearch_index": index_name,
                    "elasticsearch_score": doc.get('score', 0),
                    "document_hash": doc_hash,
                    "content_hash": content_hash,
                    "source_fields": list(doc['source'].keys()),
                    "processed_at": datetime.now().isoformat(),
                    "text_length": len(text_content),
                    "original_source": doc['source']
                }

                # Título baseado no índice e ID
                title = f"{index_name}: {doc['id']}"

                # Salva no banco
                embedding = Embedding.objects.create(
                    origin='business_brain',
                    content=text_content,
                    title=title,
                    embedding_vector=embedding_vector,
                    metadata=metadata
                )

                processed += 1
                self.processed_count += 1

                logger.info(f"Embedding salvo: {embedding.id} - {title}")

            except Exception as e:
                logger.error(
                    f"Erro ao processar documento {doc.get('id', 'N/A')}: {e}"
                )
                self.error_count += 1

        return processed

    def run(self):
        """Executa o processo completo de vetorização do Business Brain"""
        logger.info("Iniciando Business Vectorizer...")

        try:
            # Conecta ao Elasticsearch Cloud
            if not self.connect_elasticsearch():
                logger.error(
                    "Falha na conexão com Elasticsearch Cloud. Encerrando..."
                )
                return

            # Obtém timestamp da última execução
            last_run = self.get_last_run_timestamp()
            if last_run:
                logger.info(f"Última execução: {last_run}")
            else:
                logger.info(
                    "Primeira execução - processando todos os documentos"
                )

            # Obtém todos os índices
            indices = self.get_all_indices()

            if not indices:
                logger.warning(
                    "Nenhum índice encontrado no Elasticsearch Cloud"
                )
                return

            # Processa cada índice
            for index in indices:
                logger.info(f"Processando índice: {index}")

                # Busca documentos no índice
                documents = self.search_documents_in_index(index, last_run)

                if not documents:
                    logger.info(
                        f"Nenhum documento novo encontrado no índice {index}")
                    continue

                # Processa documentos e gera embeddings
                processed = self.process_documents(documents, index)

                logger.info(f"""Processados {processed} documentos do índice {
                    index
                }""")

            # Salva timestamp da execução
            self.save_last_run_timestamp()

            # Estatísticas finais
            logger.info("Business Vectorizer concluído!")
            logger.info(f"Total processado: {self.processed_count}")
            logger.info(f"Total de erros: {self.error_count}")

        except Exception as e:
            logger.error(f"Erro durante execução: {e}")


def main():
    """Função principal"""
    vectorizer = BusinessVectorizer()
    vectorizer.run()


if __name__ == "__main__":
    main()
