from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class GrhConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'grh'
    verbose_name = _('Gestion des Ressources Humaines')
    
    def ready(self):
        # Import des signaux si nécessaire
        try:
            from grh import signals  # Ensure signals.py exists in grh
        except ImportError:
            pass  # Optionally handle the error or remove this block if not needed