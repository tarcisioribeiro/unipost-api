from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from texts.models import Text
from embeddings.models import Embedding
from sites.models import Site


class Command(BaseCommand):
    help = 'Cria o grupo members com permissões para Text, Embedding e Site models'

    def handle(self, *args, **options):
        """
        Cria o grupo 'members' com permissões para Text, Embedding e Site models
        """
        # Criar ou obter o grupo 'members'
        group, created = Group.objects.get_or_create(name='members')
        
        if created:
            self.stdout.write(
                self.style.SUCCESS("Grupo 'members' criado com sucesso!")
            )
        else:
            self.stdout.write(
                self.style.WARNING("Grupo 'members' já existe.")
            )
        
        # Obter ContentTypes dos modelos
        text_content_type = ContentType.objects.get_for_model(Text)
        embedding_content_type = ContentType.objects.get_for_model(Embedding)
        site_content_type = ContentType.objects.get_for_model(Site)
        
        # Definir permissões necessárias (add, change, view)
        permissions_to_add = [
            # Permissões para Text
            Permission.objects.get(content_type=text_content_type, codename='add_text'),
            Permission.objects.get(content_type=text_content_type, codename='change_text'),
            Permission.objects.get(content_type=text_content_type, codename='view_text'),

            # Permissões para Sites
            Permission.objects.get(content_type=site_content_type, codename='add_site'),
            Permission.objects.get(content_type=site_content_type, codename='change_site'),
            Permission.objects.get(content_type=site_content_type, codename='view_site'),

            # Permissões para Embedding
            Permission.objects.get(content_type=embedding_content_type, codename='add_embedding'),
            Permission.objects.get(content_type=embedding_content_type, codename='change_embedding'),
            Permission.objects.get(content_type=embedding_content_type, codename='view_embedding'),
        ]
        
        # Adicionar permissões ao grupo
        for permission in permissions_to_add:
            group.permissions.add(permission)
            self.stdout.write(
                f"Permissão '{permission.name}' adicionada ao grupo 'members'"
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Grupo 'members' configurado com {len(permissions_to_add)} permissões!"
            )
        )