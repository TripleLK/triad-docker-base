from django.apps import AppConfig


class ContentExtractorConfig(AppConfig):
    """Configuration for Content Extractor app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.content_extractor'
    verbose_name = 'Content Extractor'
    
    def ready(self):
        """Initialize app when Django starts."""
        pass
