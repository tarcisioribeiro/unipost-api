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
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path

import httpx
import django
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client

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
    """Classe principal para realizar WebScraping usando MCP SDK"""
    
    def __init__(self):
        self.session = None
        self.api_token = None
        self.scraped_data = []
        
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
    
    async def get_sites_from_database(self) -> List[Dict[str, Any]]:
        """Obtém lista de sites diretamente do banco de dados"""
        try:
            sites = Site.objects.all()
            sites_data = []
            
            for site in sites:
                sites_data.append({
                    'id': site.id,
                    'name': site.name,
                    'url': site.url,
                    'category': site.category,
                    'created_at': site.created_at.isoformat(),
                    'updated_at': site.updated_at.isoformat()
                })
            
            logger.info(f"Obtidos {len(sites_data)} sites do banco de dados")
            return sites_data
                    
        except Exception as e:
            logger.error(f"Erro ao consultar sites: {e}")
            return []
    
    async def init_mcp_client(self):
        """Inicializa o cliente MCP gratuito"""
        try:
            # Configura parâmetros do servidor MCP
            server_params = StdioServerParameters(
                command="npx",
                args=[
                    "-y",
                    "@modelcontextprotocol/server-web-search@latest"
                ]
            )
            
            # Inicia conexão com servidor MCP
            self.session = await stdio_client(server_params).__aenter__()
            logger.info("Cliente MCP inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar MCP: {e}")
            raise
    
    async def scrape_site_content(self, site_url: str, site_name: str) -> Dict[str, Any]:
        """Realiza scraping de um site usando MCP"""
        try:
            if not self.session:
                await self.init_mcp_client()
            
            # Usa ferramenta de web search do MCP para obter conteúdo
            result = await self.session.call_tool(
                "web_search",
                arguments={
                    "query": f"site:{site_url}",
                    "max_results": 5
                }
            )
            
            # Processa o resultado
            scraped_content = {
                "site_name": site_name,
                "site_url": site_url,
                "scraped_at": datetime.now().isoformat(),
                "content": result.content if hasattr(result, 'content') else str(result),
                "status": "success"
            }
            
            logger.info(f"Scraping realizado com sucesso para: {site_name}")
            return scraped_content
            
        except Exception as e:
            logger.error(f"Erro no scraping de {site_name}: {e}")
            return {
                "site_name": site_name,
                "site_url": site_url,
                "scraped_at": datetime.now().isoformat(),
                "content": None,
                "status": "error",
                "error": str(e)
            }
    
    async def scrape_all_sites(self) -> List[Dict[str, Any]]:
        """Realiza scraping de todos os sites obtidos do banco"""
        sites = await self.get_sites_from_database()
        
        if not sites:
            logger.warning("Nenhum site encontrado na API")
            return []
        
        scraped_results = []
        
        for site in sites:
            site_name = site.get('name', 'N/A')
            site_url = site.get('url', '')
            
            if not site_url:
                logger.warning(f"URL inválida para site: {site_name}")
                continue
            
            logger.info(f"Iniciando scraping para: {site_name}")
            result = await self.scrape_site_content(site_url, site_name)
            scraped_results.append(result)
            
            # Pausa entre requisições para evitar sobrecarga
            await asyncio.sleep(2)
        
        return scraped_results
    
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
            total_sites = len(results)
            successful = len([r for r in results if r.get('status') == 'success'])
            failed = total_sites - successful
            
            logger.info(f"Resumo: {total_sites} sites processados")
            logger.info(f"Sucessos: {successful}, Falhas: {failed}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar resultados: {e}")
    
    async def run(self):
        """Executa o processo completo de scraping"""
        logger.info("Iniciando WebScraper...")
        
        try:
            # Inicializa cliente MCP
            await self.init_mcp_client()
            
            # Realiza scraping de todos os sites
            results = await self.scrape_all_sites()
            
            # Salva resultados
            await self.save_results(results)
            
            logger.info("WebScraper finalizado com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro durante execução: {e}")
        
        finally:
            # Cleanup
            if self.session:
                try:
                    await self.session.__aexit__(None, None, None)
                except:
                    pass


async def main():
    """Função principal"""
    scraper = WebScraper()
    await scraper.run()


if __name__ == "__main__":
    # Executa o scraper
    asyncio.run(main())
