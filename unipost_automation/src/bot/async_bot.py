#!/usr/bin/env python3
"""
Robô Assíncrono Unipost Automation
Monitora URLs a cada 5 minutos e detecta novos posts para replicação
"""

import os
import sys
import asyncio
import logging
from typing import List, Dict, Any, Set
from datetime import datetime
from pathlib import Path

# Django setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

import django
django.setup()

# Local imports
from unipost_automation.src.scraping.webscraper import UnipostWebScraper
from unipost_automation.src.formatting.text_formatter import TextFormatter
from unipost_automation.src.posting.wordpress_client import WordPressClient
from unipost_automation.src.storage.db import DatabaseManager

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    handlers=[
        logging.FileHandler(
            Path(__file__).parent.parent.parent / 'logs' / 'async_bot.log',
            encoding='utf-8'
        ),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class UnipostAsyncBot:
    """Robô principal para automação do Unipost"""

    def __init__(self):
        self.webscraper = UnipostWebScraper()
        self.text_formatter = TextFormatter()
        self.wordpress_client = WordPressClient()
        self.db_manager = DatabaseManager()
        self.processed_urls: Set[str] = set()
        self.running = False
        self.check_interval = 300  # 5 minutos

    async def initialize(self) -> bool:
        """Inicializa todos os componentes do bot"""
        try:
            logger.info("🤖 Inicializando Unipost Async Bot...")

            # Inicializa componentes
            await self.webscraper.initialize()
            await self.text_formatter.initialize()
            await self.wordpress_client.initialize()
            await self.db_manager.initialize()

            # Carrega URLs já processadas
            self.processed_urls = await self.db_manager.get_processed_urls()

            logger.info(f"✅ Bot inicializado com {len(self.processed_urls)} URLs já processadas")
            return True

        except Exception as e:
            logger.error(f"❌ Erro na inicialização do bot: {e}")
            return False

    async def detect_new_posts(self) -> List[Dict[str, Any]]:
        """Detecta novos posts em todas as fontes configuradas"""
        try:
            logger.info("🔍 Detectando novos posts...")

            # Obtém lista de sites do banco
            sites = await self.db_manager.get_monitored_sites()
            new_posts = []

            for site in sites:
                try:
                    # Faz scraping da página inicial/feed do site
                    posts = await self.webscraper.get_latest_posts(site)

                    # Filtra apenas posts novos
                    for post in posts:
                        if post['url'] not in self.processed_urls:
                            new_posts.append(post)
                            logger.info(f"📝 Novo post detectado: {post['title']}")

                except Exception as e:
                    logger.error(f"❌ Erro ao detectar posts do site {site['name']}: {e}")
                    continue

            logger.info(f"✨ {len(new_posts)} novos posts detectados")
            return new_posts

        except Exception as e:
            logger.error(f"❌ Erro na detecção de posts: {e}")
            return []

    async def process_new_post(self, post: Dict[str, Any]) -> bool:
        """Processa um novo post: scraping -> embedding -> replicação"""
        try:
            post_url = post['url']
            logger.info(f"⚡ Processando: {post['title']} - {post_url}")

            # 1. Faz scraping completo do post
            scraped_content = await self.webscraper.scrape_post_content(post_url)
            if not scraped_content:
                logger.warning(f"⚠️  Falha no scraping de {post_url}")
                return False

            # 2. Formata texto e gera embedding
            formatted_data = await self.text_formatter.process_content(scraped_content)
            if not formatted_data:
                logger.warning(f"⚠️  Falha na formatação de {post_url}")
                return False

            # 3. Salva embedding no banco
            embedding_id = await self.db_manager.save_embedding(formatted_data)

            # 4. Replica post no WordPress
            wp_post_id = await self.wordpress_client.create_post(formatted_data)
            if not wp_post_id:
                logger.warning(f"⚠️  Falha na replicação de {post_url}")
                return False

            # 5. Marca como processado
            await self.db_manager.mark_as_processed(
                post_url, embedding_id, wp_post_id
            )
            self.processed_urls.add(post_url)

            logger.info(f"✅ Post processado com sucesso: {post['title']}")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao processar post {post.get('url', 'N/A')}: {e}")
            return False

    async def run_cycle(self) -> None:
        """Executa um ciclo completo de monitoramento"""
        try:
            cycle_start = datetime.now()
            logger.info(f"🔄 Iniciando ciclo de monitoramento - {cycle_start}")

            # Detecta novos posts
            new_posts = await self.detect_new_posts()

            if not new_posts:
                logger.info("😴 Nenhum post novo encontrado")
                return

            # Processa cada post novo
            processed_count = 0
            for post in new_posts:
                success = await self.process_new_post(post)
                if success:
                    processed_count += 1

                # Pequena pausa entre processamentos
                await asyncio.sleep(2)

            cycle_duration = datetime.now() - cycle_start
            logger.info(
                f"🎯 Ciclo concluído: {processed_count}/{len(new_posts)} posts processados "
                f"em {cycle_duration.total_seconds():.1f}s"
            )

        except Exception as e:
            logger.error(f"❌ Erro no ciclo de monitoramento: {e}")

    async def run(self) -> None:
        """Executa o bot em loop contínuo"""
        if not await self.initialize():
            logger.error("❌ Falha na inicialização. Bot será encerrado.")
            return

        logger.info(f"🚀 Bot iniciado - Monitoramento a cada {self.check_interval}s")
        self.running = True

        try:
            while self.running:
                await self.run_cycle()

                # Aguarda próximo ciclo
                logger.info(f"⏰ Aguardando {self.check_interval}s para próximo ciclo...")
                await asyncio.sleep(self.check_interval)

        except KeyboardInterrupt:
            logger.info("🛑 Bot interrompido pelo usuário")
        except Exception as e:
            logger.error(f"❌ Erro crítico no bot: {e}")
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Encerra o bot de forma limpa"""
        logger.info("🔄 Encerrando bot...")
        self.running = False

        try:
            await self.webscraper.close()
            await self.wordpress_client.close()
            await self.db_manager.close()
            logger.info("✅ Bot encerrado com sucesso")
        except Exception as e:
            logger.error(f"❌ Erro no shutdown: {e}")


async def main():
    """Função principal"""
    bot = UnipostAsyncBot()
    await bot.run()


if __name__ == "__main__":
    # Cria diretório de logs se não existir
    logs_dir = Path(__file__).parent.parent.parent / 'logs'
    logs_dir.mkdir(exist_ok=True)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Aplicação encerrada pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro crítico: {e}")
