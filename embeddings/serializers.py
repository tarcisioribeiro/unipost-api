from rest_framework import serializers
from embeddings.models import Embedding


class EmbeddingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Embedding
        fields = [
            'id',
            'origin',
            'content',
            'title',
            'embedding_vector',
            'metadata',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
