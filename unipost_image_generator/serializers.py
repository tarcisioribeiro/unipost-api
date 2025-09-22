from rest_framework import serializers
from .models import GeneratedImage


class GeneratedImageSerializer(serializers.ModelSerializer):
    """Serializer para imagens geradas"""

    class Meta:
        model = GeneratedImage
        fields = [
            'id',
            'embedding',
            'original_text',
            'generated_prompt',
            'image_path',
            'dalle_response',
            'generation_metadata',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ImageGenerationRequestSerializer(serializers.Serializer):
    """Serializer para requisições de geração de imagem"""

    text = serializers.CharField(
        max_length=5000,
        help_text="Texto do post para gerar imagem"
    )
    embedding_id = serializers.UUIDField(
        help_text="ID do embedding relacionado"
    )
    custom_prompt = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
        help_text="Prompt customizado (opcional)"
    )
