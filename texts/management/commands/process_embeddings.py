"""
Comando Django para processar embeddings pendentes
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from texts.models import Text
from embeddings.models import Embedding
from texts.signals import process_embedding_creation
import time


class Command(BaseCommand):
    help = 'Processa embeddings pendentes para textos aprovados sem embedding'

    def add_arguments(self, parser):
        parser.add_argument(
            '--text-id',
            type=int,
            help='Processa apenas um texto específico pelo ID',
        )
        parser.add_argument(
            '--force-update',
            action='store_true',
            help='Força atualização de embeddings existentes',
        )

    def handle(self, *args, **options):
        text_id = options.get('text_id')
        force_update = options.get('force_update', False)

        if text_id:
            self.process_single_text(text_id, force_update)
        else:
            self.process_batch(force_update)

    def process_single_text(self, text_id, force_update=False):
        """Processa um único texto"""
        try:
            text = Text.objects.get(id=text_id)
            
            if not text.is_approved:
                self.stdout.write(
                    self.style.WARNING(f'Texto {text_id} não está aprovado')
                )
                return

            existing = Embedding.objects.filter(
                origin='generated',
                metadata__text_id=text.id
            ).first()

            if existing and not force_update:
                self.stdout.write(
                    self.style.WARNING(f'Embedding já existe para texto {text_id}')
                )
                return

            self.stdout.write(f'Processando texto {text_id}...')
            
            success = process_embedding_creation(text)
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Embedding processado para texto {text_id}')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'✗ Falha ao processar texto {text_id}')
                )

        except Text.DoesNotExist:
            raise CommandError(f'Texto {text_id} não encontrado')

    def process_batch(self, force_update=False):
        """Processa textos em lote"""
        approved_texts = Text.objects.filter(is_approved=True)

        if not force_update:
            texts_with_embeddings = Embedding.objects.filter(
                origin='generated',
                metadata__text_id__isnull=False
            ).values_list('metadata__text_id', flat=True)
            
            approved_texts = approved_texts.exclude(id__in=texts_with_embeddings)

        total = approved_texts.count()
        self.stdout.write(f'Encontrados {total} textos para processar')
        
        for i, text in enumerate(approved_texts, 1):
            self.stdout.write(f'[{i}/{total}] Texto {text.id}...')
            success = process_embedding_creation(text)
            
            if success:
                self.stdout.write(self.style.SUCCESS('✓ Sucesso'))
            else:
                self.stdout.write(self.style.ERROR('✗ Falha'))
            
            time.sleep(0.5)  # Pequeno delay para evitar rate limit
