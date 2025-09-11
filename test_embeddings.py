#!/usr/bin/env python3
"""
Teste simples para validar importação do modelo Embedding
"""

import os
import sys
import django

# Configuração do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
django.setup()

from embeddings.models import Embedding

def test_embedding_model():
    """Testa se o modelo Embedding está funcionando"""
    try:
        # Conta embeddings existentes
        count = Embedding.objects.count()
        print(f"✅ Modelo Embedding funcionando! Total de embeddings: {count}")
        
        # Tenta criar um embedding de teste
        test_embedding = Embedding.objects.create(
            origin='test',
            content='Teste de conteúdo',
            title='Teste',
            embedding_vector=[0.1, 0.2, 0.3],
            metadata={'test': True}
        )
        print(f"✅ Embedding de teste criado com ID: {test_embedding.id}")
        
        # Remove o embedding de teste
        test_embedding.delete()
        print("✅ Embedding de teste removido com sucesso")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao testar modelo Embedding: {e}")
        return False

if __name__ == "__main__":
    test_embedding_model()