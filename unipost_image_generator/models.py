import uuid
from django.db import models
from embeddings.models import Embedding


class GeneratedImage(models.Model):
    """Modelo para armazenar metadados das imagens geradas"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
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
        verbose_name = "Imagem Gerada"
        verbose_name_plural = "Imagens Geradas"

    def __str__(self) -> str:
        return f"Imagem para: {self.embedding.title or 'Sem título'}"
