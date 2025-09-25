import uuid
from django.db import models
from django.contrib.auth.models import User
from core.models import TimeStampedModel, Campaign, PLATFORM_CHOICES, CONTENT_STATUS_CHOICES
from core.validators import validate_content_length, validate_tags_list


class ContentPiece(TimeStampedModel):
    """Enhanced model for all content pieces replacing Text"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Basic Information
    title = models.CharField(
        max_length=200,
        verbose_name="Title"
    )
    content = models.TextField(
        verbose_name="Content",
        validators=[validate_content_length]
    )

    # Content Type & Classification
    content_type = models.CharField(
        max_length=20,
        choices=[
            ('post', 'Blog Post'),
            ('social', 'Social Media Post'),
            ('email', 'Email Content'),
            ('ad', 'Advertisement'),
            ('video_script', 'Video Script'),
            ('other', 'Other'),
        ],
        default='social',
        verbose_name="Content Type"
    )

    # Platform & Status
    target_platforms = models.JSONField(
        default=list,
        verbose_name="Target Platforms"
    )
    status = models.CharField(
        max_length=20,
        choices=CONTENT_STATUS_CHOICES,
        default='draft',
        verbose_name="Status"
    )

    # Relationships
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='content_pieces',
        verbose_name="Creator"
    )
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='content_pieces',
        null=True,
        blank=True,
        verbose_name="Campaign"
    )

    # Metadata & SEO
    tags = models.JSONField(
        default=list,
        validators=[validate_tags_list],
        verbose_name="Tags"
    )
    metadata = models.JSONField(
        default=dict,
        verbose_name="Additional Metadata"
    )

    # Publishing & Scheduling
    is_published = models.BooleanField(
        default=False,
        verbose_name="Published"
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Published At"
    )
    scheduled_for = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Scheduled For"
    )

    # Analytics & Performance
    view_count = models.PositiveIntegerField(
        default=0,
        verbose_name="View Count"
    )
    engagement_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Engagement Score"
    )
    performance_metrics = models.JSONField(
        default=dict,
        verbose_name="Performance Metrics"
    )

    class Meta:
        verbose_name = "Content Piece"
        verbose_name_plural = "Content Pieces"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['creator', 'status']),
            models.Index(fields=['campaign', 'content_type']),
            models.Index(fields=['scheduled_for']),
            models.Index(fields=['is_published', 'published_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.content_type})"

    def can_be_published(self):
        """Check if content piece can be published"""
        return self.status in ['approved', 'scheduled']

    def get_word_count(self):
        """Calculate word count of content"""
        return len(self.content.split())


# Keep original Text model for backward compatibility (deprecated)
class Text(models.Model):
    """DEPRECATED: Use ContentPiece instead"""
    theme = models.CharField(
        verbose_name="Tema",
        max_length=200,
        null=False,
        blank=False
    )
    platform = models.CharField(
        max_length=200,
        choices=[
            ('FCB', 'Facebook'),
            ('INT', 'Instagram'),
            ('TTK', 'Tiktok'),
            ('LKN', 'Linkedin')
        ],
        null=False,
        blank=False,
        verbose_name="Plataforma"
    )
    content = models.TextField(
        verbose_name="Conteúdo",
        blank=False,
        null=False
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em"
    )
    is_approved = models.BooleanField(
        verbose_name='Aprovado',
        default=False
    )

    class Meta:
        ordering = ['-id']
        verbose_name = "Texto (Deprecated)"
        verbose_name_plural = "Textos (Deprecated)"

    def __str__(self) -> str:
        return f"{self.created_at}: {self.theme} - {self.platform}"
