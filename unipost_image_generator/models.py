import uuid
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from core.models import TimeStampedModel, Campaign
from core.validators import validate_image_dimensions, validate_prompt_content, validate_metadata_structure


class AIImageRequest(TimeStampedModel):
    """Model for tracking AI image generation requests"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Request Information
    requester = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='image_requests',
        verbose_name="Requester"
    )
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='image_requests',
        null=True,
        blank=True,
        verbose_name="Campaign"
    )

    # Content Source (Generic FK to content that inspired the image)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.UUIDField(null=True, blank=True)
    source_content = GenericForeignKey('content_type', 'object_id')

    # Prompt & Generation
    original_text = models.TextField(
        verbose_name="Source Text",
        help_text="Original text that inspired the image"
    )
    ai_prompt = models.TextField(
        validators=[validate_prompt_content],
        verbose_name="AI-Generated Prompt",
        help_text="Prompt created by AI for image generation"
    )
    user_prompt_modifications = models.TextField(
        blank=True,
        verbose_name="User Modifications",
        help_text="User modifications to the AI prompt"
    )
    final_prompt = models.TextField(
        verbose_name="Final Prompt Used",
        help_text="Final prompt sent to image generation API"
    )

    # Generation Parameters
    model_name = models.CharField(
        max_length=100,
        default='dall-e-3',
        verbose_name="AI Model Used"
    )
    image_size = models.CharField(
        max_length=20,
        choices=[
            ('256x256', '256x256'),
            ('512x512', '512x512'),
            ('1024x1024', '1024x1024'),
            ('1792x1024', '1792x1024'),
            ('1024x1792', '1024x1792'),
        ],
        default='1024x1024',
        verbose_name="Image Size"
    )
    style = models.CharField(
        max_length=50,
        choices=[
            ('vivid', 'Vivid'),
            ('natural', 'Natural'),
        ],
        default='vivid',
        verbose_name="Image Style"
    )
    quality = models.CharField(
        max_length=20,
        choices=[
            ('standard', 'Standard'),
            ('hd', 'HD'),
        ],
        default='standard',
        verbose_name="Image Quality"
    )

    # Processing Status
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
            ('cancelled', 'Cancelled'),
        ],
        default='pending',
        verbose_name="Status"
    )
    processing_started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Processing Started"
    )
    processing_completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Processing Completed"
    )

    # Cost & Usage
    estimated_cost = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Estimated Cost (USD)"
    )
    actual_cost = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="Actual Cost (USD)"
    )

    # Error Handling
    error_message = models.TextField(
        blank=True,
        verbose_name="Error Message"
    )
    retry_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Retry Count"
    )

    class Meta:
        verbose_name = "AI Image Request"
        verbose_name_plural = "AI Image Requests"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['requester', 'status']),
            models.Index(fields=['campaign', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return f"Image Request {self.id} ({self.status})"

    def get_processing_duration(self):
        """Get processing duration in seconds"""
        if self.processing_started_at and self.processing_completed_at:
            return (self.processing_completed_at - self.processing_started_at).total_seconds()
        return None


class EnhancedGeneratedImage(TimeStampedModel):
    """Enhanced model for generated images with better metadata"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Request Reference
    image_request = models.ForeignKey(
        AIImageRequest,
        on_delete=models.CASCADE,
        related_name='generated_images',
        verbose_name="Image Request"
    )

    # File Information
    image_path = models.CharField(
        max_length=500,
        verbose_name="Image File Path"
    )
    original_url = models.URLField(
        blank=True,
        verbose_name="Original API URL",
        help_text="Original URL from AI service"
    )
    file_size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="File Size (bytes)"
    )
    file_format = models.CharField(
        max_length=10,
        default='png',
        verbose_name="File Format"
    )

    # Image Properties
    width = models.PositiveIntegerField(
        verbose_name="Image Width"
    )
    height = models.PositiveIntegerField(
        verbose_name="Image Height"
    )
    aspect_ratio = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Aspect Ratio"
    )

    # API Response
    api_response = models.JSONField(
        default=dict,
        validators=[validate_metadata_structure],
        verbose_name="Full API Response"
    )
    revised_prompt = models.TextField(
        blank=True,
        verbose_name="API Revised Prompt",
        help_text="Prompt modifications made by the AI service"
    )

    # Quality & Analysis
    quality_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Quality Score"
    )
    content_analysis = models.JSONField(
        default=dict,
        verbose_name="Content Analysis Results"
    )

    # Usage & Performance
    download_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Download Count"
    )
    last_accessed = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Last Accessed"
    )

    # Publishing Status
    is_approved = models.BooleanField(
        default=False,
        verbose_name="Approved for Use"
    )
    approved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='approved_images',
        verbose_name="Approved By"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Approved At"
    )

    class Meta:
        verbose_name = "Enhanced Generated Image"
        verbose_name_plural = "Enhanced Generated Images"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['image_request', 'is_approved']),
            models.Index(fields=['width', 'height']),
            models.Index(fields=['quality_score']),
        ]

    def __str__(self):
        return f"Image {self.id} ({self.width}x{self.height})"

    def get_aspect_ratio_display(self):
        """Get human-readable aspect ratio"""
        from fractions import Fraction
        ratio = Fraction(self.width, self.height)
        return f"{ratio.numerator}:{ratio.denominator}"

    def save(self, *args, **kwargs):
        # Auto-calculate aspect ratio
        if self.width and self.height:
            self.aspect_ratio = self.get_aspect_ratio_display()
        super().save(*args, **kwargs)


# Keep original GeneratedImage model for backward compatibility (deprecated)
class GeneratedImage(models.Model):
    """DEPRECATED: Use EnhancedGeneratedImage instead"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    # Note: Using old Embedding model for backward compatibility
    from embeddings.models import Embedding
    embedding = models.ForeignKey(
        Embedding,
        on_delete=models.CASCADE,
        related_name='generated_images',
        verbose_name="Embedding Relacionado"
    )
    original_text = models.TextField(
        verbose_name="Texto Original",
        help_text="Texto do post usado para gerar a imagem"
    )
    generated_prompt = models.TextField(
        verbose_name="Prompt Gerado",
        help_text="Prompt criado pelo Claude MCP"
    )
    image_path = models.CharField(
        max_length=500,
        verbose_name="Caminho da Imagem",
        help_text="Caminho relativo para o arquivo da imagem"
    )
    dalle_response = models.JSONField(
        default=dict,
        verbose_name="Resposta DALL-E",
        help_text="Metadados retornados pela API DALL-E"
    )
    generation_metadata = models.JSONField(
        default=dict,
        verbose_name="Metadados de Geração",
        help_text="Informações sobre o processo de geração"
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
        ordering = ['-created_at']
        verbose_name = "Imagem Gerada (Deprecated)"
        verbose_name_plural = "Imagens Geradas (Deprecated)"

    def __str__(self) -> str:
        return f"Imagem para: {self.embedding.title or 'Sem título'}"
