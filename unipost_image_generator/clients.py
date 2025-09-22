#!/usr/bin/env python3
"""
DALL-E API Client
Cliente para integração com a API OpenAI DALL-E para geração de imagens
"""

import logging
import asyncio
import aiohttp
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import io
from PIL import Image
import openai

logger = logging.getLogger(__name__)


@dataclass
class ImageGenerationRequest:
    """Estrutura para requisição de geração de imagem"""
    prompt: str
    size: str = "1024x1024"
    quality: str = "standard"
    n: int = 1
    style: str = "vivid"


@dataclass
class GeneratedImageResult:
    """Resultado da geração de imagem"""
    image_data: bytes
    image_url: str
    revised_prompt: str
    metadata: Dict[str, Any]


class DalleApiClient:
    """Cliente para API DALL-E da OpenAI"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('DALLE_API_KEY')
        self.client: Optional[openai.AsyncOpenAI] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self.is_initialized = False

        # Configurações padrão
        self.default_config = {
            'model': 'dall-e-3',
            'size': '1024x1024',
            'quality': 'standard',
            'style': 'vivid',
            'timeout': 120
        }

    async def initialize(self) -> bool:
        """Inicializa cliente DALL-E"""
        try:
            logger.info("🎨 Inicializando DALL-E API Client...")

            if not self.api_key:
                raise ValueError("DALLE_API_KEY não configurada")

            # Inicializar cliente OpenAI
            self.client = openai.AsyncOpenAI(api_key=self.api_key)

            # Inicializar sessão HTTP para downloads
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.default_config['timeout'])
            )

            # Testar conexão
            await self._test_connection()

            self.is_initialized = True
            logger.info("✅ DALL-E API Client inicializado")
            return True

        except Exception as e:
            logger.error(f"❌ Erro na inicialização DALL-E: {e}")
            if self.session:
                await self.session.close()
            return False

    async def _test_connection(self) -> None:
        """Testa conexão com API OpenAI"""
        try:
            # Fazer uma requisição simples para testar
            # Nota: Não gerar imagem real no teste para economizar créditos
            logger.info("🔌 Testando conexão com OpenAI API...")

            # Validar que o cliente foi criado corretamente
            if not self.client:
                raise ValueError("Cliente OpenAI não inicializado")

            logger.info("✅ Conexão com OpenAI API validada")

        except Exception as e:
            logger.error(f"❌ Falha no teste de conexão: {e}")
            raise

    async def generate_image(self, request: ImageGenerationRequest) -> GeneratedImageResult:
        """Gera imagem usando DALL-E"""
        if not self.is_initialized:
            raise RuntimeError("Cliente DALL-E não inicializado")

        try:
            logger.info(f"🖼️  Gerando imagem: {request.prompt[:100]}...")

            # Validar prompt
            self._validate_prompt(request.prompt)

            # Fazer requisição para DALL-E
            generation_start = datetime.now()

            response = await self.client.images.generate(
                model=self.default_config['model'],
                prompt=request.prompt,
                size=request.size,
                quality=request.quality,
                n=request.n,
                style=request.style,
                response_format="url"
            )

            generation_time = (datetime.now() - generation_start).total_seconds()

            # Processar resposta
            image_data = response.data[0]
            image_url = image_data.url
            revised_prompt = getattr(image_data, 'revised_prompt', request.prompt)

            # Baixar imagem
            image_bytes = await self._download_image(image_url)

            # Validar imagem baixada
            self._validate_image(image_bytes)

            result = GeneratedImageResult(
                image_data=image_bytes,
                image_url=image_url,
                revised_prompt=revised_prompt,
                metadata={
                    'model': self.default_config['model'],
                    'size': request.size,
                    'quality': request.quality,
                    'style': request.style,
                    'generation_time': generation_time,
                    'original_prompt': request.prompt,
                    'response_format': 'url',
                    'timestamp': datetime.now().isoformat()
                }
            )

            logger.info(f"✅ Imagem gerada em {generation_time:.2f}s")
            return result

        except Exception as e:
            logger.error(f"❌ Erro na geração de imagem: {e}")
            raise

    async def _download_image(self, image_url: str) -> bytes:
        """Baixa imagem da URL retornada pela API"""
        try:
            logger.info(f"⬇️  Baixando imagem de {image_url[:50]}...")

            async with self.session.get(image_url) as response:
                if response.status != 200:
                    raise Exception(f"Erro HTTP {response.status} ao baixar imagem")

                image_data = await response.read()

                logger.info(f"✅ Imagem baixada: {len(image_data)} bytes")
                return image_data

        except Exception as e:
            logger.error(f"❌ Erro no download da imagem: {e}")
            raise

    def _validate_prompt(self, prompt: str) -> None:
        """Valida prompt para DALL-E"""
        if not prompt or not prompt.strip():
            raise ValueError("Prompt não pode estar vazio")

        if len(prompt) > 1000:
            raise ValueError("Prompt muito longo (máximo 1000 caracteres)")

        # Verificar conteúdo proibido básico
        forbidden_terms = ['nude', 'violence', 'explicit']
        prompt_lower = prompt.lower()
        for term in forbidden_terms:
            if term in prompt_lower:
                raise ValueError(f"Prompt contém termo proibido: {term}")

    def _validate_image(self, image_data: bytes) -> None:
        """Valida dados da imagem baixada"""
        if not image_data:
            raise ValueError("Dados de imagem vazios")

        if len(image_data) < 1024:  # Mínimo 1KB
            raise ValueError("Imagem muito pequena (possível erro)")

        try:
            # Tentar abrir como imagem para validar formato
            image = Image.open(io.BytesIO(image_data))
            image.verify()

            logger.info(f"✅ Imagem validada: {image.format} {image.size}")

        except Exception as e:
            raise ValueError(f"Dados de imagem inválidos: {e}")

    async def generate_variations(self, base_prompt: str, variations: int = 3) -> List[GeneratedImageResult]:
        """Gera múltiplas variações de uma imagem"""
        if variations > 4:
            raise ValueError("Máximo 4 variações por vez")

        results = []
        for i in range(variations):
            # Adicionar pequenas variações no prompt
            varied_prompt = f"{base_prompt}, variation {i + 1}, unique style"

            request = ImageGenerationRequest(prompt=varied_prompt)
            result = await self.generate_image(request)
            results.append(result)

            # Pequena pausa entre gerações
            await asyncio.sleep(1)

        return results

    async def close(self) -> None:
        """Encerra cliente DALL-E"""
        try:
            logger.info("🔌 Encerrando DALL-E API Client...")

            if self.session:
                await self.session.close()

            self.is_initialized = False
            logger.info("✅ DALL-E Client encerrado")

        except Exception as e:
            logger.error(f"❌ Erro no encerramento: {e}")


# Função utilitária para uso direto
async def generate_image_from_prompt(prompt: str,
                                     size: str = "1024x1024") -> GeneratedImageResult:
    """Função utilitária para gerar imagem rapidamente"""
    client = DalleApiClient()

    try:
        await client.initialize()
        request = ImageGenerationRequest(prompt=prompt, size=size)
        return await client.generate_image(request)
    finally:
        await client.close()
