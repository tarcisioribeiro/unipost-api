#!/usr/bin/env python3
"""
Text Formatter Unipost Automation
Formata texto e gera embeddings baseado no business_vectorizer existente
"""

import os
import sys
import logging
import re
from typing import Dict, Any, Optional, List
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# Django setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

import django
django.setup()

# Load environment variables
load_dotenv()

# Logging setup
logger = logging.getLogger(__name__)


class TextFormatter:
    """Formatador de texto e gerador de embeddings"""

    def __init__(self):
        self.model_name = 'models/embedding-001'
        self.gemini_configured = False

    async def initialize(self) -> bool:
        """Inicializa o formatador"""
        try:
            # Configura Google Gemini
            google_api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
            if not google_api_key:
                logger.error("❌ GOOGLE_GEMINI_API_KEY não encontrada")
                return False

            genai.configure(api_key=google_api_key)
            self.gemini_configured = True

            logger.info("📝 Text Formatter inicializado")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Text Formatter: {e}")
            return False

    def clean_text(self, text: str) -> str:
        """Limpa e normaliza texto"""
        if not text:
            return ""

        # Remove caracteres especiais
        text = text.replace('\ufeff', '').replace('\u200b', '').replace('\u00a0', ' ')
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)

        # Normaliza quebras de linha e espaços
        text = re.sub(r'[\r\n]+', ' ', text)
        text = re.sub(r'\s+', ' ', text)

        # Remove padrões indesejados
        text = re.sub(r'\s+[^\w\s]{1,3}\s+', ' ', text)
        text = re.sub(r'[^\w\s]{3,}', ' ', text)
        text = re.sub(r'[-/]{3,}', ' ', text)

        return text.strip()

    def format_for_wordpress(self, scraped_data: Dict[str, Any]) -> Dict[str, Any]:
        """Formata conteúdo para postagem no WordPress"""
        try:
            title = scraped_data.get('title', 'Sem título')
            content = scraped_data.get('content', '')
            images = scraped_data.get('images', [])
            author = scraped_data.get('author', '')
            published_date = scraped_data.get('published_date', '')

            # Limpa e formata título
            clean_title = self.clean_text(title)

            # Limpa e formata conteúdo
            clean_content = self.clean_text(content)

            # Adiciona imagens ao conteúdo se disponível
            if images:
                image_html = []
                for img in images[:3]:  # Máximo 3 imagens
                    img_src = img.get('src', '')
                    img_alt = img.get('alt', clean_title)
                    if img_src:
                        image_html.append(
                            f'<img src="{img_src}" alt="{img_alt}" class="wp-image" />'
                        )

                if image_html:
                    clean_content = '\n'.join(image_html) + '\n\n' + clean_content

            # Formata parágrafos para WordPress
            paragraphs = clean_content.split('\n')
            formatted_paragraphs = []

            for paragraph in paragraphs:
                p = paragraph.strip()
                if p and len(p) > 10:  # Ignora parágrafos muito curtos
                    # Adiciona tags de parágrafo se não tiver
                    if not p.startswith('<'):
                        p = f'<p>{p}</p>'
                    formatted_paragraphs.append(p)

            wordpress_content = '\n\n'.join(formatted_paragraphs)

            # Metadados para WordPress
            wp_metadata = {
                'source_url': scraped_data.get('url', ''),
                'original_author': author,
                'original_date': published_date,
                'scraped_at': scraped_data.get('scraped_at', ''),
                'categories': scraped_data.get('metadata', {}).get('categories', []),
                'keywords': scraped_data.get('metadata', {}).get('keywords', '')
            }

            return {
                'title': clean_title,
                'content': wordpress_content,
                'excerpt': clean_content[:300] + '...' if len(clean_content) > 300 else clean_content,
                'status': 'draft',  # Sempre como rascunho primeiro
                'metadata': wp_metadata,
                'raw_content': clean_content  # Conteúdo limpo sem formatação HTML
            }

        except Exception as e:
            logger.error(f"❌ Erro ao formatar para WordPress: {e}")
            return {}

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Gera embedding usando Google Gemini"""
        try:
            if not self.gemini_configured:
                logger.error("❌ Gemini não configurado")
                return None

            # Limita tamanho do texto
            if len(text) > 2048:
                text = text[:2048] + "..."

            # Gera embedding
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document"
            )

            return result['embedding']

        except Exception as e:
            logger.error(f"❌ Erro ao gerar embedding: {e}")
            return None

    def prepare_embedding_data(self, formatted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara dados para salvamento do embedding"""
        try:
            content = formatted_data.get('raw_content', '')
            title = formatted_data.get('title', '')

            # Texto completo para embedding
            full_text = f"{title}\n\n{content}"
            full_text = self.clean_text(full_text)

            # Gera embedding
            embedding_vector = self.generate_embedding(full_text)
            if not embedding_vector:
                return {}

            # Metadados para embedding
            embedding_metadata = {
                'source_type': 'unipost_automation',
                'original_url': formatted_data.get('metadata', {}).get('source_url', ''),
                'title': title,
                'content_length': len(content),
                'processed_at': datetime.now().isoformat(),
                'wordpress_ready': True,
                'embedding_model': self.model_name
            }

            return {
                'origin': 'webscraping',
                'content': full_text,
                'title': title,
                'embedding_vector': embedding_vector,
                'metadata': embedding_metadata
            }

        except Exception as e:
            logger.error(f"❌ Erro ao preparar dados de embedding: {e}")
            return {}

    async def process_content(self, scraped_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Processa conteúdo completo: formatação + embedding"""
        try:
            logger.info(f"📝 Formatando conteúdo: {scraped_data.get('title', 'N/A')}")

            # 1. Formata para WordPress
            wordpress_data = self.format_for_wordpress(scraped_data)
            if not wordpress_data:
                logger.error("❌ Falha na formatação para WordPress")
                return None

            # 2. Prepara dados de embedding
            embedding_data = self.prepare_embedding_data(wordpress_data)
            if not embedding_data:
                logger.error("❌ Falha na preparação do embedding")
                return None

            # 3. Combina dados
            processed_data = {
                'wordpress': wordpress_data,
                'embedding': embedding_data,
                'source': scraped_data,
                'processed_at': datetime.now().isoformat()
            }

            logger.info(f"✅ Conteúdo processado: {len(wordpress_data.get('content', ''))} caracteres")
            return processed_data

        except Exception as e:
            logger.error(f"❌ Erro no processamento de conteúdo: {e}")
            return None

    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extrai palavras-chave do texto"""
        try:
            # Remove stopwords básicas
            stopwords = {
                'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for',
                'from', 'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on',
                'that', 'the', 'to', 'was', 'were', 'will', 'with', 'the',
                'o', 'a', 'os', 'as', 'um', 'uma', 'e', 'ou', 'mas', 'se',
                'não', 'que', 'de', 'do', 'da', 'dos', 'das', 'em', 'na',
                'no', 'nas', 'nos', 'para', 'por', 'com', 'sem', 'sobre'
            }

            # Extrai palavras
            words = re.findall(r'\b[a-zA-ZÀ-ÿ]{3,}\b', text.lower())

            # Filtra stopwords e conta frequências
            word_freq = {}
            for word in words:
                if word not in stopwords:
                    word_freq[word] = word_freq.get(word, 0) + 1

            # Ordena por frequência
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

            # Retorna top keywords
            return [word for word, freq in sorted_words[:max_keywords]]

        except Exception as e:
            logger.error(f"❌ Erro ao extrair keywords: {e}")
            return []


async def main():
    """Função de teste"""
    formatter = TextFormatter()
    await formatter.initialize()

    # Teste com dados fictícios
    test_data = {
        'title': 'Título de Teste',
        'content': 'Este é um conteúdo de teste para verificar a formatação.',
        'url': 'https://example.com/post',
        'images': [],
        'author': 'Autor Teste',
        'published_date': '2024-01-01'
    }

    result = await formatter.process_content(test_data)
    if result:
        print("✅ Processamento concluído")
        print(f"WordPress: {len(result['wordpress']['content'])} chars")
        print(f"Embedding: {len(result['embedding']['embedding_vector'])} dimensions")
    else:
        print("❌ Falha no processamento")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
