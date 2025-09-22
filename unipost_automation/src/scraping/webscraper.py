#!/usr/bin/env python3
"""
Webscraper Unipost Automation
Baseado no webscraper existente, otimizado para detecção e coleta de posts
"""

import os
import sys
import asyncio
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup

# Django setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

import django
django.setup()

# from sites.models import Site  # Não usado neste módulo

# Logging setup
logger = logging.getLogger(__name__)


class UnipostWebScraper:
    """Webscraper especializado para automação do Unipost"""

    def __init__(self):
        self.web_client: Optional[httpx.AsyncClient] = None
        self.scraped_data: List[Dict[str, Any]] = []

    async def initialize(self) -> bool:
        """Inicializa o webscraper"""
        try:
            self.web_client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    'User-Agent': (
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/91.0.4472.124 Safari/537.36'
                    )
                }
            )
            logger.info("🌐 Webscraper inicializado")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao inicializar webscraper: {e}")
            return False

    async def close(self) -> None:
        """Fecha o cliente web"""
        if self.web_client:
            await self.web_client.aclose()

    def normalize_url(self, url: str, base_url: str = None) -> str:
        """Normaliza URL"""
        if base_url:
            url = urljoin(base_url, url)

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        if normalized.endswith('/') and len(parsed.path) > 1:
            normalized = normalized[:-1]

        return normalized

    def extract_post_links(self, soup: BeautifulSoup, base_url: str,
                          site_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrai links de posts da página"""
        posts = []

        # Seletores comuns para posts
        post_selectors = [
            'article a[href]',
            '.post a[href]',
            '.entry a[href]',
            '.blog-post a[href]',
            'h2 a[href]',
            'h3 a[href]',
            '.post-title a[href]',
            '.entry-title a[href]'
        ]

        # Usa seletores customizados se disponível
        custom_selectors = site_config.get('post_selectors', '')
        if custom_selectors:
            post_selectors = custom_selectors.strip().split('\n')

        found_links = set()

        for selector in post_selectors:
            selector = selector.strip()
            if not selector:
                continue

            try:
                elements = soup.select(selector)
                for element in elements:
                    href = element.get('href')
                    if href:
                        full_url = self.normalize_url(href, base_url)

                        # Evita duplicatas
                        if full_url in found_links:
                            continue
                        found_links.add(full_url)

                        # Extrai título
                        title = element.get_text().strip()
                        if not title:
                            # Tenta pegar título do elemento pai
                            parent = element.parent
                            if parent:
                                title = parent.get_text().strip()

                        # Filtra URLs irrelevantes
                        if self.is_valid_post_url(full_url, base_url):
                            posts.append({
                                'url': full_url,
                                'title': title[:200] if title else 'Sem título',
                                'discovered_at': datetime.now().isoformat(),
                                'source_site': site_config.get('name', 'N/A')
                            })

            except Exception as e:
                logger.warning(f"⚠️  Erro ao processar seletor {selector}: {e}")
                continue

        return posts

    def is_valid_post_url(self, url: str, base_url: str) -> bool:
        """Verifica se URL é válida para um post"""
        # Deve ser do mesmo domínio
        url_domain = urlparse(url).netloc.lower()
        base_domain = urlparse(base_url).netloc.lower()
        if url_domain != base_domain:
            return False

        # Padrões para excluir
        exclude_patterns = [
            r'/category/',
            r'/tag/',
            r'/author/',
            r'/page/',
            r'/search/',
            r'/feed/',
            r'/rss/',
            r'/sitemap',
            r'\.(pdf|doc|docx|jpg|jpeg|png|gif|svg|css|js|zip)$',
            r'#',
            r'\?.*page=',
            r'/wp-',
            r'/admin',
            r'/login'
        ]

        for pattern in exclude_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False

        return True

    async def get_latest_posts(self, site_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Obtém últimos posts de um site"""
        try:
            site_url = site_config.get('url', '')
            if not site_url:
                return []

            site_url = self.normalize_url(site_url)
            logger.info(f"🔍 Buscando posts em: {site_config.get('name', site_url)}")

            # Faz request para a página
            if not self.web_client:
                await self.initialize()

            response = await self.web_client.get(site_url, follow_redirects=True)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extrai links de posts
            posts = self.extract_post_links(soup, site_url, site_config)

            logger.info(f"📝 {len(posts)} posts encontrados em {site_config.get('name', site_url)}")
            return posts

        except Exception as e:
            logger.error(f"❌ Erro ao obter posts de {site_config.get('name', 'N/A')}: {e}")
            return []

    async def scrape_post_content(self, post_url: str) -> Optional[Dict[str, Any]]:
        """Faz scraping completo do conteúdo de um post"""
        try:
            logger.info(f"📄 Fazendo scraping de: {post_url}")

            if not self.web_client:
                await self.initialize()

            # Faz request para o post
            response = await self.web_client.get(post_url, follow_redirects=True)
            response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove scripts e styles
            for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                script.decompose()

            # Extrai dados do post
            post_data = await self.extract_post_data(soup, post_url)

            if post_data['content']:
                logger.info(f"✅ Scraping concluído: {len(post_data['content'])} caracteres")
                return post_data
            else:
                logger.warning(f"⚠️  Conteúdo vazio para: {post_url}")
                return None

        except Exception as e:
            logger.error(f"❌ Erro no scraping de {post_url}: {e}")
            return None

    async def extract_post_data(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extrai dados estruturados do post"""
        # Título
        title = self.extract_title(soup)

        # Conteúdo principal
        content = self.extract_content(soup)

        # Imagens
        images = self.extract_images(soup, url)

        # Metadados
        metadata = self.extract_metadata(soup)

        # Data de publicação
        published_date = self.extract_published_date(soup)

        # Autor
        author = self.extract_author(soup)

        return {
            'url': url,
            'title': title,
            'content': content,
            'images': images,
            'author': author,
            'published_date': published_date,
            'metadata': metadata,
            'scraped_at': datetime.now().isoformat(),
            'content_length': len(content)
        }

    def extract_title(self, soup: BeautifulSoup) -> str:
        """Extrai título do post"""
        # Prioridade de seletores
        title_selectors = [
            'h1.entry-title',
            'h1.post-title',
            'h1.article-title',
            '.entry-header h1',
            '.post-header h1',
            'article h1',
            'h1',
            'title'
        ]

        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text().strip()
                if title and len(title) > 3:
                    return title

        return "Sem título"

    def extract_content(self, soup: BeautifulSoup) -> str:
        """Extrai conteúdo principal do post"""
        # Seletores para conteúdo
        content_selectors = [
            '.entry-content',
            '.post-content',
            '.article-content',
            '.main-content',
            '.content',
            'article .content',
            '.post-body',
            '[role="main"]'
        ]

        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                # Remove elementos desnecessários
                for unwanted in element(['script', 'style', 'nav', 'aside', '.share', '.related']):
                    unwanted.decompose()

                content = element.get_text(separator=' ').strip()
                content = re.sub(r'\s+', ' ', content)

                if content and len(content) > 200:
                    return content

        # Fallback: pega todos os parágrafos
        paragraphs = soup.find_all('p')
        content = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        content = re.sub(r'\s+', ' ', content)

        return content

    def extract_images(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """Extrai imagens do post"""
        images = []

        # Procura imagens no conteúdo
        img_tags = soup.select('.entry-content img, .post-content img, article img')

        for img in img_tags[:5]:  # Máximo 5 imagens
            src = img.get('src')
            alt = img.get('alt', '')

            if src:
                # Normaliza URL da imagem
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(base_url, src)

                images.append({
                    'src': src,
                    'alt': alt
                })

        return images

    def extract_author(self, soup: BeautifulSoup) -> str:
        """Extrai autor do post"""
        author_selectors = [
            '.author',
            '.by-author',
            '.post-author',
            '.entry-author',
            '[rel="author"]'
        ]

        for selector in author_selectors:
            element = soup.select_one(selector)
            if element:
                author = element.get_text().strip()
                if author:
                    return author

        return ""

    def extract_published_date(self, soup: BeautifulSoup) -> str:
        """Extrai data de publicação"""
        date_selectors = [
            'time[datetime]',
            '.published',
            '.post-date',
            '.entry-date'
        ]

        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                # Pega datetime se disponível
                date_str = element.get('datetime')
                if not date_str:
                    date_str = element.get_text().strip()

                if date_str:
                    return date_str

        return ""

    def extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extrai metadados adicionais"""
        metadata = {}

        # Meta tags
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            name = tag.get('name') or tag.get('property')
            content = tag.get('content')

            if name and content:
                if 'description' in name.lower():
                    metadata['description'] = content
                elif 'keywords' in name.lower():
                    metadata['keywords'] = content
                elif 'og:' in name:
                    metadata[name] = content

        # Categorias/Tags
        categories = []
        for selector in ['.category', '.tag', '.post-category']:
            elements = soup.select(selector)
            for element in elements:
                cat = element.get_text().strip()
                if cat and cat not in categories:
                    categories.append(cat)

        if categories:
            metadata['categories'] = categories

        return metadata


async def main():
    """Função de teste"""
    scraper = UnipostWebScraper()
    await scraper.initialize()

    # Teste com um site exemplo
    test_site = {
        'name': 'Teste',
        'url': 'https://example.com'
    }

    posts = await scraper.get_latest_posts(test_site)
    print(f"Posts encontrados: {len(posts)}")

    await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
