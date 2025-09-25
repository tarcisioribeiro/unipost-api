from rest_framework import serializers
from .models import ScrapedPost, Site
from core.serializers import BaseEnhancedSerializer, UserSerializer, SourceSiteSerializer
from core.validators import validate_content_length, validate_url_list


class ScrapedPostSerializer(BaseEnhancedSerializer):
    source_site = SourceSiteSerializer(read_only=True)
    processed_by = UserSerializer(read_only=True)

    class Meta:
        model = ScrapedPost
        fields = [
            'id', 'title', 'url', 'content', 'summary', 'keywords', 'language',
            'source_site', 'processed_by', 'status', 'processing_started_at',
            'processing_completed_at', 'word_count', 'reading_time_minutes',
            'quality_score', 'featured_image_url', 'images', 'author',
            'published_date', 'scraped_at', 'ai_analysis', 'content_themes',
            'sentiment_score', 'error_message', 'retry_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'source_site', 'processed_by', 'scraped_at',
            'created_at', 'updated_at'
        ]

    def validate_content(self, value):
        validate_content_length(value)
        return value

    def validate_images(self, value):
        validate_url_list(value)
        return value


class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = [
            'id', 'name', 'url', 'category', 'monitored', 'enable_recursive_crawling',
            'max_depth', 'max_pages', 'allow_patterns', 'deny_patterns',
            'content_selectors', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']