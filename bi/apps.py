from django.apps import AppConfig

class BIConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bi'
    verbose_name = ("Business Intelligence")
    
    def ready(self):
        # Import des signaux
        import bi.signals