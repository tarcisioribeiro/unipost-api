#!/usr/bin/env python3
"""
Image Storage Manager
Gerencia armazenamento de imagens no filesystem e metadados no PostgreSQL + PGVector
"""

from .models import GeneratedImage
from embeddings.models import Embedding
from django.conf import settings
import django
import os
import sys
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from asgiref.sync import sync_to_async

# Django setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

django.setup()


logger = logging.getLogger(__name__)


class ImageStorageManager:
    """Gerenciador de armazenamento de imagens"""

    def __init__(self):
        self.storage_path = getattr(settings, 'IMAGE_STORAGE_PATH',
                                    Path(settings.BASE_DIR) / 'unipost_automation' / 'src' / 'images')
        self.is_initialized = False

    async def initialize(self) -> bool:
        """Inicializa o gerenciador de storage"""
        try:
            logger.info("💾 Inicializando Image Storage Manager...")

            # Criar diretório se não existir
            self.storage_path = Path(self.storage_path)
            self.storage_path.mkdir(parents=True, exist_ok=True)

            # Verificar permissões
            if not os.access(self.storage_path, os.W_OK):
                raise PermissionError(f"Sem permissão de escrita em {self.storage_path}")

            self.is_initialized = True
            logger.info(f"✅ Storage inicializado em: {self.storage_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Erro na inicialização do storage: {e}")
            return False

    async def save_image(self, image_data: bytes, embedding_id: str,
                         title: str, prompt: str, metadata: Dict[str, Any]) -> str:
        """Salva imagem no filesystem e cria link simbólico no banco"""
        if not self.is_initialized:
            raise RuntimeError("Storage não inicializado")

        try:
            logger.info(f"💾 Salvando imagem para embedding {embedding_id}...")

            # Gerar nome do arquivo baseado em data_id_título.png
            filename = self._generate_filename(embedding_id, title)
            file_path = self.storage_path / filename

            # Salvar arquivo físico
            await self._write_image_file(file_path, image_data)

            # Criar registro no banco (link simbólico)
            await self._create_image_record(
                embedding_id, title, prompt, str(file_path), metadata
            )

            logger.info(f"✅ Imagem salva: {filename}")
            return str(file_path)

        except Exception as e:
            logger.error(f"❌ Erro ao salvar imagem: {e}")
            raise

    def _generate_filename(self, embedding_id: str, title: str) -> str:
        """Gera nome do arquivo baseado em data_id_título.png"""
        try:
            # Data atual
            date_str = datetime.now().strftime("%Y%m%d")

            # ID curto (primeiros 8 caracteres)
            id_short = embedding_id[:8]

            # Título limpo (apenas letras, números e espaços)
            title_clean = ''.join(c for c in title if c.isalnum() or c.isspace())
            title_clean = '_'.join(title_clean.split())[:50]  # Máximo 50 chars

            # Se título vazio, usar 'untitled'
            if not title_clean:
                title_clean = 'untitled'

            filename = f"{date_str}_{id_short}_{title_clean}.png"
            return filename

        except Exception as e:
            logger.error(f"❌ Erro ao gerar nome do arquivo: {e}")
            # Fallback name
            return f"{datetime.now().strftime('%Y%m%d')}_{embedding_id[:8]}_image.png"

    async def _write_image_file(self, file_path: Path, image_data: bytes) -> None:
        """Escreve arquivo de imagem no filesystem"""
        try:
            # Verificar se arquivo já existe
            if file_path.exists():
                logger.warning(f"⚠️  Arquivo já existe, sobrescrevendo: {file_path}")

            # Escrever arquivo de forma assíncrona
            def write_file():
                with open(file_path, 'wb') as f:
                    f.write(image_data)

            await asyncio.get_event_loop().run_in_executor(None, write_file)

            # Verificar se foi escrito corretamente
            if not file_path.exists():
                raise Exception("Arquivo não foi criado")

            file_size = file_path.stat().st_size
            if file_size != len(image_data):
                raise Exception(f"Tamanho incorreto: esperado {len(image_data)}, obtido {file_size}")

            logger.info(f"📁 Arquivo escrito: {file_path} ({file_size} bytes)")

        except Exception as e:
            logger.error(f"❌ Erro ao escrever arquivo: {e}")
            raise

    @sync_to_async
    def _create_image_record_sync(self, embedding_id: str, original_text: str,
                                  prompt: str, image_path: str,
                                  metadata: Dict[str, Any]) -> str:
        """Cria registro de imagem no banco (versão síncrona)"""
        try:
            # Buscar embedding relacionado
            embedding = Embedding.objects.get(id=embedding_id)

            # Criar registro de imagem gerada
            image_record = GeneratedImage.objects.create(
                embedding=embedding,
                original_text=original_text,
                generated_prompt=prompt,
                image_path=image_path,
                dalle_response=metadata.get('dalle_response', {}),
                generation_metadata={
                    **metadata,
                    'file_size': os.path.getsize(image_path),
                    'saved_at': datetime.now().isoformat(),
                    'storage_path': str(self.storage_path)
                }
            )

            return str(image_record.id)

        except Embedding.DoesNotExist:
            raise ValueError(f"Embedding não encontrado: {embedding_id}")
        except Exception as e:
            logger.error(f"❌ Erro ao criar registro de imagem: {e}")
            raise

    async def _create_image_record(self, embedding_id: str, original_text: str,
                                   prompt: str, image_path: str,
                                   metadata: Dict[str, Any]) -> str:
        """Cria registro de imagem no banco"""
        return await self._create_image_record_sync(
            embedding_id, original_text, prompt, image_path, metadata
        )

    @sync_to_async
    def get_image_info_sync(self, image_id: str) -> Optional[Dict[str, Any]]:
        """Obtém informações de uma imagem (versão síncrona)"""
        try:
            image_record = GeneratedImage.objects.get(id=image_id)

            return {
                'id': str(image_record.id),
                'embedding_id': str(image_record.embedding.id),
                'original_text': image_record.original_text,
                'generated_prompt': image_record.generated_prompt,
                'image_path': image_record.image_path,
                'dalle_response': image_record.dalle_response,
                'generation_metadata': image_record.generation_metadata,
                'created_at': image_record.created_at.isoformat(),
                'file_exists': os.path.exists(image_record.image_path)
            }

        except GeneratedImage.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao obter info da imagem: {e}")
            return None

    async def get_image_info(self, image_id: str) -> Optional[Dict[str, Any]]:
        """Obtém informações de uma imagem"""
        return await self.get_image_info_sync(image_id)

    @sync_to_async
    def list_images_for_embedding_sync(self, embedding_id: str) -> List[Dict[str, Any]]:
        """Lista imagens de um embedding (versão síncrona)"""
        try:
            images = GeneratedImage.objects.filter(
                embedding_id=embedding_id
            ).order_by('-created_at')

            return [
                {
                    'id': str(img.id),
                    'image_path': img.image_path,
                    'generated_prompt': img.generated_prompt,
                    'created_at': img.created_at.isoformat(),
                    'file_exists': os.path.exists(img.image_path)
                }
                for img in images
            ]

        except Exception as e:
            logger.error(f"❌ Erro ao listar imagens: {e}")
            return []

    async def list_images_for_embedding(self, embedding_id: str) -> List[Dict[str, Any]]:
        """Lista todas as imagens geradas para um embedding"""
        return await self.list_images_for_embedding_sync(embedding_id)

    async def delete_image(self, image_id: str) -> bool:
        """Remove imagem do filesystem e registro do banco"""
        try:
            logger.info(f"🗑️  Removendo imagem {image_id}...")

            # Obter informações da imagem
            image_info = await self.get_image_info(image_id)
            if not image_info:
                logger.warning(f"⚠️  Imagem não encontrada: {image_id}")
                return False

            # Remover arquivo físico
            image_path = Path(image_info['image_path'])
            if image_path.exists():
                await asyncio.get_event_loop().run_in_executor(
                    None, image_path.unlink
                )
                logger.info(f"📁 Arquivo removido: {image_path}")

            # Remover registro do banco
            await self._delete_image_record(image_id)

            logger.info(f"✅ Imagem removida: {image_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao remover imagem: {e}")
            return False

    @sync_to_async
    def _delete_image_record(self, image_id: str) -> None:
        """Remove registro de imagem do banco"""
        try:
            GeneratedImage.objects.filter(id=image_id).delete()
        except Exception as e:
            logger.error(f"❌ Erro ao remover registro: {e}")
            raise

    async def get_storage_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do storage"""
        try:
            stats = await self._get_storage_stats_sync()
            return stats

        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return {}

    @sync_to_async
    def _get_storage_stats_sync(self) -> Dict[str, Any]:
        """Obtém estatísticas do storage (versão síncrona)"""
        try:
            # Contar registros no banco
            total_images = GeneratedImage.objects.count()
            today_images = GeneratedImage.objects.filter(
                created_at__date=datetime.now().date()
            ).count()

            # Verificar arquivos no filesystem
            files_count = 0
            total_size = 0

            if self.storage_path.exists():
                for file_path in self.storage_path.glob("*.png"):
                    files_count += 1
                    total_size += file_path.stat().st_size

            return {
                'total_images_db': total_images,
                'today_images': today_images,
                'files_on_disk': files_count,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'storage_path': str(self.storage_path),
                'storage_path_exists': self.storage_path.exists()
            }

        except Exception as e:
            logger.error(f"❌ Erro ao calcular estatísticas: {e}")
            return {}

    async def cleanup_orphaned_files(self) -> int:
        """Remove arquivos órfãos (sem registro no banco)"""
        try:
            logger.info("🧹 Iniciando limpeza de arquivos órfãos...")

            # Obter todos os caminhos registrados no banco
            @sync_to_async
            def get_registered_paths():
                return set(GeneratedImage.objects.values_list('image_path', flat=True))

            registered_paths = await get_registered_paths()

            # Verificar arquivos no filesystem
            removed_count = 0
            if self.storage_path.exists():
                for file_path in self.storage_path.glob("*.png"):
                    if str(file_path) not in registered_paths:
                        await asyncio.get_event_loop().run_in_executor(
                            None, file_path.unlink
                        )
                        removed_count += 1
                        logger.info(f"🗑️  Arquivo órfão removido: {file_path}")

            logger.info(f"✅ {removed_count} arquivos órfãos removidos")
            return removed_count

        except Exception as e:
            logger.error(f"❌ Erro na limpeza de arquivos órfãos: {e}")
            return 0

    async def close(self) -> None:
        """Encerra storage manager"""
        try:
            logger.info("💾 Encerrando Image Storage Manager...")
            self.is_initialized = False
            logger.info("✅ Storage encerrado")
        except Exception as e:
            logger.error(f"❌ Erro no encerramento: {e}")


# Função utilitária para uso direto
async def save_generated_image(image_data: bytes, embedding_id: str,
                               title: str, prompt: str,
                               metadata: Dict[str, Any]) -> str:
    """Função utilitária para salvar imagem rapidamente"""
    storage = ImageStorageManager()

    try:
        await storage.initialize()
        return await storage.save_image(image_data, embedding_id, title, prompt, metadata)
    finally:
        await storage.close()
