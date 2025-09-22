#!/usr/bin/env python3
"""
WordPress Client Unipost Automation
Cliente para postagem automática no WordPress via REST API
"""

import os
import sys
import logging
import base64
from typing import Dict, Any, Optional, List
import httpx
from dotenv import load_dotenv

# Django setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

import django
django.setup()

# Load environment variables
load_dotenv()

# Logging setup
logger = logging.getLogger(__name__)


class WordPressClient:
    """Cliente para integração com WordPress REST API"""

    def __init__(self):
        self.wp_url = os.getenv('WORDPRESS_URL', '')
        self.wp_username = os.getenv('WORDPRESS_USERNAME', '')
        self.wp_password = os.getenv('WORDPRESS_APP_PASSWORD', '')
        self.client: Optional[httpx.AsyncClient] = None
        self.auth_header = ""

    async def initialize(self) -> bool:
        """Inicializa o cliente WordPress"""
        try:
            # Valida configurações
            if not all([self.wp_url, self.wp_username, self.wp_password]):
                logger.error("❌ Configurações do WordPress não encontradas")
                logger.error("Required: WORDPRESS_URL, WORDPRESS_USERNAME, WORDPRESS_APP_PASSWORD")
                return False

            # Prepara autenticação básica
            credentials = f"{self.wp_username}:{self.wp_password}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            self.auth_header = f"Basic {encoded_credentials}"

            # Inicializa cliente HTTP
            self.client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    'Authorization': self.auth_header,
                    'Content-Type': 'application/json',
                    'User-Agent': 'Unipost-Automation/1.0'
                }
            )

            # Testa conexão
            if await self.test_connection():
                logger.info("🌐 WordPress Client inicializado")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao inicializar WordPress Client: {e}")
            return False

    async def close(self) -> None:
        """Fecha o cliente"""
        if self.client:
            await self.client.aclose()

    async def test_connection(self) -> bool:
        """Testa conexão com WordPress"""
        try:
            api_url = f"{self.wp_url.rstrip('/')}/wp-json/wp/v2/users/me"
            response = await self.client.get(api_url)

            if response.status_code == 200:
                user_info = response.json()
                logger.info(f"✅ Conectado ao WordPress como: {user_info.get('name', 'N/A')}")
                return True
            else:
                logger.error(f"❌ Falha na autenticação WordPress: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao testar conexão WordPress: {e}")
            return False

    async def get_categories(self) -> List[Dict[str, Any]]:
        """Obtém lista de categorias do WordPress"""
        try:
            api_url = f"{self.wp_url.rstrip('/')}/wp-json/wp/v2/categories"
            response = await self.client.get(api_url)

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"⚠️  Falha ao obter categorias: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"❌ Erro ao obter categorias: {e}")
            return []

    async def create_category(self, name: str, description: str = "") -> Optional[int]:
        """Cria uma nova categoria"""
        try:
            api_url = f"{self.wp_url.rstrip('/')}/wp-json/wp/v2/categories"

            category_data = {
                'name': name,
                'description': description
            }

            response = await self.client.post(api_url, json=category_data)

            if response.status_code == 201:
                category = response.json()
                logger.info(f"📁 Categoria criada: {name} (ID: {category['id']})")
                return category['id']
            else:
                logger.warning(f"⚠️  Falha ao criar categoria {name}: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ Erro ao criar categoria {name}: {e}")
            return None

    async def get_or_create_category(self, category_name: str) -> Optional[int]:
        """Obtém ID da categoria ou cria se não existir"""
        try:
            # Busca categoria existente
            categories = await self.get_categories()

            for category in categories:
                if category['name'].lower() == category_name.lower():
                    return category['id']

            # Cria nova categoria se não existe
            return await self.create_category(category_name)

        except Exception as e:
            logger.error(f"❌ Erro ao obter/criar categoria {category_name}: {e}")
            return None

    async def upload_media(self, image_url: str, title: str = "") -> Optional[int]:
        """Faz upload de imagem para biblioteca de mídia"""
        try:
            # Baixa imagem
            image_response = await self.client.get(image_url)
            if image_response.status_code != 200:
                return None

            # Prepara upload
            api_url = f"{self.wp_url.rstrip('/')}/wp-json/wp/v2/media"

            filename = image_url.split('/')[-1].split('?')[0]
            if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                filename += '.jpg'

            # Headers para upload de mídia
            headers = {
                'Authorization': self.auth_header,
                'Content-Disposition': f'attachment; filename="{filename}"'
            }

            # Remove Content-Type para upload de mídia
            upload_client = httpx.AsyncClient(
                timeout=60.0,
                headers=headers
            )

            response = await upload_client.post(
                api_url,
                content=image_response.content,
                params={
                    'title': title or filename,
                    'alt_text': title
                }
            )

            await upload_client.aclose()

            if response.status_code == 201:
                media = response.json()
                logger.info(f"🖼️  Imagem uploaded: {filename} (ID: {media['id']})")
                return media['id']
            else:
                logger.warning(f"⚠️  Falha no upload de {filename}: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ Erro no upload de mídia {image_url}: {e}")
            return None

    async def create_post(self, formatted_data: Dict[str, Any]) -> Optional[int]:
        """Cria um novo post no WordPress"""
        try:
            wordpress_data = formatted_data.get('wordpress', {})
            if not wordpress_data:
                logger.error("❌ Dados do WordPress não encontrados")
                return None

            title = wordpress_data.get('title', 'Sem título')
            content = wordpress_data.get('content', '')
            excerpt = wordpress_data.get('excerpt', '')
            metadata = wordpress_data.get('metadata', {})

            logger.info(f"📝 Criando post: {title}")

            # Prepara dados do post
            post_data = {
                'title': title,
                'content': content,
                'excerpt': excerpt,
                'status': 'draft',  # Sempre como rascunho
                'author': 1,  # ID do autor (usuário autenticado)
                'meta': {
                    'source_url': metadata.get('source_url', ''),
                    'original_author': metadata.get('original_author', ''),
                    'scraped_at': metadata.get('scraped_at', ''),
                    'unipost_automation': True
                }
            }

            # Processa categorias se disponível
            categories = metadata.get('categories', [])
            if categories:
                category_ids = []
                for cat_name in categories[:3]:  # Máximo 3 categorias
                    cat_id = await self.get_or_create_category(cat_name)
                    if cat_id:
                        category_ids.append(cat_id)

                if category_ids:
                    post_data['categories'] = category_ids

            # TODO: Processar imagens (upload para WordPress)
            # Por enquanto, as imagens ficam com URLs externas no conteúdo

            # Cria o post
            api_url = f"{self.wp_url.rstrip('/')}/wp-json/wp/v2/posts"
            response = await self.client.post(api_url, json=post_data)

            if response.status_code == 201:
                post = response.json()
                post_id = post['id']
                post_url = post.get('link', 'N/A')

                logger.info(f"✅ Post criado: ID {post_id}")
                logger.info(f"🔗 URL: {post_url}")

                return post_id
            else:
                logger.error(f"❌ Falha ao criar post: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None

        except Exception as e:
            logger.error(f"❌ Erro ao criar post: {e}")
            return None

    async def update_post(self, post_id: int, updates: Dict[str, Any]) -> bool:
        """Atualiza um post existente"""
        try:
            api_url = f"{self.wp_url.rstrip('/')}/wp-json/wp/v2/posts/{post_id}"
            response = await self.client.post(api_url, json=updates)

            if response.status_code == 200:
                logger.info(f"✅ Post {post_id} atualizado")
                return True
            else:
                logger.error(f"❌ Falha ao atualizar post {post_id}: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao atualizar post {post_id}: {e}")
            return False

    async def publish_post(self, post_id: int) -> bool:
        """Publica um post (muda status de draft para publish)"""
        try:
            return await self.update_post(post_id, {'status': 'publish'})
        except Exception as e:
            logger.error(f"❌ Erro ao publicar post {post_id}: {e}")
            return False

    async def delete_post(self, post_id: int) -> bool:
        """Move post para lixeira"""
        try:
            api_url = f"{self.wp_url.rstrip('/')}/wp-json/wp/v2/posts/{post_id}"
            response = await self.client.delete(api_url)

            if response.status_code == 200:
                logger.info(f"🗑️  Post {post_id} movido para lixeira")
                return True
            else:
                logger.error(f"❌ Falha ao deletar post {post_id}: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao deletar post {post_id}: {e}")
            return False

    async def get_post_info(self, post_id: int) -> Optional[Dict[str, Any]]:
        """Obtém informações de um post"""
        try:
            api_url = f"{self.wp_url.rstrip('/')}/wp-json/wp/v2/posts/{post_id}"
            response = await self.client.get(api_url)

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"⚠️  Post {post_id} não encontrado: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"❌ Erro ao obter info do post {post_id}: {e}")
            return None


async def main():
    """Função de teste"""
    wp_client = WordPressClient()

    if await wp_client.initialize():
        print("✅ WordPress client inicializado")

        # Teste de categorias
        categories = await wp_client.get_categories()
        print(f"📁 {len(categories)} categorias encontradas")

        # Teste de criação de post (dados fictícios)
        test_data = {
            'wordpress': {
                'title': 'Post de Teste - Unipost Automation',
                'content': '<p>Este é um post de teste criado pelo Unipost Automation.</p>',
                'excerpt': 'Post de teste do sistema de automação.',
                'metadata': {
                    'source_url': 'https://example.com/test',
                    'categories': ['Teste', 'Automação']
                }
            }
        }

        post_id = await wp_client.create_post(test_data)
        if post_id:
            print(f"📝 Post de teste criado: ID {post_id}")
    else:
        print("❌ Falha na inicialização")

    await wp_client.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
