import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal


# Choices for various fields
CONTENT_TYPE_CHOICES = [
    ('post', 'Blog Post'),
    ('social', 'Social Media Post'),
    ('email', 'Email Content'),
    ('ad', 'Advertisement'),
    ('video_script', 'Video Script'),
    ('other', 'Other'),
]

CONTENT_STATUS_CHOICES = [
    ('draft', 'Draft'),
    ('review', 'Under Review'),
    ('approved', 'Approved'),
    ('scheduled', 'Scheduled'),
    ('published', 'Published'),
    ('archived', 'Archived'),
]

POST_STATUS_CHOICES = [
    ('discovered', 'Discovered'),
    ('processing', 'Processing'),
    ('processed', 'Processed'),
    ('failed', 'Failed'),
    ('archived', 'Archived'),
]

PLATFORM_CHOICES = [
    ('facebook', 'Facebook'),
    ('instagram', 'Instagram'),
    ('twitter', 'Twitter/X'),
    ('linkedin', 'LinkedIn'),
    ('youtube', 'YouTube'),
    ('tiktok', 'TikTok'),
    ('wordpress', 'WordPress'),
    ('email', 'Email'),
    ('other', 'Other'),
]

CAMPAIGN_STATUS_CHOICES = [
    ('planning', 'Planning'),
    ('active', 'Active'),
    ('paused', 'Paused'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]

SITE_CATEGORY_CHOICES = [
    ('blog', 'Blog'),
    ('news', 'News'),
    ('ecommerce', 'E-commerce'),
    ('corporate', 'Corporate'),
    ('education', 'Education'),
    ('technology', 'Technology'),
    ('marketing', 'Marketing'),
    ('other', 'Other'),
]


class TimeStampedModel(models.Model):
    """Abstract base model with timestamp fields"""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        abstract = True


class UserProfile(TimeStampedModel):
    """Extended user profile with API quotas and preferences"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name="User"
    )

    # Profile Information
    company = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Company"
    )
    job_title = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Job Title"
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Phone Number"
    )

    # API Usage & Quotas
    api_quota = models.PositiveIntegerField(
        default=1000,
        validators=[MinValueValidator(0)],
        verbose_name="API Quota per Month",
        help_text="Maximum API calls per month"
    )
    api_usage_current_month = models.PositiveIntegerField(
        default=0,
        verbose_name="Current Month Usage"
    )
    quota_reset_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="Quota Reset Date"
    )

    # Plan & Billing
    plan_type = models.CharField(
        max_length=20,
        choices=[
            ('free', 'Free'),
            ('basic', 'Basic'),
            ('premium', 'Premium'),
            ('enterprise', 'Enterprise'),
        ],
        default='free',
        verbose_name="Plan Type"
    )
    is_premium = models.BooleanField(
        default=False,
        verbose_name="Premium User"
    )

    # Preferences
    timezone = models.CharField(
        max_length=50,
        default='America/Sao_Paulo',
        verbose_name="Timezone"
    )
    language = models.CharField(
        max_length=10,
        default='pt-BR',
        verbose_name="Language"
    )
    email_notifications = models.BooleanField(
        default=True,
        verbose_name="Email Notifications"
    )

    # Settings
    preferences = models.JSONField(
        default=dict,
        verbose_name="User Preferences",
        help_text="JSON field for user-specific settings"
    )

    # Stats
    total_content_created = models.PositiveIntegerField(default=0)
    total_images_generated = models.PositiveIntegerField(default=0)
    total_embeddings_created = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} Profile"

    def get_api_usage_percentage(self):
        """Calculate API usage percentage"""
        if self.api_quota == 0:
            return 0
        return round((self.api_usage_current_month / self.api_quota) * 100, 2)

    def can_make_api_call(self):
        """Check if user can make another API call"""
        return self.api_usage_current_month < self.api_quota

    def increment_api_usage(self):
        """Increment API usage counter"""
        self.api_usage_current_month += 1
        self.save(update_fields=['api_usage_current_month'])


class Campaign(TimeStampedModel):
    """Marketing campaigns to group content pieces"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Basic Information
    name = models.CharField(
        max_length=200,
        verbose_name="Campaign Name"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )

    # Ownership
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='campaigns',
        verbose_name="Campaign Owner"
    )

    # Campaign Details
    status = models.CharField(
        max_length=20,
        choices=CAMPAIGN_STATUS_CHOICES,
        default='planning',
        verbose_name="Status"
    )

    target_platforms = models.JSONField(
        default=list,
        verbose_name="Target Platforms",
        help_text="List of platforms for this campaign"
    )

    target_audience = models.TextField(
        blank=True,
        verbose_name="Target Audience",
        help_text="Description of target audience"
    )

    # Budget & Timeline
    budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Budget"
    )

    start_date = models.DateTimeField(
        verbose_name="Start Date"
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="End Date"
    )

    # Goals & KPIs
    goals = models.JSONField(
        default=dict,
        verbose_name="Campaign Goals",
        help_text="JSON field for campaign objectives and KPIs"
    )

    # Tags & Categories
    tags = models.JSONField(
        default=list,
        verbose_name="Tags"
    )

    # Settings
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active"
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name="Public Campaign",
        help_text="Allow other users to view this campaign"
    )

    class Meta:
        verbose_name = "Campaign"
        verbose_name_plural = "Campaigns"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['start_date', 'end_date']),
        ]

    def __str__(self):
        return f"{self.name} ({self.owner.username})"

    def get_content_count(self):
        """Get total content pieces in this campaign"""
        return self.content_pieces.count()

    def get_published_content_count(self):
        """Get published content pieces count"""
        return self.content_pieces.filter(status='published').count()


class SourceSite(TimeStampedModel):
    """Enhanced model for sites to be monitored and scraped"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Basic Information
    name = models.CharField(
        max_length=200,
        verbose_name="Site Name"
    )
    url = models.URLField(
        unique=True,
        verbose_name="Site URL"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )

    # Categorization
    category = models.CharField(
        max_length=50,
        choices=SITE_CATEGORY_CHOICES,
        verbose_name="Category"
    )

    # Ownership & Access Control
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='owned_sites',
        verbose_name="Owner"
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name="Public Site",
        help_text="Allow other users to use this site for scraping"
    )

    # Monitoring Settings
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active"
    )
    monitor_frequency = models.PositiveIntegerField(
        default=3600,  # 1 hour in seconds
        validators=[MinValueValidator(300)],  # Min 5 minutes
        verbose_name="Check Frequency (seconds)",
        help_text="How often to check for new content"
    )
    last_checked = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Last Checked"
    )
    next_check = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Next Check"
    )

    # Scraping Configuration
    content_selectors = models.JSONField(
        default=dict,
        verbose_name="Content Selectors",
        help_text="CSS selectors for extracting specific content"
    )
    exclude_patterns = models.JSONField(
        default=list,
        verbose_name="Exclude Patterns",
        help_text="URL patterns to exclude from scraping"
    )
    custom_headers = models.JSONField(
        default=dict,
        verbose_name="Custom Headers",
        help_text="Additional HTTP headers for requests"
    )

    # Quality & Filtering
    min_content_length = models.PositiveIntegerField(
        default=200,
        verbose_name="Minimum Content Length"
    )
    language = models.CharField(
        max_length=10,
        default='pt-BR',
        verbose_name="Expected Language"
    )

    # Performance Stats
    total_posts_discovered = models.PositiveIntegerField(
        default=0,
        verbose_name="Total Posts Discovered"
    )
    successful_extractions = models.PositiveIntegerField(
        default=0,
        verbose_name="Successful Extractions"
    )
    failed_extractions = models.PositiveIntegerField(
        default=0,
        verbose_name="Failed Extractions"
    )

    # Error Tracking
    last_error = models.TextField(
        blank=True,
        verbose_name="Last Error"
    )
    error_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Consecutive Error Count"
    )

    # Settings
    auto_create_campaigns = models.BooleanField(
        default=False,
        verbose_name="Auto Create Campaigns",
        help_text="Automatically create campaigns for scraped content"
    )

    class Meta:
        verbose_name = "Source Site"
        verbose_name_plural = "Source Sites"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'is_active']),
            models.Index(fields=['next_check']),
            models.Index(fields=['category', 'is_public']),
        ]

    def __str__(self):
        return f"{self.name} ({self.url})"

    def get_success_rate(self):
        """Calculate extraction success rate"""
        total = self.total_posts_discovered
        if total == 0:
            return 0
        return round((self.successful_extractions / total) * 100, 2)


class APIAuditLog(models.Model):
    """Comprehensive API audit logging"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Request Information
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="User"
    )
    session_id = models.CharField(
        max_length=40,
        blank=True,
        verbose_name="Session ID"
    )

    # HTTP Details
    method = models.CharField(
        max_length=10,
        verbose_name="HTTP Method"
    )
    endpoint = models.CharField(
        max_length=500,
        verbose_name="API Endpoint"
    )
    full_url = models.URLField(
        verbose_name="Full URL"
    )

    # Client Information
    ip_address = models.GenericIPAddressField(
        verbose_name="IP Address"
    )
    user_agent = models.TextField(
        verbose_name="User Agent"
    )
    referer = models.URLField(
        blank=True,
        null=True,
        verbose_name="Referer"
    )

    # Request/Response Data
    request_headers = models.JSONField(
        default=dict,
        verbose_name="Request Headers"
    )
    request_body = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Request Body"
    )
    response_status = models.PositiveIntegerField(
        verbose_name="Response Status Code"
    )
    response_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Response Size (bytes)"
    )

    # Performance Metrics
    response_time_ms = models.FloatField(
        verbose_name="Response Time (ms)"
    )
    db_queries_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Database Queries Count"
    )
    db_time_ms = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Database Time (ms)"
    )

    # Resource Access
    resource_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Resource Type"
    )
    resource_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Resource ID"
    )

    # Security & Risk
    is_suspicious = models.BooleanField(
        default=False,
        verbose_name="Suspicious Activity"
    )
    risk_score = models.PositiveSmallIntegerField(
        default=0,
        validators=[MaxValueValidator(100)],
        verbose_name="Risk Score (0-100)"
    )

    # API Specific
    api_version = models.CharField(
        max_length=10,
        default='v1',
        verbose_name="API Version"
    )
    rate_limit_hit = models.BooleanField(
        default=False,
        verbose_name="Rate Limit Hit"
    )

    # Additional Context
    error_message = models.TextField(
        blank=True,
        verbose_name="Error Message"
    )
    additional_data = models.JSONField(
        default=dict,
        verbose_name="Additional Data"
    )

    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Timestamp"
    )

    class Meta:
        verbose_name = "API Audit Log"
        verbose_name_plural = "API Audit Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['endpoint', 'method']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['response_status', 'timestamp']),
            models.Index(fields=['is_suspicious', 'risk_score']),
        ]

    def __str__(self):
        user_info = f" ({self.user.username})" if self.user else " (Anonymous)"
        return f"{self.method} {self.endpoint}{user_info} - {self.response_status}"

    def is_error(self):
        """Check if this was an error response"""
        return self.response_status >= 400

    def is_slow(self, threshold_ms=1000):
        """Check if response was slower than threshold"""
        return self.response_time_ms > threshold_ms


class SystemMetrics(TimeStampedModel):
    """System-wide metrics and health indicators"""

    # API Metrics
    total_api_calls_today = models.PositiveIntegerField(default=0)
    successful_api_calls_today = models.PositiveIntegerField(default=0)
    failed_api_calls_today = models.PositiveIntegerField(default=0)
    avg_response_time_ms = models.FloatField(null=True, blank=True)

    # Content Metrics
    total_content_pieces = models.PositiveIntegerField(default=0)
    total_published_content = models.PositiveIntegerField(default=0)
    total_campaigns = models.PositiveIntegerField(default=0)

    # AI Metrics
    total_embeddings_created = models.PositiveIntegerField(default=0)
    total_images_generated = models.PositiveIntegerField(default=0)
    ai_processing_cost_today = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="AI Processing Cost Today"
    )

    # User Metrics
    active_users_today = models.PositiveIntegerField(default=0)
    new_users_today = models.PositiveIntegerField(default=0)
    premium_users = models.PositiveIntegerField(default=0)

    # System Health
    system_status = models.CharField(
        max_length=20,
        choices=[
            ('healthy', 'Healthy'),
            ('warning', 'Warning'),
            ('critical', 'Critical'),
            ('maintenance', 'Maintenance'),
        ],
        default='healthy'
    )

    # Date for daily metrics
    metrics_date = models.DateField(
        unique=True,
        default=timezone.now
    )

    class Meta:
        verbose_name = "System Metrics"
        verbose_name_plural = "System Metrics"
        ordering = ['-metrics_date']

    def __str__(self):
        return f"Metrics for {self.metrics_date}"