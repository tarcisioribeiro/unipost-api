#!/usr/bin/env python3
"""
Prompt Builder - OpenAI GPT-4 Integration
Constrói prompts otimizados para geração de imagens usando OpenAI GPT-4
"""

import logging
import asyncio
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
import openai

logger = logging.getLogger(__name__)


@dataclass
class PromptRequest:
    """Estrutura para requisição de prompt"""
    text: str
    context: Optional[Dict[str, Any]] = None
    style_preferences: Optional[Dict[str, str]] = None


@dataclass
class PromptResponse:
    """Estrutura para resposta do prompt"""
    prompt: str
    confidence_score: float
    metadata: Dict[str, Any]


class OpenAIPromptBuilder:
    """Construtor de prompts usando OpenAI GPT-4"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY') or os.getenv('DALLE_API_KEY')
        self.client: Optional[openai.AsyncOpenAI] = None
        self.is_initialized = False
        self.default_style = {
            'art_style': 'digital illustration',
            'mood': 'professional and engaging',
            'quality': 'high quality, detailed',
            'format': '16:9 aspect ratio'
        }

    async def initialize(self) -> bool:
        """Inicializa a conexão com OpenAI GPT-4"""
        try:
            logger.info("🔌 Inicializando OpenAI GPT-4 Prompt Builder...")

            if not self.api_key:
                raise ValueError("OpenAI API Key não configurada (DALLE_API_KEY ou OPENAI_API_KEY)")

            # Inicializar cliente OpenAI
            self.client = openai.AsyncOpenAI(api_key=self.api_key)

            # Testar conexão com uma chamada simples
            await self._test_connection()

            self.is_initialized = True
            logger.info("✅ OpenAI GPT-4 Prompt Builder inicializado")
            return True

        except Exception as e:
            logger.error(f"❌ Erro na inicialização do OpenAI GPT-4: {e}")
            return False

    async def _test_connection(self) -> None:
        """Testa conexão com OpenAI API"""
        try:
            # Fazer uma requisição simples para testar
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            logger.info("✅ Conexão com OpenAI API validada")
        except Exception as e:
            logger.error(f"❌ Falha no teste de conexão: {e}")
            raise

    async def build_prompt(self, request: PromptRequest) -> PromptResponse:
        """Constrói prompt otimizado para DALL-E usando GPT-4"""
        if not self.is_initialized:
            raise RuntimeError("OpenAI GPT-4 não inicializado")

        try:
            logger.info(f"🎨 Construindo prompt para texto: {request.text[:100]}...")

            # Preparar contexto para GPT-4
            context = self._prepare_context(request)

            # Enviar para GPT-4
            gpt4_response = await self._call_gpt4(context)

            # Processar resposta
            response = self._process_gpt4_response(gpt4_response, request)

            logger.info(f"✅ Prompt construído: {response.prompt[:100]}...")
            return response

        except Exception as e:
            logger.error(f"❌ Erro na construção do prompt: {e}")
            raise

    def _prepare_context(self, request: PromptRequest) -> Dict[str, Any]:
        """Prepara contexto para envio ao GPT-4"""
        style = {**self.default_style, **(request.style_preferences or {})}

        return {
            'task': 'generate_image_prompt',
            'input_text': request.text,
            'style_preferences': style,
            'context': request.context or {},
            'requirements': {
                'target_model': 'dall-e-3',
                'max_prompt_length': 1000,
                'language': 'english',
                'content_type': 'blog_post_illustration'
            }
        }

    async def _call_gpt4(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Chama GPT-4 para gerar prompt otimizado para DALL-E"""
        try:
            # Construir prompt para GPT-4
            system_prompt = """You are an expert at creating optimized prompts for DALL-E 3 image generation.
Your task is to transform text content into detailed, creative visual prompts that will generate professional illustrations.

Guidelines:
- Maximum 1000 characters
- Be specific about visual elements, style, mood, and composition
- Focus on visual metaphors that represent the text content
- Use artistic terminology (lighting, perspective, color palette)
- Avoid text, watermarks, or specific people
- Make it engaging and professional for social media posts"""

            user_prompt = f"""Transform this text into an optimized DALL-E 3 prompt:

TEXT: {context['input_text']}

STYLE PREFERENCES:
- Art Style: {context['style_preferences']['art_style']}
- Mood: {context['style_preferences']['mood']}
- Quality: {context['style_preferences']['quality']}
- Format: {context['style_preferences']['format']}

Create a detailed visual prompt that captures the essence of this content:"""

            # Fazer chamada para GPT-4
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )

            generated_prompt = response.choices[0].message.content.strip()

            # Garantir que não exceda limite do DALL-E
            if len(generated_prompt) > 1000:
                generated_prompt = generated_prompt[:997] + "..."

            return {
                'prompt': generated_prompt,
                'confidence': 0.9,
                'metadata': {
                    'model_used': 'gpt-4',
                    'tokens_used': response.usage.total_tokens,
                    'style_applied': context['style_preferences']
                }
            }

        except Exception as e:
            logger.error(f"❌ Erro na chamada GPT-4: {e}")
            # Fallback para prompt manual se GPT-4 falhar
            fallback_prompt = self._generate_fallback_prompt(context)
            return {
                'prompt': fallback_prompt,
                'confidence': 0.7,
                'metadata': {
                    'model_used': 'fallback',
                    'fallback_reason': str(e),
                    'style_applied': context['style_preferences']
                }
            }

    def _generate_fallback_prompt(self, context: Dict[str, Any]) -> str:
        """Gera prompt fallback quando GPT-4 não está disponível"""
        text = context['input_text']
        style = context['style_preferences']

        # Extrair conceitos principais do texto
        key_concepts = self._extract_key_concepts(text)

        # Construir prompt estruturado
        prompt_parts = [
            f"Create a {style['art_style']}"
        ]

        if key_concepts:
            prompt_parts.append(f"illustrating {', '.join(key_concepts[:3])}")

        prompt_parts.extend([
            f"with a {style['mood']} atmosphere",
            f"{style['quality']}",
            f"{style['format']}",
            "no text or watermarks"
        ])

        return ", ".join(prompt_parts)

    def _extract_key_concepts(self, text: str) -> list:
        """Extrai conceitos principais do texto"""
        # Implementação simples - em produção, usar NLP mais sofisticado
        words = text.lower().split()

        # Palavras-chave comuns para posts
        important_words = []
        keywords = ['technology', 'business', 'innovation', 'digital', 'future',
                    'growth', 'success', 'strategy', 'data', 'AI', 'automation']

        for word in words:
            if word in keywords and word not in important_words:
                important_words.append(word)

        return important_words[:5]

    def _process_gpt4_response(self, gpt4_response: Dict[str, Any],
                              request: PromptRequest) -> PromptResponse:
        """Processa resposta do GPT-4"""
        return PromptResponse(
            prompt=gpt4_response['prompt'],
            confidence_score=gpt4_response['confidence'],
            metadata={
                'original_text_length': len(request.text),
                'gpt4_metadata': gpt4_response['metadata'],
                'style_applied': request.style_preferences or self.default_style
            }
        )

    async def close(self) -> None:
        """Encerra conexões do OpenAI GPT-4"""
        try:
            logger.info("🔌 Encerrando OpenAI GPT-4 Prompt Builder...")
            self.is_initialized = False
            logger.info("✅ OpenAI GPT-4 encerrado")
        except Exception as e:
            logger.error(f"❌ Erro no encerramento: {e}")


# Função utilitária para uso direto
async def build_prompt_for_text(text: str,
                                style_preferences: Optional[Dict[str, str]] = None) -> str:
    """Função utilitária para construir prompt rapidamente"""
    builder = OpenAIPromptBuilder()

    try:
        await builder.initialize()
        request = PromptRequest(text=text, style_preferences=style_preferences)
        response = await builder.build_prompt(request)
        return response.prompt
    finally:
        await builder.close()


# Alias para compatibilidade (manter nome antigo)
ClaudePromptBuilder = OpenAIPromptBuilder
