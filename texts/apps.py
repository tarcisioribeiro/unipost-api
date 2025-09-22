from django.apps import AppConfig


class TextsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'texts'
    verbose_name = 'Textos'

    def ready(self):
        """Importa signals quando o app está pronto"""
        import texts.signals  # noqa: F401
