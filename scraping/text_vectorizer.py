#!/usr/bin/env python3
"""
Text Vectorizer - Processa JSONs do WebScraping e gera embeddings usando
Google Gemini
"""

import os
import sys
import json
import glob
import logging
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

import django
import google.generativeai as genai
from dotenv import load_dotenv

# Configuração do Django
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

# Django imports after setup
from embeddings.models import Embedding

# Carrega variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent / 'vectorizer.log'),
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


class TextVectorizer:
    """Classe para vetorizar textos usando Google Gemini"""

    def __init__(self):
        self.model_name = 'models/embedding-001'
        self.processed_count = 0
        self.error_count = 0

    def find_json_files(self) -> List[str]:
        """Encontra todos os arquivos JSON de scraping"""
        scraping_dir = Path(__file__).parent
        # Procura por arquivos de scraping (tanto originais quanto simples)
        patterns = [
            "scraping_results_*.json",
            "simple_scraping_results_*.json"
        ]

        json_files = []
        for pattern in patterns:
            files = glob.glob(str(scraping_dir / pattern))
            json_files.extend(files)

        logger.info(
            f"Encontrados {len(json_files)} arquivos JSON para processar"
        )
        return json_files

    def load_json_data(self, file_path: str) -> List[Dict[str, Any]]:
        """Carrega dados de um arquivo JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Carregados {len(data)} registros de {file_path}")
            return data
        except Exception as e:
            logger.error(f"Erro ao carregar {file_path}: {e}")
            return []

    def generate_embedding(self, text: str) -> List[float]:
        """Gera embedding usando Google Gemini"""
        try:
            # Remove texto muito longo (máximo 2048 caracteres para evitar
            # limite da API)
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

    def chunk_text(self, text: str, max_length: int = 1000) -> List[str]:
        """Divide texto em chunks menores se necessário"""
        if len(text) <= max_length:
            return [text]

        chunks = []
        words = text.split()
        current_chunk = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1  # +1 para espaço

            if current_length + word_length > max_length:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = [word]
                    current_length = word_length
                else:
                    # Palavra muito longa, adiciona mesmo assim
                    chunks.append(word)
                    current_length = 0
            else:
                current_chunk.append(word)
                current_length += word_length

        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks

    def process_scraped_data(self, scraped_data: List[Dict[str, Any]]) -> int:
        """Processa dados do scraping e salva embeddings no banco"""
        processed = 0

        for item in scraped_data:
            try:
                site_name = item.get('site_name', 'N/A')
                site_url = item.get('site_url', '')
                content = item.get('content', '')
                status = item.get('status', 'unknown')

                # Pula itens com erro
                if status != 'success' or not content:
                    logger.warning(
                        f"Pulando item de {site_name}: status={status}"
                    )
                    continue

                # Converte content para string se necessário
                if isinstance(content, dict) or isinstance(content, list):
                    content = json.dumps(content, ensure_ascii=False)

                content_str = str(content)

                # Divide em chunks se necessário
                chunks = self.chunk_text(content_str)

                for idx, chunk in enumerate(chunks):
                    # Gera embedding
                    embedding_vector = self.generate_embedding(chunk)

                    if embedding_vector is None:
                        self.error_count += 1
                        continue

                    # Prepara metadados
                    metadata = {
                        "site_name": site_name,
                        "site_url": site_url,
                        "url": item.get('url'),  # URL específica da página
                        "scraped_at": item.get('scraped_at'),
                        "chunk_index": idx,
                        "total_chunks": len(chunks),
                        "processed_at": datetime.now().isoformat()
                    }

                    # Título
                    title = f"{site_name}"
                    if len(chunks) > 1:
                        title += f" (Parte {idx + 1}/{len(chunks)})"

                    # Salva no banco
                    embedding = Embedding.objects.create(
                        origin='webscraping',
                        content=chunk,
                        title=title,
                        embedding_vector=embedding_vector,
                        metadata=metadata
                    )

                    processed += 1
                    self.processed_count += 1

                    logger.info(f"Embedding salvo: {embedding.id} - {title}")

            except Exception as e:
                logger.error(
                    f"Erro ao processar item de "
                    f"{item.get('site_name', 'N/A')}: {e}"
                )
                self.error_count += 1

        return processed

    def remove_processed_file(self, file_path: str):
        """Remove arquivo JSON após processamento"""
        try:
            os.remove(file_path)
            logger.info(f"Arquivo removido: {file_path}")
        except Exception as e:
            logger.error(f"Erro ao remover arquivo {file_path}: {e}")

    def run(self):
        """Executa o processo completo de vetorização"""
        logger.info("Iniciando Text Vectorizer...")

        try:
            # Encontra arquivos JSON
            json_files = self.find_json_files()

            if not json_files:
                logger.info("Nenhum arquivo JSON encontrado para processar")
                return

            # Processa cada arquivo
            for json_file in json_files:
                logger.info(f"Processando arquivo: {json_file}")

                # Carrega dados
                scraped_data = self.load_json_data(json_file)

                if not scraped_data:
                    logger.warning(f"Nenhum dado encontrado em {json_file}")
                    continue

                # Processa e salva embeddings
                processed = self.process_scraped_data(scraped_data)

                logger.info(f"Processados {processed} itens de {json_file}")

                # Remove arquivo após processamento bem-sucedido
                if processed > 0:
                    self.remove_processed_file(json_file)

            # Estatísticas finais
            logger.info("Vectorização concluída!")
            logger.info(f"Total processado: {self.processed_count}")
            logger.info(f"Total de erros: {self.error_count}")

        except Exception as e:
            logger.error(f"Erro durante execução: {e}")


def main():
    """Função principal"""
    vectorizer = TextVectorizer()
    vectorizer.run()


if __name__ == "__main__":
    main()
