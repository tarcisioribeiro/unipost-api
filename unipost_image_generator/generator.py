#!/usr/bin/env python3
"""
Image Generator - Orquestrador Principal
Coordena todo o processo de geração de imagens: prompt -> DALL-E -> storage
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from .prompt_builder import ClaudePromptBuilder, PromptRequest
from .clients import DalleApiClient, ImageGenerationRequest
from .storage import ImageStorageManager

logger = logging.getLogger(__name__)


@dataclass
class ImageGenerationTask:
    """Estrutura para tarefa de geração de imagem"""
    embedding_id: str
    text: str
    title: str
    style_preferences: Optional[Dict[str, str]] = None
    custom_prompt: Optional[str] = None


@dataclass
class ImageGenerationResult:
    """Resultado da geração de imagem"""
    success: bool
    image_path: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


class UnipostImageGenerator:
    """Orquestrador principal para geração de imagens"""

    def __init__(self):
        self.prompt_builder = ClaudePromptBuilder()
        self.dalle_client = DalleApiClient()
        self.storage_manager = ImageStorageManager()
        self.is_initialized = False

    async def initialize(self) -> bool:
        """Inicializa todos os componentes"""
        try:
            logger.info("🚀 Inicializando Unipost Image Generator...")

            # Inicializar componentes em paralelo
            results = await asyncio.gather(
                self.prompt_builder.initialize(),
                self.dalle_client.initialize(),
                self.storage_manager.initialize(),
                return_exceptions=True
            )

            # Verificar se todos foram inicializados com sucesso
            if not all(isinstance(result, bool) and result for result in results):
                failed_components = []
                if not results[0]:
                    failed_components.append("Claude Prompt Builder")
                if not results[1]:
                    failed_components.append("DALL-E Client")
                if not results[2]:
                    failed_components.append("Storage Manager")

                raise Exception(f"Falha na inicialização: {', '.join(failed_components)}")

            self.is_initialized = True
            logger.info("✅ Unipost Image Generator inicializado")
            return True

        except Exception as e:
            logger.error(f"❌ Erro na inicialização: {e}")
            return False

    async def generate_image(self, task: ImageGenerationTask) -> ImageGenerationResult:
        """Gera imagem completa para um post"""
        if not self.is_initialized:
            raise RuntimeError("Generator não inicializado")

        try:
            logger.info(f"🎨 Iniciando geração de imagem para: {task.title}")
            generation_start = datetime.now()

            # 1. Construir prompt (ou usar customizado)
            if task.custom_prompt:
                prompt = task.custom_prompt
                prompt_metadata = {'type': 'custom', 'source': 'user'}
            else:
                prompt_request = PromptRequest(
                    text=task.text,
                    style_preferences=task.style_preferences
                )
                prompt_response = await self.prompt_builder.build_prompt(prompt_request)
                prompt = prompt_response.prompt
                prompt_metadata = prompt_response.metadata

            logger.info(f"🎯 Prompt construído: {prompt[:100]}...")

            # 2. Gerar imagem com DALL-E
            dalle_request = ImageGenerationRequest(
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                style="vivid"
            )

            dalle_result = await self.dalle_client.generate_image(dalle_request)
            logger.info("🖼️  Imagem gerada pelo DALL-E")

            # 3. Salvar imagem e metadados
            storage_metadata = {
                'dalle_response': dalle_result.metadata,
                'prompt_metadata': prompt_metadata,
                'generation_task': {
                    'embedding_id': task.embedding_id,
                    'original_text_length': len(task.text),
                    'has_custom_prompt': bool(task.custom_prompt),
                    'style_preferences': task.style_preferences
                },
                'generation_time': (datetime.now() - generation_start).total_seconds()
            }

            image_path = await self.storage_manager.save_image(
                image_data=dalle_result.image_data,
                embedding_id=task.embedding_id,
                title=task.title,
                prompt=prompt,
                metadata=storage_metadata
            )

            total_time = (datetime.now() - generation_start).total_seconds()
            logger.info(f"✅ Imagem gerada com sucesso em {total_time:.2f}s: {image_path}")

            return ImageGenerationResult(
                success=True,
                image_path=image_path,
                metadata={
                    'prompt_used': prompt,
                    'dalle_url': dalle_result.image_url,
                    'revised_prompt': dalle_result.revised_prompt,
                    'total_generation_time': total_time,
                    'storage_metadata': storage_metadata
                }
            )

        except Exception as e:
            logger.error(f"❌ Erro na geração de imagem: {e}")
            return ImageGenerationResult(
                success=False,
                error_message=str(e),
                metadata={'error_type': type(e).__name__}
            )

    async def generate_multiple_images(self, tasks: List[ImageGenerationTask],
                                       max_concurrent: int = 3) -> List[ImageGenerationResult]:
        """Gera múltiplas imagens em paralelo com limite de concorrência"""
        try:
            logger.info(f"🎨 Gerando {len(tasks)} imagens com máximo {max_concurrent} simultâneas")

            semaphore = asyncio.Semaphore(max_concurrent)

            async def generate_with_semaphore(task: ImageGenerationTask) -> ImageGenerationResult:
                async with semaphore:
                    return await self.generate_image(task)

            # Executar todas as tarefas com controle de concorrência
            results = await asyncio.gather(
                *[generate_with_semaphore(task) for task in tasks],
                return_exceptions=True
            )

            # Processar resultados
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append(ImageGenerationResult(
                        success=False,
                        error_message=str(result),
                        metadata={'task_index': i, 'error_type': type(result).__name__}
                    ))
                else:
                    processed_results.append(result)

            success_count = sum(1 for r in processed_results if r.success)
            logger.info(f"✅ {success_count}/{len(tasks)} imagens geradas com sucesso")

            return processed_results

        except Exception as e:
            logger.error(f"❌ Erro na geração múltipla: {e}")
            return [ImageGenerationResult(
                success=False,
                error_message=str(e),
                metadata={'error_type': type(e).__name__}
            ) for _ in tasks]

    async def regenerate_image(self, embedding_id: str,
                               new_prompt: Optional[str] = None) -> ImageGenerationResult:
        """Regenera imagem para um embedding existente"""
        try:
            logger.info(f"🔄 Regenerando imagem para embedding {embedding_id}")

            # Buscar dados do embedding original
            from embeddings.models import Embedding
            from asgiref.sync import sync_to_async

            @sync_to_async
            def get_embedding_data():
                embedding = Embedding.objects.get(id=embedding_id)
                return {
                    'content': embedding.content,
                    'title': embedding.title or 'Untitled',
                    'metadata': embedding.metadata
                }

            embedding_data = await get_embedding_data()

            # Criar nova tarefa
            task = ImageGenerationTask(
                embedding_id=embedding_id,
                text=embedding_data['content'],
                title=embedding_data['title'],
                custom_prompt=new_prompt
            )

            # Gerar nova imagem
            result = await self.generate_image(task)

            if result.success:
                logger.info(f"✅ Imagem regenerada: {result.image_path}")
            else:
                logger.error(f"❌ Falha na regeneração: {result.error_message}")

            return result

        except Exception as e:
            logger.error(f"❌ Erro na regeneração: {e}")
            return ImageGenerationResult(
                success=False,
                error_message=str(e),
                metadata={'error_type': type(e).__name__}
            )

    async def get_generation_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas de geração"""
        try:
            storage_stats = await self.storage_manager.get_storage_stats()

            return {
                'initialized': self.is_initialized,
                'storage_stats': storage_stats,
                'components_status': {
                    'prompt_builder': self.prompt_builder.is_initialized,
                    'dalle_client': self.dalle_client.is_initialized,
                    'storage_manager': self.storage_manager.is_initialized
                }
            }

        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return {'error': str(e)}

    async def close(self) -> None:
        """Encerra todos os componentes"""
        try:
            logger.info("🔄 Encerrando Unipost Image Generator...")

            # Encerrar componentes em paralelo
            await asyncio.gather(
                self.prompt_builder.close(),
                self.dalle_client.close(),
                self.storage_manager.close(),
                return_exceptions=True
            )

            self.is_initialized = False
            logger.info("✅ Image Generator encerrado")

        except Exception as e:
            logger.error(f"❌ Erro no encerramento: {e}")


# Função utilitária para uso direto
async def generate_image_for_post(embedding_id: str, text: str, title: str,
                                  style_preferences: Optional[Dict[str, str]] = None) -> ImageGenerationResult:
    """Função utilitária para gerar imagem rapidamente"""
    generator = UnipostImageGenerator()

    try:
        await generator.initialize()

        task = ImageGenerationTask(
            embedding_id=embedding_id,
            text=text,
            title=title,
            style_preferences=style_preferences
        )

        return await generator.generate_image(task)
    finally:
        await generator.close()


# Função para integração com unipost_automation
async def process_post_for_images(formatted_data: Dict[str, Any]) -> Optional[str]:
    """
    Função específica para ser chamada pelo unipost_automation
    Retorna o caminho da imagem gerada ou None em caso de erro
    """
    try:
        embedding_data = formatted_data.get('embedding', {})
        if not embedding_data:
            logger.error("❌ Dados de embedding não encontrados")
            return None

        embedding_id = embedding_data.get('id')
        if not embedding_id:
            logger.error("❌ ID do embedding não encontrado")
            return None

        # Extrair dados para geração
        content = embedding_data.get('content', '')
        title = embedding_data.get('title', 'Untitled')

        # Gerar imagem
        result = await generate_image_for_post(
            embedding_id=embedding_id,
            text=content,
            title=title
        )

        if result.success:
            logger.info(f"✅ Imagem gerada para automação: {result.image_path}")
            return result.image_path
        else:
            logger.error(f"❌ Falha na geração para automação: {result.error_message}")
            return None

    except Exception as e:
        logger.error(f"❌ Erro no processamento para automação: {e}")
        return None
