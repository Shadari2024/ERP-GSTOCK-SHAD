from django.apps import AppConfig

class AchatsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'achats'
    verbose_name = 'Gestion des Achats'

    def ready(self):
        import achats.signals