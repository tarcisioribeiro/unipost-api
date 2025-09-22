import uuid
from django.db import models


ORIGIN_CHOICES = (
    ('webscraping', 'WebScraping'),
    ('generated', 'Generated'),
    ('business_brain', 'Business Brain')
)


class Embedding(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    origin = models.CharField(
        max_length=20,
        choices=ORIGIN_CHOICES,
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
        verbose_name = "Embedding"
        verbose_name_plural = "Embeddings"

    def __str__(self) -> str:
        return f"{self.origin}: {self.title or 'Sem título'}"
