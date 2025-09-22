#!/usr/bin/env python3
"""
Database Manager Unipost Automation
Gerencia operações de banco de dados usando os modelos Django existentes
"""

import os
import sys
import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from asgiref.sync import sync_to_async

# Django setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

import django
django.setup()

from sites.models import Site
from embeddings.models import Embedding

# Logging setup
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gerenciador de operações de banco de dados"""

    def __init__(self):
        self.processed_urls_cache: Set[str] = set()

    async def initialize(self) -> bool:
        """Inicializa o gerenciador de banco"""
        try:
            logger.info("🗄️  Database Manager inicializado")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Database Manager: {e}")
            return False

    async def close(self) -> None:
        """Fecha conexões se necessário"""
        pass

    @sync_to_async
    def get_monitored_sites_sync(self) -> List[Dict[str, Any]]:
        """Obtém sites monitorados (versão síncrona)"""
        try:
            sites = Site.objects.filter(enable_recursive_crawling=True)
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

            return sites_data

        except Exception as e:
            logger.error(f"❌ Erro ao obter sites monitorados: {e}")
            return []

    async def get_monitored_sites(self) -> List[Dict[str, Any]]:
        """Obtém lista de sites para monitoramento"""
        try:
            sites_data = await self.get_monitored_sites_sync()
            logger.info(f"📊 {len(sites_data)} sites monitorados encontrados")
            return sites_data

        except Exception as e:
            logger.error(f"❌ Erro ao obter sites monitorados: {e}")
            return []

    @sync_to_async
    def get_processed_urls_sync(self) -> Set[str]:
        """Obtém URLs já processadas (versão síncrona)"""
        try:
            # Busca embeddings do tipo webscraping com metadata
            embeddings = Embedding.objects.filter(
                origin='webscraping'
            ).values('metadata')

            processed_urls = set()

            for embedding in embeddings:
                metadata = embedding.get('metadata', {})
                source_url = metadata.get('original_url') or metadata.get('source_url')

                if source_url:
                    processed_urls.add(source_url)

            return processed_urls

        except Exception as e:
            logger.error(f"❌ Erro ao obter URLs processadas: {e}")
            return set()

    async def get_processed_urls(self) -> Set[str]:
        """Obtém conjunto de URLs já processadas"""
        try:
            processed_urls = await self.get_processed_urls_sync()
            self.processed_urls_cache = processed_urls
            logger.info(f"📈 {len(processed_urls)} URLs já processadas")
            return processed_urls

        except Exception as e:
            logger.error(f"❌ Erro ao obter URLs processadas: {e}")
            return set()

    @sync_to_async
    def save_embedding_sync(self, embedding_data: Dict[str, Any]) -> str:
        """Salva embedding no banco (versão síncrona)"""
        try:
            embedding = Embedding.objects.create(
                origin=embedding_data.get('origin', 'webscraping'),
                content=embedding_data.get('content', ''),
                title=embedding_data.get('title', ''),
                embedding_vector=embedding_data.get('embedding_vector', []),
                metadata=embedding_data.get('metadata', {})
            )

            return str(embedding.id)

        except Exception as e:
            logger.error(f"❌ Erro ao salvar embedding: {e}")
            raise

    async def save_embedding(self, formatted_data: Dict[str, Any]) -> Optional[str]:
        """Salva embedding no banco de dados"""
        try:
            embedding_data = formatted_data.get('embedding', {})
            if not embedding_data:
                logger.error("❌ Dados de embedding não encontrados")
                return None

            embedding_id = await self.save_embedding_sync(embedding_data)
            logger.info(f"💾 Embedding salvo: {embedding_id}")

            # Atualiza cache
            source_url = embedding_data.get('metadata', {}).get('original_url')
            if source_url:
                self.processed_urls_cache.add(source_url)

            return embedding_id

        except Exception as e:
            logger.error(f"❌ Erro ao salvar embedding: {e}")
            return None

    @sync_to_async
    def save_processing_record_sync(self, record_data: Dict[str, Any]) -> None:
        """Salva registro de processamento (versão síncrona)"""
        try:
            # Por enquanto, usa a tabela de embeddings para tracking
            # Futuramente pode ser criada uma tabela específica

            tracking_embedding = Embedding.objects.create(
                origin='webscraping',
                content=f"Processing record for: {record_data.get('url', 'N/A')}",
                title=f"Processing: {record_data.get('title', 'N/A')}",
                embedding_vector=[0.0] * 768,  # Dummy embedding
                metadata={
                    'type': 'processing_record',
                    'source_url': record_data.get('url', ''),
                    'embedding_id': record_data.get('embedding_id', ''),
                    'wordpress_post_id': record_data.get('wordpress_post_id', ''),
                    'processed_at': datetime.now().isoformat(),
                    'status': 'completed'
                }
            )

            logger.info(f"📝 Registro de processamento salvo: {tracking_embedding.id}")

        except Exception as e:
            logger.error(f"❌ Erro ao salvar registro de processamento: {e}")
            raise

    async def mark_as_processed(self, url: str, embedding_id: str,
                              wordpress_post_id: Optional[int] = None) -> bool:
        """Marca URL como processada"""
        try:
            record_data = {
                'url': url,
                'title': f"Processed: {url}",
                'embedding_id': embedding_id,
                'wordpress_post_id': wordpress_post_id
            }

            await self.save_processing_record_sync(record_data)

            # Atualiza cache
            self.processed_urls_cache.add(url)

            logger.info(f"✅ URL marcada como processada: {url}")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao marcar URL como processada: {e}")
            return False

    @sync_to_async
    def get_processing_stats_sync(self) -> Dict[str, Any]:
        """Obtém estatísticas de processamento (versão síncrona)"""
        try:
            # Total de embeddings
            total_embeddings = Embedding.objects.filter(origin='webscraping').count()

            # Embeddings de hoje
            today = datetime.now().date()
            today_embeddings = Embedding.objects.filter(
                origin='webscraping',
                created_at__date=today
            ).count()

            # Registros de processamento
            processing_records = Embedding.objects.filter(
                origin='webscraping',
                metadata__type='processing_record'
            ).count()

            return {
                'total_embeddings': total_embeddings,
                'today_embeddings': today_embeddings,
                'processing_records': processing_records,
                'processed_urls_count': len(self.processed_urls_cache)
            }

        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return {}

    async def get_processing_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas de processamento"""
        try:
            stats = await self.get_processing_stats_sync()
            return stats

        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return {}

    async def cleanup_old_records(self, days_old: int = 30) -> int:
        """Remove registros antigos de processamento"""
        try:
            from django.utils import timezone
            cutoff_date = timezone.now() - timezone.timedelta(days=days_old)

            @sync_to_async
            def delete_old_records():
                deleted_count = Embedding.objects.filter(
                    origin='webscraping',
                    metadata__type='processing_record',
                    created_at__lt=cutoff_date
                ).delete()[0]
                return deleted_count

            deleted_count = await delete_old_records()
            logger.info(f"🧹 {deleted_count} registros antigos removidos")
            return deleted_count

        except Exception as e:
            logger.error(f"❌ Erro na limpeza de registros antigos: {e}")
            return 0

    @sync_to_async
    def get_recent_posts_sync(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtém posts recentes (versão síncrona)"""
        try:
            recent_embeddings = Embedding.objects.filter(
                origin='webscraping'
            ).exclude(
                metadata__type='processing_record'
            ).order_by('-created_at')[:limit]

            posts = []
            for embedding in recent_embeddings:
                metadata = embedding.metadata or {}
                posts.append({
                    'id': str(embedding.id),
                    'title': embedding.title,
                    'url': metadata.get('original_url', ''),
                    'content_length': len(embedding.content),
                    'created_at': embedding.created_at.isoformat(),
                    'wordpress_post_id': metadata.get('wordpress_post_id')
                })

            return posts

        except Exception as e:
            logger.error(f"❌ Erro ao obter posts recentes: {e}")
            return []

    async def get_recent_posts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtém lista de posts recentes processados"""
        try:
            posts = await self.get_recent_posts_sync(limit)
            return posts

        except Exception as e:
            logger.error(f"❌ Erro ao obter posts recentes: {e}")
            return []


async def main():
    """Função de teste"""
    db_manager = DatabaseManager()
    await db_manager.initialize()

    # Teste de obtenção de sites
    sites = await db_manager.get_monitored_sites()
    print(f"📊 {len(sites)} sites monitorados")

    # Teste de URLs processadas
    processed_urls = await db_manager.get_processed_urls()
    print(f"📈 {len(processed_urls)} URLs processadas")

    # Estatísticas
    stats = await db_manager.get_processing_stats()
    print(f"📈 Estatísticas: {stats}")

    await db_manager.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
