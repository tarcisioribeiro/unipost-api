#!/usr/bin/env python3
"""
Vector Store Unipost Automation
Gerencia operações de busca e similaridade com embeddings
"""

import os
import sys
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from asgiref.sync import sync_to_async

# Django setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')

import django
django.setup()

from embeddings.models import Embedding

# Logging setup
logger = logging.getLogger(__name__)


class VectorStore:
    """Gerenciador de operações com embeddings/vetores"""

    def __init__(self):
        self.similarity_threshold = 0.8  # Threshold para considerar similar

    async def initialize(self) -> bool:
        """Inicializa o vector store"""
        try:
            logger.info("🔍 Vector Store inicializado")
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao inicializar Vector Store: {e}")
            return False

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcula similaridade cosseno entre dois vetores"""
        try:
            # Converte para numpy arrays
            a = np.array(vec1)
            b = np.array(vec2)

            # Calcula similaridade cosseno
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)

            if norm_a == 0 or norm_b == 0:
                return 0.0

            similarity = dot_product / (norm_a * norm_b)
            return float(similarity)

        except Exception as e:
            logger.error(f"❌ Erro ao calcular similaridade: {e}")
            return 0.0

    @sync_to_async
    def find_similar_content_sync(self, query_vector: List[float],
                                 limit: int = 10,
                                 min_similarity: float = 0.7) -> List[Dict[str, Any]]:
        """Busca conteúdo similar (versão síncrona)"""
        try:
            # Obtém todos os embeddings (em produção, seria melhor paginar)
            embeddings = Embedding.objects.filter(
                origin='webscraping'
            ).exclude(
                metadata__type='processing_record'
            )

            similar_items = []

            for embedding in embeddings:
                try:
                    # Calcula similaridade
                    similarity = self.cosine_similarity(
                        query_vector,
                        embedding.embedding_vector
                    )

                    if similarity >= min_similarity:
                        similar_items.append({
                            'id': str(embedding.id),
                            'title': embedding.title,
                            'content': embedding.content[:500] + "..." if len(embedding.content) > 500 else embedding.content,
                            'similarity': similarity,
                            'metadata': embedding.metadata,
                            'created_at': embedding.created_at.isoformat()
                        })

                except Exception as e:
                    logger.warning(f"⚠️  Erro ao processar embedding {embedding.id}: {e}")
                    continue

            # Ordena por similaridade
            similar_items.sort(key=lambda x: x['similarity'], reverse=True)

            return similar_items[:limit]

        except Exception as e:
            logger.error(f"❌ Erro na busca por similaridade: {e}")
            return []

    async def find_similar_content(self, query_vector: List[float],
                                 limit: int = 10,
                                 min_similarity: float = 0.7) -> List[Dict[str, Any]]:
        """Busca conteúdo similar baseado no vetor de consulta"""
        try:
            similar_items = await self.find_similar_content_sync(
                query_vector, limit, min_similarity
            )

            logger.info(f"🔍 {len(similar_items)} itens similares encontrados")
            return similar_items

        except Exception as e:
            logger.error(f"❌ Erro na busca por similaridade: {e}")
            return []

    @sync_to_async
    def check_duplicate_content_sync(self, content_vector: List[float],
                                   title: str = "") -> Optional[Dict[str, Any]]:
        """Verifica se existe conteúdo duplicado (versão síncrona)"""
        try:
            # Busca com threshold alto para duplicatas
            similar_items = self.find_similar_content_sync(
                content_vector,
                limit=5,
                min_similarity=self.similarity_threshold
            )

            # Se encontrou algo muito similar, considera duplicata
            for item in similar_items:
                if item['similarity'] >= self.similarity_threshold:
                    # Verifica se título também é similar (opcional)
                    if title and item['title']:
                        title_similarity = self.text_similarity(title, item['title'])
                        if title_similarity > 0.6:  # Título também similar
                            return item

                    # Mesmo sem título similar, se conteúdo é muito similar
                    if item['similarity'] >= 0.9:
                        return item

            return None

        except Exception as e:
            logger.error(f"❌ Erro ao verificar duplicatas: {e}")
            return None

    async def check_duplicate_content(self, content_vector: List[float],
                                    title: str = "") -> Optional[Dict[str, Any]]:
        """Verifica se existe conteúdo duplicado no banco"""
        try:
            duplicate = await self.check_duplicate_content_sync(content_vector, title)

            if duplicate:
                logger.warning(f"⚠️  Conteúdo duplicado encontrado: {duplicate['title']}")
                return duplicate
            else:
                logger.info("✅ Conteúdo único, não é duplicata")
                return None

        except Exception as e:
            logger.error(f"❌ Erro ao verificar duplicatas: {e}")
            return None

    def text_similarity(self, text1: str, text2: str) -> float:
        """Calcula similaridade básica entre textos"""
        try:
            # Converte para lowercase e remove espaços extras
            t1 = text1.lower().strip()
            t2 = text2.lower().strip()

            if not t1 or not t2:
                return 0.0

            # Jaccard similarity usando palavras
            words1 = set(t1.split())
            words2 = set(t2.split())

            intersection = words1.intersection(words2)
            union = words1.union(words2)

            if not union:
                return 0.0

            return len(intersection) / len(union)

        except Exception as e:
            logger.error(f"❌ Erro ao calcular similaridade de texto: {e}")
            return 0.0

    @sync_to_async
    def get_content_clusters_sync(self, min_cluster_size: int = 3) -> List[Dict[str, Any]]:
        """Agrupa conteúdo similar em clusters (versão síncrona)"""
        try:
            # Obtém todos os embeddings
            embeddings = list(Embedding.objects.filter(
                origin='webscraping'
            ).exclude(
                metadata__type='processing_record'
            ))

            clusters = []
            processed_ids = set()

            for i, embedding in enumerate(embeddings):
                if str(embedding.id) in processed_ids:
                    continue

                # Inicia novo cluster
                cluster = {
                    'id': len(clusters),
                    'representative': {
                        'id': str(embedding.id),
                        'title': embedding.title,
                        'content': embedding.content[:200] + "..."
                    },
                    'members': [str(embedding.id)],
                    'similarity_scores': []
                }

                processed_ids.add(str(embedding.id))

                # Encontra membros similares
                for j, other_embedding in enumerate(embeddings[i + 1:], i + 1):
                    if str(other_embedding.id) in processed_ids:
                        continue

                    similarity = self.cosine_similarity(
                        embedding.embedding_vector,
                        other_embedding.embedding_vector
                    )

                    if similarity >= 0.75:  # Threshold para cluster
                        cluster['members'].append(str(other_embedding.id))
                        cluster['similarity_scores'].append(similarity)
                        processed_ids.add(str(other_embedding.id))

                # Adiciona cluster se tem membros suficientes
                if len(cluster['members']) >= min_cluster_size:
                    clusters.append(cluster)

            return clusters

        except Exception as e:
            logger.error(f"❌ Erro ao criar clusters: {e}")
            return []

    async def get_content_clusters(self, min_cluster_size: int = 3) -> List[Dict[str, Any]]:
        """Agrupa conteúdo similar em clusters para análise"""
        try:
            clusters = await self.get_content_clusters_sync(min_cluster_size)
            logger.info(f"📊 {len(clusters)} clusters de conteúdo identificados")
            return clusters

        except Exception as e:
            logger.error(f"❌ Erro ao obter clusters: {e}")
            return []

    @sync_to_async
    def get_vector_stats_sync(self) -> Dict[str, Any]:
        """Obtém estatísticas dos vetores (versão síncrona)"""
        try:
            embeddings = Embedding.objects.filter(
                origin='webscraping'
            ).exclude(
                metadata__type='processing_record'
            )

            total_count = embeddings.count()
            if total_count == 0:
                return {'total_vectors': 0}

            # Pega uma amostra para análise
            sample_embeddings = list(embeddings[:100])

            vector_dimensions = []
            for embedding in sample_embeddings:
                if embedding.embedding_vector:
                    vector_dimensions.append(len(embedding.embedding_vector))

            avg_dimension = np.mean(vector_dimensions) if vector_dimensions else 0

            return {
                'total_vectors': total_count,
                'sample_size': len(sample_embeddings),
                'avg_vector_dimension': avg_dimension,
                'unique_dimensions': list(set(vector_dimensions))
            }

        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas de vetores: {e}")
            return {}

    async def get_vector_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas dos vetores armazenados"""
        try:
            stats = await self.get_vector_stats_sync()
            return stats

        except Exception as e:
            logger.error(f"❌ Erro ao obter estatísticas: {e}")
            return {}


async def main():
    """Função de teste"""
    vector_store = VectorStore()
    await vector_store.initialize()

    # Teste de estatísticas
    stats = await vector_store.get_vector_stats()
    print(f"📊 Estatísticas: {stats}")

    # Teste de clusters
    clusters = await vector_store.get_content_clusters()
    print(f"📊 {len(clusters)} clusters encontrados")

    print("✅ Vector Store testado com sucesso")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
