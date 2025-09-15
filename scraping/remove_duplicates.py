#!/usr/bin/env python3
"""
Remove Duplicates - Remove embeddings duplicados da origem webscraping
baseado no campo content
"""

import os
import sys
import logging
from typing import List, Dict, Any, Set
from datetime import datetime
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
from django.db.models import Q

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent / 'remove_duplicates.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DuplicateRemover:
    """Classe para remover embeddings duplicados de origem webscraping"""

    def __init__(self):
        self.processed_count = 0
        self.duplicates_removed = 0
        self.content_groups = defaultdict(list)

    def get_webscraping_embeddings(self) -> List[Embedding]:
        """Obtém todos os embeddings de origem webscraping"""
        try:
            embeddings = Embedding.objects.filter(origin='webscraping').order_by('created_at')
            logger.info(f"Encontrados {embeddings.count()} embeddings de webscraping")
            return list(embeddings)
        except Exception as e:
            logger.error(f"Erro ao consultar embeddings: {e}")
            return []

    def group_by_content(self, embeddings: List[Embedding]) -> Dict[str, List[Embedding]]:
        """Agrupa embeddings pelo conteúdo"""
        content_groups = defaultdict(list)

        for embedding in embeddings:
            content_key = embedding.content.strip()
            content_groups[content_key].append(embedding)

        logger.info(f"Agrupados em {len(content_groups)} grupos de conteúdo único")
        return content_groups

    def find_duplicates(self, embeddings: List[Embedding]) -> Dict[str, List[Embedding]]:
        """Identifica grupos de embeddings com conteúdo duplicado"""
        content_groups = self.group_by_content(embeddings)

        duplicates = {}
        for content, group in content_groups.items():
            if len(group) > 1:
                duplicates[content] = group

        logger.info(f"Encontrados {len(duplicates)} grupos com duplicatas")
        return duplicates

    def select_embedding_to_keep(self, duplicates: List[Embedding]) -> Embedding:
        """Seleciona qual embedding manter entre as duplicatas"""
        # Ordena por data de criação (mantém o mais antigo)
        sorted_embeddings = sorted(duplicates, key=lambda x: x.created_at)
        return sorted_embeddings[0]

    def remove_duplicates_dry_run(self, embeddings: List[Embedding]) -> Dict[str, Any]:
        """Executa uma simulação da remoção de duplicatas"""
        duplicates = self.find_duplicates(embeddings)

        stats = {
            'total_embeddings': len(embeddings),
            'duplicate_groups': len(duplicates),
            'embeddings_to_remove': 0,
            'embeddings_to_keep': len(duplicates),
            'details': []
        }

        for content, duplicate_group in duplicates.items():
            to_keep = self.select_embedding_to_keep(duplicate_group)
            to_remove = [emb for emb in duplicate_group if emb.id != to_keep.id]

            stats['embeddings_to_remove'] += len(to_remove)

            group_info = {
                'content_preview': content[:100] + '...' if len(content) > 100 else content,
                'total_duplicates': len(duplicate_group),
                'to_keep': {
                    'id': str(to_keep.id),
                    'title': to_keep.title,
                    'created_at': to_keep.created_at.isoformat()
                },
                'to_remove': [
                    {
                        'id': str(emb.id),
                        'title': emb.title,
                        'created_at': emb.created_at.isoformat()
                    }
                    for emb in to_remove
                ]
            }
            stats['details'].append(group_info)

        return stats

    def remove_duplicates(self, embeddings: List[Embedding], confirm: bool = False) -> Dict[str, Any]:
        """Remove embeddings duplicados"""
        if not confirm:
            logger.warning("Executando dry run - nenhuma exclusão será realizada")
            return self.remove_duplicates_dry_run(embeddings)

        duplicates = self.find_duplicates(embeddings)
        removed_ids = []
        kept_ids = []

        for content, duplicate_group in duplicates.items():
            to_keep = self.select_embedding_to_keep(duplicate_group)
            to_remove = [emb for emb in duplicate_group if emb.id != to_keep.id]

            kept_ids.append(str(to_keep.id))

            # Remove duplicatas
            for embedding in to_remove:
                try:
                    embedding_id = str(embedding.id)
                    embedding.delete()
                    removed_ids.append(embedding_id)
                    self.duplicates_removed += 1
                    logger.info(f"Removido embedding duplicado: {embedding_id}")
                except Exception as e:
                    logger.error(f"Erro ao remover embedding {embedding.id}: {e}")

        stats = {
            'total_embeddings': len(embeddings),
            'duplicate_groups': len(duplicates),
            'embeddings_removed': len(removed_ids),
            'embeddings_kept': len(kept_ids),
            'removed_ids': removed_ids,
            'kept_ids': kept_ids
        }

        logger.info(f"Remoção concluída: {len(removed_ids)} embeddings removidos")
        return stats

    def generate_report(self, stats: Dict[str, Any]) -> str:
        """Gera relatório detalhado da operação"""
        report = []
        report.append("=" * 60)
        report.append("RELATÓRIO DE REMOÇÃO DE DUPLICATAS")
        report.append("=" * 60)
        report.append(f"Data/Hora: {datetime.now().isoformat()}")
        report.append(f"Total de embeddings analisados: {stats['total_embeddings']}")
        report.append(f"Grupos com duplicatas encontrados: {stats['duplicate_groups']}")

        if 'embeddings_removed' in stats:
            report.append(f"Embeddings removidos: {stats['embeddings_removed']}")
            report.append(f"Embeddings mantidos: {stats['embeddings_kept']}")
        else:
            report.append(f"Embeddings que seriam removidos: {stats['embeddings_to_remove']}")
            report.append(f"Embeddings que seriam mantidos: {stats['embeddings_to_keep']}")

        if stats.get('details'):
            report.append("\n" + "=" * 40)
            report.append("DETALHES DOS GRUPOS DUPLICADOS")
            report.append("=" * 40)

            for i, detail in enumerate(stats['details'][:10]):  # Limita a 10 grupos no relatório
                report.append(f"\nGrupo {i+1}:")
                report.append(f"  Conteúdo: {detail['content_preview']}")
                report.append(f"  Total de duplicatas: {detail['total_duplicates']}")
                report.append(f"  Mantido: {detail['to_keep']['title']} ({detail['to_keep']['id']})")
                report.append(f"  Removidos: {len(detail['to_remove'])} embeddings")

        report.append("\n" + "=" * 60)
        return "\n".join(report)

    def save_report(self, stats: Dict[str, Any], filename: str = None):
        """Salva relatório em arquivo"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"duplicate_removal_report_{timestamp}.txt"

        report_path = Path(__file__).parent / filename
        report_content = self.generate_report(stats)

        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"Relatório salvo em: {report_path}")
        except Exception as e:
            logger.error(f"Erro ao salvar relatório: {e}")

    def run(self, confirm_removal: bool = False):
        """Executa o processo completo de remoção de duplicatas"""
        logger.info("Iniciando processo de remoção de duplicatas...")

        try:
            # Obtém embeddings de webscraping
            embeddings = self.get_webscraping_embeddings()

            if not embeddings:
                logger.info("Nenhum embedding de webscraping encontrado")
                return

            # Remove duplicatas
            stats = self.remove_duplicates(embeddings, confirm=confirm_removal)

            # Salva relatório
            self.save_report(stats)

            # Exibe resumo
            if confirm_removal:
                logger.info(f"Processo concluído: {stats['embeddings_removed']} duplicatas removidas")
            else:
                logger.info(f"Dry run concluído: {stats['embeddings_to_remove']} duplicatas seriam removidas")
                logger.info("Execute com --confirm para realizar a remoção")

        except Exception as e:
            logger.error(f"Erro durante execução: {e}")


def main():
    """Função principal"""
    import argparse

    parser = argparse.ArgumentParser(description='Remove embeddings duplicados de webscraping')
    parser.add_argument('--confirm', action='store_true',
                       help='Confirma a remoção (sem este flag, executa apenas dry run)')
    parser.add_argument('--verbose', action='store_true',
                       help='Ativa logs verbosos')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    remover = DuplicateRemover()

    # Para execução via crontab, sempre confirma a remoção automaticamente
    # Se não há argumentos (execução direta), assume confirmação
    if len(sys.argv) == 1:
        logger.info("🤖 Executando remoção automática de duplicatas via crontab")
        remover.run(confirm_removal=True)
    else:
        remover.run(confirm_removal=args.confirm)


if __name__ == "__main__":
    main()