from rest_framework import serializers
from .models import AIImageRequest, EnhancedGeneratedImage, GeneratedImage
from core.serializers import BaseEnhancedSerializer, UserSerializer, CampaignSerializer
from core.validators import validate_prompt_content, validate_metadata_structure


class AIImageRequestSerializer(BaseEnhancedSerializer):
    requester = UserSerializer(read_only=True)
    campaign = CampaignSerializer(read_only=True)

    class Meta:
        model = AIImageRequest
        fields = [
            'id', 'requester', 'campaign', 'original_text', 'ai_prompt',
            'user_prompt_modifications', 'final_prompt', 'model_name',
            'image_size', 'style', 'quality', 'status',
            'processing_started_at', 'processing_completed_at',
            'estimated_cost', 'actual_cost', 'error_message', 'retry_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'requester', 'status', 'processing_started_at',
            'processing_completed_at', 'actual_cost', 'error_message',
            'retry_count', 'created_at', 'updated_at'
        ]

    def validate_ai_prompt(self, value):
        validate_prompt_content(value)
        return value

    def validate_final_prompt(self, value):
        validate_prompt_content(value)
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['requester'] = request.user
        return super().create(validated_data)


class EnhancedGeneratedImageSerializer(BaseEnhancedSerializer):
    image_request = AIImageRequestSerializer(read_only=True)

    class Meta:
        model = EnhancedGeneratedImage
        fields = [
            'id', 'image_request', 'image_path', 'original_url', 'file_size',
            'file_format', 'width', 'height', 'aspect_ratio', 'api_response',
            'revised_prompt', 'quality_score', 'content_analysis',
            'download_count', 'last_accessed', 'is_approved',
            'approved_by', 'approved_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'image_request', 'download_count', 'last_accessed',
            'created_at', 'updated_at'
        ]

    def validate_api_response(self, value):
        validate_metadata_structure(value)
        return value


class GeneratedImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedImage
        fields = [
            'id', 'embedding', 'original_text', 'generated_prompt',
            'image_path', 'dalle_response', 'generation_metadata',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']