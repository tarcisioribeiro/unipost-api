import uuid
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from core.models import TimeStampedModel, Campaign
from core.validators import validate_embedding_vector, validate_metadata_structure


class KnowledgeBase(TimeStampedModel):
    """Enhanced model for organizing embeddings into knowledge bases"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Basic Information
    name = models.CharField(
        max_length=200,
        verbose_name="Knowledge Base Name"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Description"
    )

    # Ownership
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='knowledge_bases',
        verbose_name="Owner"
    )

    # Configuration
    embedding_model = models.CharField(
        max_length=100,
        default='text-embedding-ada-002',
        verbose_name="Embedding Model"
    )
    dimension = models.PositiveIntegerField(
        default=1536,
        verbose_name="Vector Dimension"
    )

    # Access Control
    is_public = models.BooleanField(
        default=False,
        verbose_name="Public Knowledge Base"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Active"
    )

    # Statistics
    total_embeddings = models.PositiveIntegerField(
        default=0,
        verbose_name="Total Embeddings"
    )
    total_tokens = models.PositiveBigIntegerField(
        default=0,
        verbose_name="Total Tokens Processed"
    )

    class Meta:
        verbose_name = "Knowledge Base"
        verbose_name_plural = "Knowledge Bases"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.owner.username})"


class EnhancedEmbedding(TimeStampedModel):
    """Enhanced embedding model with better relationships and metadata"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Content Information
    title = models.CharField(
        max_length=500,
        verbose_name="Content Title"
    )
    content = models.TextField(
        verbose_name="Original Content"
    )
    content_hash = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="Content Hash",
        help_text="SHA-256 hash of content for deduplication"
    )

    # Embedding Data
    embedding_vector = models.JSONField(
        validators=[validate_embedding_vector],
        verbose_name="Embedding Vector"
    )
    model_name = models.CharField(
        max_length=100,
        default='text-embedding-ada-002',
        verbose_name="Model Used"
    )
    token_count = models.PositiveIntegerField(
        verbose_name="Token Count"
    )

    # Relationships
    knowledge_base = models.ForeignKey(
        KnowledgeBase,
        on_delete=models.CASCADE,
        related_name='embeddings',
        verbose_name="Knowledge Base"
    )
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='embeddings',
        null=True,
        blank=True,
        verbose_name="Campaign"
    )

    # Generic relationship to source content
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.UUIDField(null=True, blank=True)
    source_content = GenericForeignKey('content_type', 'object_id')

    # Source & Origin
    source_type = models.CharField(
        max_length=50,
        choices=[
            ('scraped_post', 'Scraped Post'),
            ('content_piece', 'Content Piece'),
            ('user_upload', 'User Upload'),
            ('generated', 'AI Generated'),
            ('imported', 'Imported'),
            ('other', 'Other'),
        ],
        verbose_name="Source Type"
    )
    source_url = models.URLField(
        blank=True,
        null=True,
        verbose_name="Original Source URL"
    )

    # Quality & Analysis
    quality_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name="Content Quality Score"
    )
    language = models.CharField(
        max_length=10,
        default='pt-BR',
        verbose_name="Content Language"
    )
    topics = models.JSONField(
        default=list,
        verbose_name="Identified Topics"
    )
    keywords = models.JSONField(
        default=list,
        verbose_name="Key Terms"
    )

    # Processing Status
    is_processed = models.BooleanField(
        default=True,
        verbose_name="Processing Complete"
    )
    processing_error = models.TextField(
        blank=True,
        verbose_name="Processing Error"
    )

    # Enhanced Metadata
    metadata = models.JSONField(
        default=dict,
        validators=[validate_metadata_structure],
        verbose_name="Enhanced Metadata"
    )

    # Usage Statistics
    similarity_search_count = models.PositiveIntegerField(
        default=0,
        verbose_name="Times Found in Similarity Search"
    )
    last_accessed = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Last Accessed"
    )

    class Meta:
        verbose_name = "Enhanced Embedding"
        verbose_name_plural = "Enhanced Embeddings"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['knowledge_base', 'source_type']),
            models.Index(fields=['content_hash']),
            models.Index(fields=['quality_score']),
            models.Index(fields=['campaign', 'is_processed']),
            models.Index(fields=['language', 'source_type']),
        ]

    def __str__(self):
        return f"{self.title[:50]}... ({self.knowledge_base.name})"

    def calculate_similarity(self, other_vector):
        """Calculate cosine similarity with another vector"""
        import numpy as np

        a = np.array(self.embedding_vector)
        b = np.array(other_vector)

        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


# Keep original Embedding model for backward compatibility (deprecated)
class Embedding(models.Model):
    """DEPRECATED: Use EnhancedEmbedding instead"""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    origin = models.CharField(
        max_length=20,
        choices=[
            ('webscraping', 'WebScraping'),
            ('generated', 'Generated'),
            ('business_brain', 'Business Brain')
        ],
        null=False,
        blank=False,
        verbose_name="Origem"
    )
    content = models.TextField(
        verbose_name="Conteúdo Original",
        blank=False,
        null=False
    )
    title = models.CharField(
        max_length=500,
        verbose_name="Título",
        blank=True,
        null=True
    )
    embedding_vector = models.JSONField(
        verbose_name="Vetor Embedding",
        null=False,
        blank=False
    )
    metadata = models.JSONField(
        default=dict,
        verbose_name="Metadados",
        blank=True
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
        verbose_name = "Embedding (Deprecated)"
        verbose_name_plural = "Embeddings (Deprecated)"

    def __str__(self) -> str:
        return f"{self.origin}: {self.title or 'Sem título'}"
