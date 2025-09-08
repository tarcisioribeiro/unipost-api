from django.db import models


PLATFORM_CHOICES = (
    ('FCB', 'Facebook'),
    ('INT', 'Instagram'),
    ('TTK', 'Tiktok'),
    ('LKN', 'Linkedin')
)


class Text(models.Model):
    theme = models.CharField(
        verbose_name="Tema",
        max_length=200,
        null=False,
        blank=False
    )
    platform = models.CharField(
        max_length=200,
        choices=PLATFORM_CHOICES,
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
    is_aproved = models.BooleanField(
        verbose_name='Aprovado',
        default=False
    )

    class Meta:
        ordering = ['-id']
        verbose_name = "Texto"
        verbose_name_plural = "Textos"

    def __str__(self) -> str:
        return f"{self.created_at}: {self.theme} - {self.platform}"
