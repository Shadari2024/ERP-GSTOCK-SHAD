from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class PromotionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'promotions'
    verbose_name = _('Promotions')
    
    def ready(self):
        # Import des signaux avec import différé pour éviter les circulaires
        import promotions.signals