from django.db import models


CATEGORY_CHOICES = (
    ('BLOG', 'Blog'),
    ('ECOMMERCE', 'E-commerce'),
    ('PORTFOLIO', 'Portfólio'),
    ('NOTICIAS', 'Notícias'),
    ('EMPRESA', 'Empresa'),
    ('EDUCACAO', 'Educação'),
    ('OUTROS', 'Outros')
)


class Site(models.Model):
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
        choices=CATEGORY_CHOICES,
        null=False,
        blank=False,
        verbose_name="Categoria"
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
        verbose_name = "Site"
        verbose_name_plural = "Sites"

    def __str__(self) -> str:
        return f"{self.name} - {self.category}"
