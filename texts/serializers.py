from rest_framework import serializers
from .models import ContentPiece, Text
from core.serializers import BaseEnhancedSerializer, UserSerializer
from core.validators import validate_content_length, validate_tags_list
from core.models import Campaign


class ContentPieceSerializer(BaseEnhancedSerializer):
    creator = UserSerializer(read_only=True)
    campaign = serializers.PrimaryKeyRelatedField(
        queryset=Campaign.objects.all(),
        allow_null=True,
        required=False
    )

    class Meta:
        model = ContentPiece
        fields = [
            'id', 'title', 'content', 'content_type', 'target_platforms',
            'status', 'creator', 'campaign', 'tags', 'metadata',
            'is_published', 'published_at', 'scheduled_for',
            'view_count', 'engagement_score', 'performance_metrics',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'creator', 'view_count', 'engagement_score',
            'is_published', 'published_at', 'created_at', 'updated_at'
        ]

    def validate_content(self, value):
        validate_content_length(value)
        return value

    def validate_tags(self, value):
        validate_tags_list(value)
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['creator'] = request.user
        return super().create(validated_data)


class TextSerializer(serializers.ModelSerializer):
    class Meta:
        model = Text
        fields = [
            'id', 'theme', 'platform', 'content', 'is_approved',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']