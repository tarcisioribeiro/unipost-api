#!/usr/bin/env python3
"""
WebScraper usando MCP SDK Python
Consulta sites de referência através da API do projeto e realiza scraping automatizado
"""

import os
import sys
import json
import asyncio
import logging
import re
from typing import List, Dict, Any, Set
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlunparse
from collections import deque

import httpx
import django

# Configuração do Django
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from sites.models import Site


# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent / 'scraping.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configurações da API
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8005/api/v1')
API_USERNAME = os.getenv('DJANGO_SUPERUSER_USERNAME')
API_PASSWORD = os.getenv('DJANGO_SUPERUSER_PASSWORD')


class WebScraper:
    """Classe principal para realizar WebScraping recursivo usando MCP SDK"""

    def __init__(self):
        self.session = None
        self.api_token = None
        self.scraped_data = []
        self.visited_urls: Set[str] = set()
        self.url_queue = deque()
        self.domain_urls: Dict[str, Set[str]] = {}
        
    async def authenticate_api(self) -> bool:
        """Autentica na API do projeto para obter token JWT"""
        try:
            async with httpx.AsyncClient() as client:
                auth_data = {
                    "username": API_USERNAME,
                    "password": API_PASSWORD
                }
                
                response = await client.post(
                    f"{API_BASE_URL}/auth/login/",
                    json=auth_data
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.api_token = token_data.get('access')
                    logger.info("Autenticação na API realizada com sucesso")
                    return True
                else:
                    logger.error(f"Falha na autenticação: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Erro ao autenticar na API: {e}")
            return False
    
    def get_sites_from_database_sync(self) -> List[Dict[str, Any]]:
        """Obtém lista de sites diretamente do banco de dados (versão síncrona)"""
        try:
            from django.db import transaction
            
            with transaction.atomic():
                sites = Site.objects.all()
                sites_data = []
                
                for site in sites:
                    sites_data.append({
                        'id': site.id,
                        'name': site.name,
                        'url': site.url,
                        'category': site.category,
                        'enable_recursive_crawling': site.enable_recursive_crawling,
                        'max_depth': site.max_depth,
                        'max_pages': site.max_pages,
                        'allow_patterns': site.allow_patterns,
                        'deny_patterns': site.deny_patterns,
                        'content_selectors': site.content_selectors,
                        'created_at': site.created_at.isoformat(),
                        'updated_at': site.updated_at.isoformat()
                    })
                
                logger.info(f"Obtidos {len(sites_data)} sites do banco de dados")
                return sites_data
                        
        except Exception as e:
            logger.error(f"Erro ao consultar sites: {e}")
            return []
    
    async def get_sites_from_database(self) -> List[Dict[str, Any]]:
        """Wrapper assíncrono para consulta de sites"""
        try:
            from django.db import connection
            from asgiref.sync import sync_to_async

            # Usa sync_to_async para executar a consulta Django
            sites_data = await sync_to_async(self.get_sites_from_database_sync, thread_sensitive=True)()
            return sites_data
        except Exception as e:
            logger.error(f"Erro ao consultar sites: {e}")
            return []
    
    async def init_web_client(self):
        """Inicializa cliente web simples"""
        try:
            self.web_client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            logger.info("Cliente web inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar cliente web: {e}")
            raise

    def normalize_url(self, url: str, base_url: str = None) -> str:
        """Normaliza URL removendo fragmentos e parâmetros desnecessários"""
        if base_url:
            url = urljoin(base_url, url)

        parsed = urlparse(url)
        # Remove fragment (#)
        normalized = urlunparse((
            parsed.scheme, parsed.netloc, parsed.path,
            parsed.params, parsed.query, None
        ))

        # Remove trailing slash exceto para root
        if normalized.endswith('/') and len(parsed.path) > 1:
            normalized = normalized[:-1]

        return normalized

    def is_same_domain(self, url1: str, url2: str) -> bool:
        """Verifica se duas URLs são do mesmo domínio"""
        domain1 = urlparse(url1).netloc.lower()
        domain2 = urlparse(url2).netloc.lower()
        return domain1 == domain2

    def should_crawl_url(self, url: str, site_config: Dict[str, Any], base_url: str) -> bool:
        """Verifica se uma URL deve ser incluída no crawling"""
        # Só crawl URLs do mesmo domínio
        if not self.is_same_domain(url, base_url):
            return False

        # Verifica padrões de negação
        deny_patterns = site_config.get('deny_patterns', '')
        if deny_patterns:
            for pattern in deny_patterns.strip().split('\n'):
                pattern = pattern.strip()
                if pattern and re.search(pattern, url, re.IGNORECASE):
                    return False

        # Verifica padrões permitidos
        allow_patterns = site_config.get('allow_patterns', '')
        if allow_patterns:
            for pattern in allow_patterns.strip().split('\n'):
                pattern = pattern.strip()
                if pattern and re.search(pattern, url, re.IGNORECASE):
                    return True
            return False  # Se tem allow_patterns, só passa o que bater

        # Padrões padrão para excluir arquivos não relevantes
        exclude_extensions = [
            r'\.(pdf|doc|docx|xls|xlsx|ppt|pptx|zip|rar|tar|gz)$',
            r'\.(jpg|jpeg|png|gif|svg|ico|webp|bmp)$',
            r'\.(mp3|mp4|avi|mov|wmv|flv|webm)$',
            r'\.(css|js|json|xml|rss)$'
        ]

        for pattern in exclude_extensions:
            if re.search(pattern, url, re.IGNORECASE):
                return False

        return True

    def extract_links(self, soup, base_url: str) -> List[str]:
        """Extrai todos os links internos de uma página"""
        links = set()

        # Procura por links <a href="">
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href:
                full_url = self.normalize_url(href, base_url)
                if self.is_same_domain(full_url, base_url):
                    links.add(full_url)

        return list(links)

    def extract_content_with_selectors(self, soup, selectors: str) -> str:
        """Extrai conteúdo usando seletores CSS específicos"""
        if not selectors:
            return ""

        content_parts = []
        for selector in selectors.strip().split('\n'):
            selector = selector.strip()
            if selector:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text().strip()
                    if text:
                        content_parts.append(text)

        return ' '.join(content_parts)

    def is_content_relevant(self, soup, url: str) -> bool:
        """Verifica se a página contém conteúdo relevante (artigos, posts, etc.)"""
        # Indicadores de conteúdo relevante
        content_indicators = [
            'article', 'post', 'blog', 'news', 'content',
            '[role="article"]', '[role="main"]', '.entry',
            '.post-content', '.article-content', '.blog-post'
        ]

        # Verifica se tem indicadores de conteúdo
        for indicator in content_indicators:
            if soup.select(indicator):
                return True

        # Verifica se tem parágrafos suficientes
        paragraphs = soup.find_all('p')
        if len(paragraphs) >= 3:
            total_text = ' '.join([p.get_text() for p in paragraphs])
            if len(total_text.strip()) >= 200:  # Pelo menos 200 caracteres
                return True

        return False
    
    async def scrape_page_content(self, url: str, site_name: str, site_config: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza scraping de uma página individual"""
        try:
            if not hasattr(self, 'web_client'):
                await self.init_web_client()

            # Verifica se a URL tem protocolo
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            # Faz request para a página
            response = await self.web_client.get(url, follow_redirects=True)
            response.raise_for_status()

            # Parse do HTML usando BeautifulSoup
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')

                # Remove scripts e styles
                for script in soup(["script", "style"]):
                    script.decompose()

                # Extrai título
                title = soup.find('title')
                title_text = title.get_text().strip() if title else ""

                # Extrai conteúdo usando seletores customizados se disponível
                content_selectors = site_config.get('content_selectors', '')
                if content_selectors:
                    content_text = self.extract_content_with_selectors(soup, content_selectors)
                else:
                    # Extração padrão - procura por artigos, então parágrafos
                    content_elements = soup.select('article, .content, .post-content, .entry-content')
                    if content_elements:
                        content_text = ' '.join([elem.get_text().strip() for elem in content_elements])
                    else:
                        paragraphs = soup.find_all('p')
                        content_text = ' '.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])

                # Limita o tamanho do conteúdo
                if len(content_text) > 5000:
                    content_text = content_text[:5000] + "..."

                # Extrai links para crawling recursivo
                links = self.extract_links(soup, url)

                return {
                    "site_name": site_name,
                    "url": url,
                    "title": title_text,
                    "scraped_at": datetime.now().isoformat(),
                    "content": content_text,
                    "content_length": len(content_text),
                    "is_relevant": self.is_content_relevant(soup, url),
                    "links_found": len(links),
                    "links": links,
                    "status": "success"
                }

            except ImportError:
                # Fallback sem BeautifulSoup
                content_text = response.text[:5000] + "..." if len(response.text) > 5000 else response.text
                return {
                    "site_name": site_name,
                    "url": url,
                    "title": site_name,
                    "scraped_at": datetime.now().isoformat(),
                    "content": content_text,
                    "content_length": len(content_text),
                    "is_relevant": True,  # Assume relevante sem parser
                    "links_found": 0,
                    "links": [],
                    "status": "success"
                }

        except Exception as e:
            logger.error(f"Erro no scraping de {url}: {e}")
            return {
                "site_name": site_name,
                "url": url,
                "title": "",
                "scraped_at": datetime.now().isoformat(),
                "content": "",
                "content_length": 0,
                "is_relevant": False,
                "links_found": 0,
                "links": [],
                "status": "error",
                "error": str(e)
            }
    
    async def crawl_site_recursive(self, site_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Realiza crawling recursivo de um site"""
        site_name = site_config.get('name', 'N/A')
        base_url = site_config.get('url', '')
        enable_recursive = site_config.get('enable_recursive_crawling', True)
        max_depth = site_config.get('max_depth', 2)
        max_pages = site_config.get('max_pages', 50)

        if not base_url:
            logger.warning(f"URL inválida para site: {site_name}")
            return []

        # Normaliza URL base
        if not base_url.startswith(('http://', 'https://')):
            base_url = 'https://' + base_url
        base_url = self.normalize_url(base_url)

        # Reinicia controles para este site
        self.visited_urls.clear()
        self.url_queue.clear()

        # Adiciona URL inicial na fila
        self.url_queue.append((base_url, 0))  # (url, depth)
        scraped_pages = []

        logger.info(f"Iniciando crawling {'recursivo' if enable_recursive else 'simples'} para: {site_name}")
        logger.info(f"Configurações - Max depth: {max_depth}, Max pages: {max_pages}")

        pages_scraped = 0

        while self.url_queue and pages_scraped < max_pages:
            current_url, depth = self.url_queue.popleft()

            # Verifica se já visitou esta URL
            if current_url in self.visited_urls:
                continue

            # Marca como visitada
            self.visited_urls.add(current_url)

            # Faz scraping da página atual
            logger.info(f"Fazendo scraping de: {current_url} (profundidade: {depth})")
            page_result = await self.scrape_page_content(current_url, site_name, site_config)

            if page_result['status'] == 'success':
                scraped_pages.append(page_result)
                pages_scraped += 1

                # Se habilitado crawling recursivo e não atingiu max depth
                if enable_recursive and depth < max_depth and page_result.get('links'):
                    # Adiciona links encontrados na fila
                    for link in page_result['links']:
                        if (link not in self.visited_urls and
                            self.should_crawl_url(link, site_config, base_url)):
                            self.url_queue.append((link, depth + 1))

                logger.info(f"Página processada - Relevante: {page_result.get('is_relevant', False)}, "
                           f"Links encontrados: {page_result.get('links_found', 0)}")
            else:
                logger.warning(f"Falha no scraping de: {current_url}")

            # Pausa entre requisições
            await asyncio.sleep(1)

        logger.info(f"Crawling finalizado para {site_name}: {pages_scraped} páginas processadas")
        return scraped_pages

    async def scrape_all_sites(self) -> List[Dict[str, Any]]:
        """Realiza scraping de todos os sites obtidos do banco"""
        sites = await self.get_sites_from_database()

        if not sites:
            logger.warning("Nenhum site encontrado no banco de dados")
            return []

        all_scraped_results = []

        for site in sites:
            try:
                site_results = await self.crawl_site_recursive(site)
                all_scraped_results.extend(site_results)

                # Pausa maior entre sites
                await asyncio.sleep(3)

            except Exception as e:
                logger.error(f"Erro no crawling do site {site.get('name', 'N/A')}: {e}")

        return all_scraped_results
    
    async def save_results(self, results: List[Dict[str, Any]], output_file: str = None):
        """Salva os resultados do scraping em arquivo JSON"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"scraping_results_{timestamp}.json"
        
        output_path = Path(__file__).parent / output_file
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Resultados salvos em: {output_path}")
            
            # Estatísticas
            total_pages = len(results)
            successful = len([r for r in results if r.get('status') == 'success'])
            failed = total_pages - successful
            relevant_pages = len([r for r in results if r.get('is_relevant', False)])
            total_links = sum([r.get('links_found', 0) for r in results])

            logger.info(f"Resumo: {total_pages} páginas processadas")
            logger.info(f"Sucessos: {successful}, Falhas: {failed}")
            logger.info(f"Páginas relevantes: {relevant_pages}")
            logger.info(f"Total de links encontrados: {total_links}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar resultados: {e}")
    
    async def run(self):
        """Executa o processo completo de scraping"""
        logger.info("Iniciando WebScraper...")
        
        try:
            # Inicializa cliente web
            await self.init_web_client()
            
            # Realiza scraping de todos os sites
            results = await self.scrape_all_sites()
            
            # Salva resultados
            await self.save_results(results)
            
            logger.info("WebScraper finalizado com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro durante execução: {e}")
        
        finally:
            # Cleanup
            if hasattr(self, 'web_client'):
                try:
                    await self.web_client.aclose()
                except:
                    pass


async def main():
    """Função principal"""
    scraper = WebScraper()
    await scraper.run()


if __name__ == "__main__":
    # Executa o scraper
    asyncio.run(main())
