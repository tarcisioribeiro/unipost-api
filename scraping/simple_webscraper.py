#!/usr/bin/env python3
"""
Simple WebScraper - Versão simplificada para teste
Consulta sites e extrai informações básicas usando requests/httpx
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
from asgiref.sync import sync_to_async

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
        logging.FileHandler(Path(__file__).parent / 'simple_scraping.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SimpleWebScraper:
    """Classe para realizar WebScraping simples usando httpx"""
    
    def __init__(self):
        self.scraped_data = []
        
    async def get_sites_from_database(self) -> List[Dict[str, Any]]:
        """Obtém lista de sites diretamente do banco de dados"""
        try:
            # Usa sync_to_async para operações do Django ORM
            sites = await sync_to_async(list)(Site.objects.all())
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
    
    async def scrape_site_content(self, site_url: str, site_name: str) -> Dict[str, Any]:
        """Realiza scraping básico de um site"""
        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; UniversidadeMarketplace-Bot/1.0)'
                }
            ) as client:
                
                response = await client.get(site_url)
                
                # Extrai informações básicas
                content_info = {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "content_length": len(response.content),
                    "content_type": response.headers.get('content-type', 'unknown'),
                    "text_preview": response.text[:1000] if response.text else None
                }
                
                scraped_content = {
                    "site_name": site_name,
                    "site_url": site_url,
                    "scraped_at": datetime.now().isoformat(),
                    "content": content_info,
                    "status": "success" if response.status_code == 200 else "partial_success",
                    "response_time": None  # Could be added with timing
                }
                
                logger.info(f"Scraping realizado com sucesso para: {site_name} (Status: {response.status_code})")
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
            logger.warning("Nenhum site encontrado no banco")
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
            
            # Pausa entre requisições para ser respeitoso
            await asyncio.sleep(1)
        
        return scraped_results
    
    async def save_results(self, results: List[Dict[str, Any]], output_file: str = None):
        """Salva os resultados do scraping em arquivo JSON"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"simple_scraping_results_{timestamp}.json"
        
        output_path = Path(__file__).parent / output_file
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Resultados salvos em: {output_path}")
            
            # Estatísticas
            total_sites = len(results)
            successful = len([r for r in results if r.get('status') == 'success'])
            partial = len([r for r in results if r.get('status') == 'partial_success'])
            failed = total_sites - successful - partial
            
            logger.info(f"Resumo: {total_sites} sites processados")
            logger.info(f"Sucessos: {successful}, Parciais: {partial}, Falhas: {failed}")
            
        except Exception as e:
            logger.error(f"Erro ao salvar resultados: {e}")
    
    async def run(self):
        """Executa o processo completo de scraping"""
        logger.info("Iniciando Simple WebScraper...")
        
        try:
            # Realiza scraping de todos os sites
            results = await self.scrape_all_sites()
            
            # Salva resultados
            await self.save_results(results)
            
            logger.info("Simple WebScraper finalizado com sucesso!")
            
        except Exception as e:
            logger.error(f"Erro durante execução: {e}")


async def main():
    """Função principal"""
    scraper = SimpleWebScraper()
    await scraper.run()


if __name__ == "__main__":
    # Executa o scraper
    asyncio.run(main())