#!/usr/bin/env python3
"""
Script para remover duplicatas dos embeddings que possuam o mesmo title
e sejam da fonte 'business_brain'.
"""

import os
import sys
import logging
from pathlib import Path
from collections import defaultdict
import django

# Configuração do Django
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from embeddings.models import Embedding
from django.db.models import Count

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent / 'duplicates_remover.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DuplicatesRemover:
    """Remove duplicatas dos embeddings da fonte business_brain com base no título"""

    def __init__(self):
        self.removed_count = 0
        self.kept_count = 0

    def find_duplicates(self):
        """Encontra grupos de embeddings duplicados por título na origem business_brain"""
        logger.info("🔍 Buscando duplicatas em embeddings da origem 'business_brain'...")

        # Busca embeddings com títulos duplicados na origem business_brain
        duplicates = (
            Embedding.objects
            .filter(origin='business_brain')
            .exclude(title__isnull=True)
            .exclude(title='')
            .values('title')
            .annotate(count=Count('title'))
            .filter(count__gt=1)
            .order_by('-count')
        )

        logger.info(f"📊 Encontrados {duplicates.count()} títulos com duplicatas")

        return duplicates

    def remove_duplicates_for_title(self, title: str):
        """Remove duplicatas para um título específico, mantendo apenas o mais antigo"""
        embeddings = (
            Embedding.objects
            .filter(origin='business_brain', title=title)
            .order_by('created_at')  # Ordena por criação (mais antigo primeiro)
        )

        count = embeddings.count()
        if count <= 1:
            return 0

        # Mantém o primeiro (mais antigo) e remove os outros
        first_embedding = embeddings.first()
        duplicates_to_remove = embeddings.exclude(id=first_embedding.id)

        removed_ids = list(duplicates_to_remove.values_list('id', flat=True))
        duplicates_count = duplicates_to_remove.count()

        # Remove as duplicatas
        duplicates_to_remove.delete()

        logger.info(f"✅ Título: '{title}' - Mantido: {first_embedding.id} | Removidos: {duplicates_count} duplicatas")

        return duplicates_count

    def run(self):
        """Executa o processo completo de remoção de duplicatas"""
        logger.info("🚀 Iniciando remoção de duplicatas dos embeddings 'business_brain'")

        try:
            # Estatísticas iniciais
            total_business_brain = Embedding.objects.filter(origin='business_brain').count()
            logger.info(f"📈 Total de embeddings 'business_brain' antes: {total_business_brain}")

            # Encontra duplicatas
            duplicates = self.find_duplicates()

            if not duplicates:
                logger.info("✅ Nenhuma duplicata encontrada!")
                return

            # Remove duplicatas para cada título
            total_removed = 0

            for duplicate in duplicates:
                title = duplicate['title']
                duplicate_count = duplicate['count']

                logger.info(f"🔄 Processando título: '{title}' ({duplicate_count} duplicatas)")

                removed = self.remove_duplicates_for_title(title)
                total_removed += removed
                self.kept_count += 1  # Cada título mantém 1 embedding

            # Estatísticas finais
            total_after = Embedding.objects.filter(origin='business_brain').count()

            logger.info(f"\n{'='*60}")
            logger.info("🎉 REMOÇÃO DE DUPLICATAS CONCLUÍDA!")
            logger.info(f"📊 Embeddings 'business_brain' antes: {total_business_brain}")
            logger.info(f"📊 Embeddings 'business_brain' depois: {total_after}")
            logger.info(f"🗑️  Total removido: {total_removed}")
            logger.info(f"✅ Total mantido: {total_after}")
            logger.info(f"💾 Espaço liberado: {total_removed} embeddings duplicados")
            logger.info(f"{'='*60}")

        except Exception as e:
            logger.error(f"❌ Erro durante a remoção de duplicatas: {e}")
            raise

    def preview_duplicates(self):
        """Mostra uma prévia das duplicatas que seriam removidas sem removê-las"""
        logger.info("👀 MODO PREVIEW - Apenas visualizando duplicatas...")

        duplicates = self.find_duplicates()

        if not duplicates:
            logger.info("✅ Nenhuma duplicata encontrada!")
            return

        total_to_remove = 0

        for duplicate in duplicates:
            title = duplicate['title']
            count = duplicate['count']

            embeddings = Embedding.objects.filter(
                origin='business_brain',
                title=title
            ).order_by('created_at')

            first = embeddings.first()
            to_remove = count - 1
            total_to_remove += to_remove

            logger.info(f"📋 '{title}': {count} total | Manter: {first.created_at} | Remover: {to_remove}")

        logger.info(f"\n📊 RESUMO PREVIEW:")
        logger.info(f"🗑️  Seriam removidos: {total_to_remove} embeddings duplicados")
        logger.info(f"✅ Seriam mantidos: {duplicates.count()} embeddings únicos")


def main():
    """Função principal com opção de preview"""
    import argparse

    parser = argparse.ArgumentParser(description='Remove duplicatas de embeddings business_brain')
    parser.add_argument('--preview', action='store_true',
                       help='Apenas mostra o que seria removido, sem executar')

    args = parser.parse_args()

    remover = DuplicatesRemover()

    if args.preview:
        remover.preview_duplicates()
    else:
        # Execução automática para crontab - sem confirmação interativa
        logger.info("🤖 Executando remoção automática de duplicatas via crontab")
        remover.run()


if __name__ == "__main__":
    main()