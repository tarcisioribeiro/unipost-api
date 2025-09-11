#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from texts.models import Text
from embeddings.models import Embedding

def create_members_group():
    """
    Cria o grupo 'members' com permissões para Text e Embedding models
    """
    # Criar ou obter o grupo 'members'
    group, created = Group.objects.get_or_create(name='members')
    
    if created:
        print("Grupo 'members' criado com sucesso!")
    else:
        print("Grupo 'members' já existe.")
    
    # Obter ContentTypes dos modelos
    text_content_type = ContentType.objects.get_for_model(Text)
    embedding_content_type = ContentType.objects.get_for_model(Embedding)
    
    # Definir permissões necessárias (add, change, view)
    permissions_to_add = [
        # Permissões para Text
        Permission.objects.get(content_type=text_content_type, codename='add_text'),
        Permission.objects.get(content_type=text_content_type, codename='change_text'),
        Permission.objects.get(content_type=text_content_type, codename='view_text'),
        
        # Permissões para Embedding
        Permission.objects.get(content_type=embedding_content_type, codename='add_embedding'),
        Permission.objects.get(content_type=embedding_content_type, codename='change_embedding'),
        Permission.objects.get(content_type=embedding_content_type, codename='view_embedding'),
    ]
    
    # Adicionar permissões ao grupo
    for permission in permissions_to_add:
        group.permissions.add(permission)
        print(f"Permissão '{permission.name}' adicionada ao grupo 'members'")
    
    print(f"Grupo 'members' configurado com {len(permissions_to_add)} permissões!")

if __name__ == '__main__':
    create_members_group()