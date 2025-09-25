from rest_framework import serializers
from .models import KnowledgeBase, EnhancedEmbedding, Embedding
from core.serializers import BaseEnhancedSerializer, UserSerializer
from core.validators import validate_embedding_vector, validate_metadata_structure


class KnowledgeBaseSerializer(BaseEnhancedSerializer):
    owner = UserSerializer(read_only=True)

    class Meta:
        model = KnowledgeBase
        fields = [
            'id', 'name', 'description', 'owner', 'embedding_model',
            'dimension', 'is_public', 'is_active', 'total_embeddings',
            'total_tokens', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'owner', 'total_embeddings', 'total_tokens',
            'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['owner'] = request.user
        return super().create(validated_data)


class EnhancedEmbeddingSerializer(BaseEnhancedSerializer):
    knowledge_base = KnowledgeBaseSerializer(read_only=True)

    class Meta:
        model = EnhancedEmbedding
        fields = [
            'id', 'title', 'content', 'content_hash', 'embedding_vector',
            'model_name', 'token_count', 'knowledge_base', 'campaign',
            'source_type', 'source_url', 'quality_score', 'language',
            'topics', 'keywords', 'is_processed', 'processing_error',
            'metadata', 'similarity_search_count', 'last_accessed',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'content_hash', 'knowledge_base', 'similarity_search_count',
            'last_accessed', 'created_at', 'updated_at'
        ]

    def validate_embedding_vector(self, value):
        validate_embedding_vector(value)
        return value

    def validate_metadata(self, value):
        validate_metadata_structure(value)
        return value


class EmbeddingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Embedding
        fields = [
            'id', 'origin', 'content', 'title', 'embedding_vector',
            'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']