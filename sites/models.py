import uuid
from django.db import models
from django.contrib.auth.models import User
from core.models import TimeStampedModel, SourceSite, POST_STATUS_CHOICES
from core.validators import validate_content_length, validate_url_list


class ScrapedPost(TimeStampedModel):
    """Model for posts scraped from monitored sites"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Basic Information
    title = models.CharField(
        max_length=500,
        verbose_name="Post Title"
    )
    url = models.URLField(
        unique=True,
        verbose_name="Original URL"
    )
    content = models.TextField(
        verbose_name="Extracted Content",
        validators=[validate_content_length]
    )

    # Content Analysis
    summary = models.TextField(
        blank=True,
        verbose_name="AI-Generated Summary"
    )
    keywords = models.JSONField(
        default=list,
        verbose_name="Extracted Keywords"
    )
    language = models.CharField(
        max_length=10,
        default='pt-BR',
        verbose_name="Detected Language"
    )

    # Relationships
    source_site = models.ForeignKey(
        SourceSite,
        on_delete=models.CASCADE,
        related_name='scraped_posts',
        verbose_name="Source Site"
    )
    processed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Processed By"
    )

    # Processing Status
    status = models.CharField(
        max_length=20,
        choices=POST_STATUS_CHOICES,
        default='discovered',
        verbose_name="Processing Status"
    )
    processing_started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Processing Started At"
    )
    processing_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Processing Completed At"
    )

    # Content Metrics
    word_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Word Count"
    )
    reading_time_minutes = models.PositiveIntegerField(
        default=0,
        verbose_name="Estimated Reading Time (minutes)"
    )
    quality_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Content Quality Score"
    )

    # Media & Assets
    featured_image_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Featured Image URL"
    )
    images = models.JSONField(
        default=list,
        validators=[validate_url_list],
        verbose_name="Extracted Image URLs"
    )

    # Metadata
    author = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Original Author"
    )
    published_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Original Publish Date"
    )
    scraped_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Scraped At"
    )

    # AI Processing
    ai_analysis = models.JSONField(
        default=dict,
        verbose_name="AI Analysis Results"
    )
    content_themes = models.JSONField(
        default=list,
        verbose_name="Identified Content Themes"
    )
    sentiment_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Sentiment Analysis Score"
    )

    # Error Handling
    error_message = models.TextField(
        blank=True,
        verbose_name="Last Processing Error"
    )
    retry_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Processing Retry Count"
    )

    class Meta:
        verbose_name = "Scraped Post"
        verbose_name_plural = "Scraped Posts"
        ordering = ['-scraped_at']
        indexes = [
            models.Index(fields=['source_site', 'status']),
            models.Index(fields=['scraped_at', 'status']),
            models.Index(fields=['quality_score']),
            models.Index(fields=['published_date']),
        ]

    def __str__(self):
        return f"{self.title[:50]}... ({self.source_site.name})"

    def is_processing_stale(self):
        """Check if processing has been stale for too long"""
        if not self.processing_started_at:
            return False

        from django.utils import timezone
        from datetime import timedelta

        # Consider stale if processing started more than 1 hour ago
        return timezone.now() - self.processing_started_at > timedelta(hours=1)

    def calculate_reading_time(self):
        """Calculate estimated reading time based on word count"""
        # Average reading speed: 200 words per minute
        return max(1, self.word_count // 200)

    def get_processing_duration(self):
        """Get processing duration in seconds"""
        if self.processing_started_at and self.processing_completed_at:
            return (self.processing_completed_at - self.processing_started_at).total_seconds()
        return None


# Keep original Site model for backward compatibility (deprecated)
class Site(models.Model):
    """DEPRECATED: Use SourceSite from core app instead"""
    name = models.CharField(
        verbose_name="Nome",
        max_length=200,
        null=False,
        blank=False
    )
    url = models.URLField(
        verbose_name="URL",
        null=False,
        blank=False
    )
    category = models.CharField(
        max_length=200,
        choices=[
            ('BLOG', 'Blog'),
            ('ECOMMERCE', 'E-commerce'),
            ('PORTFOLIO', 'Portfólio'),
            ('NOTICIAS', 'Notícias'),
            ('EMPRESA', 'Empresa'),
            ('EDUCACAO', 'Educação'),
            ('OUTROS', 'Outros')
        ],
        null=False,
        blank=False,
        verbose_name="Categoria"
    )
    monitored = models.BooleanField(
        default=False,
        verbose_name="Monitorar para novos posts"
    )
    enable_recursive_crawling = models.BooleanField(
        default=True,
        verbose_name="Habilitar crawling recursivo"
    )
    max_depth = models.PositiveIntegerField(
        default=2,
        verbose_name="Profundidade máxima de crawling"
    )
    max_pages = models.PositiveIntegerField(
        default=50,
        verbose_name="Máximo de páginas para crawl"
    )
    allow_patterns = models.TextField(
        blank=True,
        null=True,
        verbose_name="Padrões de URL permitidos (um por linha)"
    )
    deny_patterns = models.TextField(
        blank=True,
        null=True,
        verbose_name="Padrões de URL negados (um por linha)"
    )
    content_selectors = models.TextField(
        blank=True,
        null=True,
        verbose_name="Seletores CSS para conteúdo"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Criado em"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Atualizado em"
    )

    class Meta:
        ordering = ['-id']
        verbose_name = "Site (Deprecated)"
        verbose_name_plural = "Sites (Deprecated)"

    def __str__(self) -> str:
        return f"{self.name} - {self.category}"
