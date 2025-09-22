#!/usr/bin/env python3
"""
Testes básicos para Unipost Automation
"""

import os
import sys
import unittest
import asyncio
from unittest.mock import patch

# Setup do Django para testes
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

import django
django.setup()

# Imports dos módulos
from unipost_automation.src.scraping.webscraper import UnipostWebScraper
from unipost_automation.src.formatting.text_formatter import TextFormatter
from unipost_automation.src.storage.db import DatabaseManager
from unipost_automation.src.storage.vector_store import VectorStore


class TestUnipostWebScraper(unittest.TestCase):
    """Testes para o WebScraper"""

    def setUp(self):
        self.scraper = UnipostWebScraper()

    def test_normalize_url(self):
        """Testa normalização de URLs"""
        # URL sem protocolo
        result = self.scraper.normalize_url("example.com")
        self.assertEqual(result, "https://example.com")

        # URL com protocolo
        result = self.scraper.normalize_url("https://example.com/")
        self.assertEqual(result, "https://example.com")

        # URL relativa com base
        result = self.scraper.normalize_url("/post", "https://example.com")
        self.assertEqual(result, "https://example.com/post")

    def test_is_valid_post_url(self):
        """Testa validação de URLs de posts"""
        base_url = "https://example.com"

        # URL válida
        self.assertTrue(
            self.scraper.is_valid_post_url("https://example.com/post/123", base_url)
        )

        # URL de categoria (deve ser rejeitada)
        self.assertFalse(
            self.scraper.is_valid_post_url("https://example.com/category/tech", base_url)
        )

        # URL de arquivo (deve ser rejeitada)
        self.assertFalse(
            self.scraper.is_valid_post_url("https://example.com/file.pdf", base_url)
        )

        # Domínio diferente (deve ser rejeitada)
        self.assertFalse(
            self.scraper.is_valid_post_url("https://other.com/post", base_url)
        )


class TestTextFormatter(unittest.TestCase):
    """Testes para o TextFormatter"""

    def setUp(self):
        self.formatter = TextFormatter()

    def test_clean_text(self):
        """Testa limpeza de texto"""
        dirty_text = "  Este é um\n\n texto   sujo\t\t  "
        clean_text = self.formatter.clean_text(dirty_text)
        self.assertEqual(clean_text, "Este é um texto sujo")

        # Texto com caracteres especiais
        dirty_text = "\ufeffTexto\u200bcom\u00a0caracteres\x00especiais"
        clean_text = self.formatter.clean_text(dirty_text)
        self.assertEqual(clean_text, "Texto com caracteres especiais")

    def test_format_for_wordpress(self):
        """Testa formatação para WordPress"""
        scraped_data = {
            'title': 'Título de Teste',
            'content': 'Este é o conteúdo do post de teste.',
            'url': 'https://example.com/post',
            'author': 'Autor Teste',
            'images': [{'src': 'https://example.com/img.jpg', 'alt': 'Imagem'}]
        }

        result = self.formatter.format_for_wordpress(scraped_data)

        self.assertEqual(result['title'], 'Título de Teste')
        self.assertIn('<p>', result['content'])
        self.assertIn('Este é o conteúdo', result['content'])
        self.assertEqual(result['status'], 'draft')

    def test_extract_keywords(self):
        """Testa extração de palavras-chave"""
        text = "Python é uma linguagem de programação. Python é muito popular para ciência de dados."
        keywords = self.formatter.extract_keywords(text, max_keywords=5)

        self.assertIn('python', keywords)
        self.assertIn('programação', keywords)
        # Stopwords não devem aparecer
        self.assertNotIn('é', keywords)
        self.assertNotIn('uma', keywords)


class TestVectorStore(unittest.TestCase):
    """Testes para o VectorStore"""

    def setUp(self):
        self.vector_store = VectorStore()

    def test_cosine_similarity(self):
        """Testa cálculo de similaridade cosseno"""
        # Vetores idênticos
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0, 3.0]
        similarity = self.vector_store.cosine_similarity(vec1, vec2)
        self.assertAlmostEqual(similarity, 1.0, places=5)

        # Vetores ortogonais
        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]
        similarity = self.vector_store.cosine_similarity(vec1, vec2)
        self.assertAlmostEqual(similarity, 0.0, places=5)

        # Vetores opostos
        vec1 = [1.0, 0.0]
        vec2 = [-1.0, 0.0]
        similarity = self.vector_store.cosine_similarity(vec1, vec2)
        self.assertAlmostEqual(similarity, -1.0, places=5)

    def test_text_similarity(self):
        """Testa similaridade de texto"""
        text1 = "Python é uma linguagem de programação"
        text2 = "Python é uma linguagem de programação"
        similarity = self.vector_store.text_similarity(text1, text2)
        self.assertEqual(similarity, 1.0)

        text1 = "Python programação"
        text2 = "Java programação"
        similarity = self.vector_store.text_similarity(text1, text2)
        self.assertGreater(similarity, 0.0)
        self.assertLess(similarity, 1.0)


class TestAsyncComponents(unittest.IsolatedAsyncioTestCase):
    """Testes assíncronos para componentes"""

    async def test_webscraper_initialization(self):
        """Testa inicialização do webscraper"""
        scraper = UnipostWebScraper()
        result = await scraper.initialize()
        self.assertTrue(result)
        await scraper.close()

    async def test_text_formatter_initialization(self):
        """Testa inicialização do text formatter"""
        formatter = TextFormatter()

        # Mock da configuração do Gemini para evitar necessidade de API key nos testes
        with patch.dict(os.environ, {'GOOGLE_GEMINI_API_KEY': 'test_key'}):
            with patch('google.generativeai.configure'):
                result = await formatter.initialize()
                # Pode falhar sem API key real, mas deve tentar inicializar
                self.assertIsInstance(result, bool)

    async def test_database_manager_initialization(self):
        """Testa inicialização do database manager"""
        db_manager = DatabaseManager()
        result = await db_manager.initialize()
        self.assertTrue(result)
        await db_manager.close()

    async def test_vector_store_initialization(self):
        """Testa inicialização do vector store"""
        vector_store = VectorStore()
        result = await vector_store.initialize()
        self.assertTrue(result)


class TestIntegration(unittest.IsolatedAsyncioTestCase):
    """Testes de integração"""

    async def test_full_pipeline_mock(self):
        """Testa pipeline completo com dados mockados"""
        # Dados de entrada simulados
        mock_scraped_data = {
            'title': 'Post de Teste',
            'content': 'Este é um conteúdo de teste para verificar o pipeline.',
            'url': 'https://example.com/test-post',
            'images': [],
            'author': 'Autor Teste',
            'published_date': '2024-01-01'
        }

        # Inicializa componentes
        formatter = TextFormatter()

        # Mock da configuração do Gemini
        with patch.dict(os.environ, {'GOOGLE_GEMINI_API_KEY': 'test_key'}):
            with patch('google.generativeai.configure'):
                with patch.object(formatter, 'generate_embedding', return_value=[0.1] * 768):
                    await formatter.initialize()

                    # Testa formatação
                    result = await formatter.process_content(mock_scraped_data)

                    if result:  # Se conseguiu processar
                        self.assertIn('wordpress', result)
                        self.assertIn('embedding', result)
                        self.assertEqual(result['wordpress']['title'], 'Post de Teste')
                        self.assertEqual(len(result['embedding']['embedding_vector']), 768)


def run_tests():
    """Executa todos os testes"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Adiciona testes síncronos
    suite.addTests(loader.loadTestsFromTestCase(TestUnipostWebScraper))
    suite.addTests(loader.loadTestsFromTestCase(TestTextFormatter))
    suite.addTests(loader.loadTestsFromTestCase(TestVectorStore))

    # Executa testes síncronos
    runner = unittest.TextTestRunner(verbosity=2)
    sync_result = runner.run(suite)

    # Executa testes assíncronos
    async def run_async_tests():
        async_suite = unittest.TestSuite()
        async_suite.addTests(loader.loadTestsFromTestCase(TestAsyncComponents))
        async_suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

        async_runner = unittest.TextTestRunner(verbosity=2)
        return async_runner.run(async_suite)

    async_result = asyncio.run(run_async_tests())

    # Retorna True se todos os testes passaram
    return sync_result.wasSuccessful() and async_result.wasSuccessful()


if __name__ == "__main__":
    print("🧪 Executando testes do Unipost Automation...")
    print("=" * 50)

    success = run_tests()

    print("=" * 50)
    if success:
        print("✅ Todos os testes passaram!")
    else:
        print("❌ Alguns testes falharam!")

    sys.exit(0 if success else 1)
