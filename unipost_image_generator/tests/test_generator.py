#!/usr/bin/env python3
"""
Testes unitários para o módulo unipost_image_generator
"""

from unipost_image_generator.generator import UnipostImageGenerator, ImageGenerationTask
from unipost_image_generator.storage import ImageStorageManager
from unipost_image_generator.clients import DalleApiClient, ImageGenerationRequest
from unipost_image_generator.prompt_builder import ClaudePromptBuilder, PromptRequest
import django
import os
import sys
import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

# Django setup para testes
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

django.setup()


class TestPromptBuilder(unittest.TestCase):
    """Testes para o construtor de prompts"""

    def setUp(self):
        self.prompt_builder = ClaudePromptBuilder()

    def test_prompt_request_creation(self):
        """Testa criação de PromptRequest"""
        request = PromptRequest(
            text="Test post content",
            style_preferences={"art_style": "digital"}
        )

        self.assertEqual(request.text, "Test post content")
        self.assertEqual(request.style_preferences["art_style"], "digital")

    def test_extract_key_concepts(self):
        """Testa extração de conceitos principais"""
        text = "This post discusses AI technology and business innovation"
        concepts = self.prompt_builder._extract_key_concepts(text)

        self.assertIsInstance(concepts, list)
        self.assertTrue(any('technology' in concept for concept in concepts))

    def test_generate_fallback_prompt(self):
        """Testa geração de prompt fallback"""
        context = {
            'input_text': 'AI technology business innovation',
            'style_preferences': {
                'art_style': 'digital illustration',
                'mood': 'professional',
                'quality': 'high quality',
                'format': '16:9'
            }
        }

        prompt = self.prompt_builder._generate_fallback_prompt(context)

        self.assertIsInstance(prompt, str)
        self.assertIn('digital illustration', prompt)
        self.assertIn('professional', prompt)

    @patch('asyncio.sleep', new_callable=AsyncMock)
    async def test_async_build_prompt(self, mock_sleep):
        """Testa construção de prompt assíncrona"""
        await self.prompt_builder.initialize()

        request = PromptRequest(text="Test content for image generation")
        response = await self.prompt_builder.build_prompt(request)

        self.assertIsNotNone(response.prompt)
        self.assertIsInstance(response.confidence_score, float)
        self.assertIsInstance(response.metadata, dict)


class TestDalleClient(unittest.TestCase):
    """Testes para o cliente DALL-E"""

    def setUp(self):
        self.dalle_client = DalleApiClient(api_key="test_key")

    def test_image_generation_request_creation(self):
        """Testa criação de ImageGenerationRequest"""
        request = ImageGenerationRequest(
            prompt="Test prompt",
            size="1024x1024",
            quality="standard"
        )

        self.assertEqual(request.prompt, "Test prompt")
        self.assertEqual(request.size, "1024x1024")

    def test_validate_prompt_valid(self):
        """Testa validação de prompt válido"""
        valid_prompt = "A beautiful landscape with mountains"

        # Não deve lançar exceção
        try:
            self.dalle_client._validate_prompt(valid_prompt)
        except ValueError:
            self.fail("Prompt válido não deveria lançar exceção")

    def test_validate_prompt_empty(self):
        """Testa validação de prompt vazio"""
        with self.assertRaises(ValueError):
            self.dalle_client._validate_prompt("")

    def test_validate_prompt_too_long(self):
        """Testa validação de prompt muito longo"""
        long_prompt = "a" * 1001
        with self.assertRaises(ValueError):
            self.dalle_client._validate_prompt(long_prompt)

    def test_validate_prompt_forbidden_content(self):
        """Testa validação de conteúdo proibido"""
        with self.assertRaises(ValueError):
            self.dalle_client._validate_prompt("nude content")

    def test_validate_image_valid(self):
        """Testa validação de dados de imagem válidos"""
        # Simular dados de imagem PNG mínimos
        fake_png_data = b'\x89PNG\r\n\x1a\n' + b'0' * 1024

        with patch('PIL.Image.open') as mock_open:
            mock_image = Mock()
            mock_image.format = 'PNG'
            mock_image.size = (1024, 1024)
            mock_open.return_value = mock_image

            # Não deve lançar exceção
            try:
                self.dalle_client._validate_image(fake_png_data)
            except ValueError:
                self.fail("Dados de imagem válidos não deveriam lançar exceção")

    def test_validate_image_empty(self):
        """Testa validação de dados de imagem vazios"""
        with self.assertRaises(ValueError):
            self.dalle_client._validate_image(b'')


class TestImageStorageManager(unittest.TestCase):
    """Testes para o gerenciador de storage"""

    def setUp(self):
        self.storage_manager = ImageStorageManager()

    def test_generate_filename(self):
        """Testa geração de nome de arquivo"""
        embedding_id = "12345678-1234-1234-1234-123456789abc"
        title = "Test Article Title"

        filename = self.storage_manager._generate_filename(embedding_id, title)

        self.assertIsInstance(filename, str)
        self.assertTrue(filename.endswith('.png'))
        self.assertIn('12345678', filename)  # ID curto
        self.assertIn('Test_Article_Title', filename)

    def test_generate_filename_special_chars(self):
        """Testa geração de nome com caracteres especiais"""
        embedding_id = "12345678-1234-1234-1234-123456789abc"
        title = "Test@#$%^&*()Title!!!"

        filename = self.storage_manager._generate_filename(embedding_id, title)

        # Deve remover caracteres especiais
        self.assertNotIn('@', filename)
        self.assertNotIn('#', filename)
        self.assertNotIn('!', filename)

    def test_generate_filename_empty_title(self):
        """Testa geração de nome com título vazio"""
        embedding_id = "12345678-1234-1234-1234-123456789abc"
        title = ""

        filename = self.storage_manager._generate_filename(embedding_id, title)

        self.assertIn('untitled', filename)


class TestUnipostImageGenerator(unittest.TestCase):
    """Testes para o gerador principal"""

    def setUp(self):
        self.generator = UnipostImageGenerator()

    def test_image_generation_task_creation(self):
        """Testa criação de ImageGenerationTask"""
        task = ImageGenerationTask(
            embedding_id="test-id",
            text="Test content",
            title="Test Title",
            style_preferences={"art_style": "digital"}
        )

        self.assertEqual(task.embedding_id, "test-id")
        self.assertEqual(task.text, "Test content")
        self.assertEqual(task.title, "Test Title")

    @patch('unipost_image_generator.generator.ClaudePromptBuilder')
    @patch('unipost_image_generator.generator.DalleApiClient')
    @patch('unipost_image_generator.generator.ImageStorageManager')
    async def test_initialize_success(self, mock_storage, mock_dalle, mock_prompt):
        """Testa inicialização bem-sucedida"""
        # Configurar mocks para retornar True
        mock_prompt.return_value.initialize = AsyncMock(return_value=True)
        mock_dalle.return_value.initialize = AsyncMock(return_value=True)
        mock_storage.return_value.initialize = AsyncMock(return_value=True)

        generator = UnipostImageGenerator()
        result = await generator.initialize()

        self.assertTrue(result)
        self.assertTrue(generator.is_initialized)

    @patch('unipost_image_generator.generator.ClaudePromptBuilder')
    @patch('unipost_image_generator.generator.DalleApiClient')
    @patch('unipost_image_generator.generator.ImageStorageManager')
    async def test_initialize_failure(self, mock_storage, mock_dalle, mock_prompt):
        """Testa falha na inicialização"""
        # Configurar um mock para falhar
        mock_prompt.return_value.initialize = AsyncMock(return_value=False)
        mock_dalle.return_value.initialize = AsyncMock(return_value=True)
        mock_storage.return_value.initialize = AsyncMock(return_value=True)

        generator = UnipostImageGenerator()
        result = await generator.initialize()

        self.assertFalse(result)
        self.assertFalse(generator.is_initialized)


class TestIntegration(unittest.TestCase):
    """Testes de integração"""

    def test_import_modules(self):
        """Testa se todos os módulos podem ser importados"""
        try:
            import unipost_image_generator.prompt_builder  # noqa: F401
            import unipost_image_generator.clients  # noqa: F401
            import unipost_image_generator.storage  # noqa: F401
            import unipost_image_generator.generator  # noqa: F401
            import unipost_image_generator.models  # noqa: F401
            import unipost_image_generator.serializers  # noqa: F401
            import unipost_image_generator.views  # noqa: F401
        except ImportError as e:
            self.fail(f"Falha ao importar módulos: {e}")

    def test_django_models(self):
        """Testa se os modelos Django foram criados corretamente"""
        from unipost_image_generator.models import GeneratedImage
        from embeddings.models import Embedding  # noqa: F401

        # Verificar se os modelos existem
        self.assertTrue(hasattr(GeneratedImage, 'embedding'))
        self.assertTrue(hasattr(GeneratedImage, 'original_text'))
        self.assertTrue(hasattr(GeneratedImage, 'generated_prompt'))

    def test_serializers(self):
        """Testa se os serializers funcionam"""
        from unipost_image_generator.serializers import (
            ImageGenerationRequestSerializer
        )

        # Testar serializer de requisição
        data = {
            'text': 'Test content',
            'embedding_id': '12345678-1234-1234-1234-123456789abc'
        }

        serializer = ImageGenerationRequestSerializer(data=data)
        self.assertTrue(serializer.is_valid())


def run_async_test(coro):
    """Utilitário para executar testes assíncronos"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


if __name__ == '__main__':
    # Executar testes assíncronos
    async_tests = [
        TestPromptBuilder().test_async_build_prompt(),
        TestUnipostImageGenerator().test_initialize_success(),
        TestUnipostImageGenerator().test_initialize_failure(),
    ]

    for test in async_tests:
        try:
            run_async_test(test)
            print("✅ Teste assíncrono passou")
        except Exception as e:
            print(f"❌ Teste assíncrono falhou: {e}")

    # Executar testes síncronos
    unittest.main(verbosity=2)
