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
    # Configurações de crawling recursivo
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
        verbose_name="Padrões de URL permitidos (um por linha)",
        help_text="Expressões regulares para URLs que devem ser incluídas no crawling"
    )
    deny_patterns = models.TextField(
        blank=True,
        null=True,
        verbose_name="Padrões de URL negados (um por linha)",
        help_text="Expressões regulares para URLs que devem ser excluídas do crawling"
    )
    content_selectors = models.TextField(
        blank=True,
        null=True,
        verbose_name="Seletores CSS para conteúdo",
        help_text="Seletores CSS específicos para extrair conteúdo relevante (um por linha)"
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
