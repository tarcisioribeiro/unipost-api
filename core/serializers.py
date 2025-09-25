"""
Enhanced serializers with security, validation, and standardized responses
"""
import hashlib
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import (
    UserProfile, Campaign, SourceSite, APIAuditLog, SystemMetrics
)
from .validators import (
    validate_content_length, validate_tags_list, validate_url_list,
    validate_css_selectors, validate_metadata_structure
)


class UserSerializer(serializers.ModelSerializer):
    """Secure user serializer with minimal exposed data"""

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']

    def to_representation(self, instance):
        """Remove sensitive information for non-owners"""
        data = super().to_representation(instance)
        request = self.context.get('request')

        # Only show email to the user themselves or staff
        if request and hasattr(request, 'user'):
            if request.user != instance and not request.user.is_staff:
                data.pop('email', None)

        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """Enhanced user profile serializer with quota management"""

    user = UserSerializer(read_only=True)
    api_usage_percentage = serializers.SerializerMethodField()
    can_make_api_call = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = [
            'user', 'company', 'job_title', 'phone_number',
            'api_quota', 'api_usage_current_month', 'quota_reset_date',
            'plan_type', 'is_premium', 'timezone', 'language',
            'email_notifications', 'preferences',
            'total_content_created', 'total_images_generated', 'total_embeddings_created',
            'api_usage_percentage', 'can_make_api_call',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'user', 'api_usage_current_month', 'quota_reset_date',
            'total_content_created', 'total_images_generated', 'total_embeddings_created',
            'created_at', 'updated_at'
        ]

    def get_api_usage_percentage(self, obj):
        return obj.get_api_usage_percentage()

    def get_can_make_api_call(self, obj):
        return obj.can_make_api_call()

    def validate_preferences(self, value):
        """Validate preferences JSON structure"""
        validate_metadata_structure(value)
        return value


class CampaignSerializer(serializers.ModelSerializer):
    """Enhanced campaign serializer with metrics"""

    owner = UserSerializer(read_only=True)
    content_count = serializers.SerializerMethodField()
    published_content_count = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = [
            'id', 'name', 'description', 'owner', 'status',
            'target_platforms', 'target_audience', 'budget',
            'start_date', 'end_date', 'goals', 'tags',
            'is_active', 'is_public',
            'content_count', 'published_content_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']

    def get_content_count(self, obj):
        return obj.get_content_count()

    def get_published_content_count(self, obj):
        return obj.get_published_content_count()

    def validate_target_platforms(self, value):
        """Validate platform choices"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Target platforms must be a list.")

        valid_platforms = ['facebook', 'instagram', 'twitter', 'linkedin', 'youtube', 'tiktok', 'wordpress', 'email', 'other']
        for platform in value:
            if platform not in valid_platforms:
                raise serializers.ValidationError(f"Invalid platform: {platform}")

        return value

    def validate_tags(self, value):
        """Validate tags structure"""
        validate_tags_list(value)
        return value

    def validate_goals(self, value):
        """Validate goals JSON structure"""
        validate_metadata_structure(value)
        return value

    def validate(self, data):
        """Cross-field validation"""
        if data.get('end_date') and data.get('start_date'):
            if data['end_date'] <= data['start_date']:
                raise serializers.ValidationError("End date must be after start date.")

        return data


class SourceSiteSerializer(serializers.ModelSerializer):
    """Enhanced source site serializer with monitoring metrics"""

    owner = UserSerializer(read_only=True)
    success_rate = serializers.SerializerMethodField()

    class Meta:
        model = SourceSite
        fields = [
            'id', 'name', 'url', 'description', 'category', 'owner',
            'is_public', 'is_active', 'monitor_frequency',
            'last_checked', 'next_check', 'content_selectors',
            'exclude_patterns', 'custom_headers',
            'min_content_length', 'language',
            'total_posts_discovered', 'successful_extractions', 'failed_extractions',
            'last_error', 'error_count', 'auto_create_campaigns',
            'success_rate', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'owner', 'last_checked', 'next_check',
            'total_posts_discovered', 'successful_extractions', 'failed_extractions',
            'last_error', 'error_count', 'created_at', 'updated_at'
        ]

    def get_success_rate(self, obj):
        return obj.get_success_rate()

    def validate_content_selectors(self, value):
        """Validate CSS selectors structure"""
        validate_css_selectors(value)
        return value

    def validate_exclude_patterns(self, value):
        """Validate exclude patterns list"""
        validate_url_list(value)
        return value

    def validate_custom_headers(self, value):
        """Validate custom headers structure"""
        validate_metadata_structure(value)
        return value

    def validate_monitor_frequency(self, value):
        """Ensure reasonable monitoring frequency"""
        if value < 300:  # 5 minutes minimum
            raise serializers.ValidationError("Monitor frequency must be at least 5 minutes (300 seconds).")
        if value > 86400:  # 24 hours maximum
            raise serializers.ValidationError("Monitor frequency cannot exceed 24 hours (86400 seconds).")
        return value


class APIAuditLogSerializer(serializers.ModelSerializer):
    """Read-only serializer for API audit logs"""

    user = UserSerializer(read_only=True)

    class Meta:
        model = APIAuditLog
        fields = [
            'id', 'user', 'session_id', 'method', 'endpoint', 'full_url',
            'ip_address', 'user_agent', 'referer', 'request_headers',
            'response_status', 'response_size', 'response_time_ms',
            'db_queries_count', 'db_time_ms', 'resource_type', 'resource_id',
            'is_suspicious', 'risk_score', 'api_version', 'rate_limit_hit',
            'error_message', 'additional_data', 'timestamp'
        ]
        read_only_fields = '__all__'

    def to_representation(self, instance):
        """Filter sensitive data based on user permissions"""
        data = super().to_representation(instance)
        request = self.context.get('request')

        if request and hasattr(request, 'user'):
            # Non-staff users can only see their own logs and limited fields
            if not request.user.is_staff:
                if instance.user != request.user:
                    return {}  # Hide logs from other users

                # Remove sensitive fields for regular users
                sensitive_fields = ['request_headers', 'ip_address', 'session_id', 'additional_data']
                for field in sensitive_fields:
                    data.pop(field, None)

        return data


class SystemMetricsSerializer(serializers.ModelSerializer):
    """Read-only serializer for system metrics (admin only)"""

    class Meta:
        model = SystemMetrics
        fields = [
            'total_api_calls_today', 'successful_api_calls_today', 'failed_api_calls_today',
            'avg_response_time_ms', 'total_content_pieces', 'total_published_content',
            'total_campaigns', 'total_embeddings_created', 'total_images_generated',
            'ai_processing_cost_today', 'active_users_today', 'new_users_today',
            'premium_users', 'system_status', 'metrics_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = '__all__'


class ContentHashMixin:
    """Mixin to add content hashing functionality"""

    def create_content_hash(self, content):
        """Create SHA-256 hash of content for deduplication"""
        if isinstance(content, str):
            content = content.encode('utf-8')
        return hashlib.sha256(content).hexdigest()


class TimestampMixin:
    """Mixin to add timestamp utilities"""

    def get_current_timestamp(self):
        return timezone.now()


class BaseEnhancedSerializer(serializers.ModelSerializer, ContentHashMixin, TimestampMixin):
    """Base serializer with common enhancements"""

    def validate(self, data):
        """Base validation with common checks"""
        # Add content hash if content field exists
        if 'content' in data and hasattr(self.Meta.model, 'content_hash'):
            data['content_hash'] = self.create_content_hash(data['content'])

        return super().validate(data)

    def to_representation(self, instance):
        """Enhanced representation with computed fields"""
        data = super().to_representation(instance)

        # Add computed fields
        if hasattr(instance, 'get_word_count'):
            data['word_count'] = instance.get_word_count()

        if hasattr(instance, 'get_processing_duration'):
            duration = instance.get_processing_duration()
            if duration:
                data['processing_duration_seconds'] = duration

        return data


# Generic response serializers for standardized API responses
class SuccessResponseSerializer(serializers.Serializer):
    """Standard success response format"""
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    data = serializers.JSONField()
    meta = serializers.JSONField(required=False)
    timestamp = serializers.DateTimeField(default=timezone.now)


class ErrorResponseSerializer(serializers.Serializer):
    """Standard error response format"""
    success = serializers.BooleanField(default=False)
    error = serializers.CharField()
    details = serializers.JSONField(required=False)
    error_code = serializers.CharField(required=False)
    timestamp = serializers.DateTimeField(default=timezone.now)


class PaginatedResponseSerializer(serializers.Serializer):
    """Standard paginated response format"""
    success = serializers.BooleanField(default=True)
    data = serializers.JSONField()
    pagination = serializers.JSONField()
    meta = serializers.JSONField(required=False)
    timestamp = serializers.DateTimeField(default=timezone.now)


class ValidationErrorSerializer(serializers.Serializer):
    """Standard validation error response format"""
    success = serializers.BooleanField(default=False)
    error = serializers.CharField(default="Validation Error")
    validation_errors = serializers.JSONField()
    timestamp = serializers.DateTimeField(default=timezone.now)