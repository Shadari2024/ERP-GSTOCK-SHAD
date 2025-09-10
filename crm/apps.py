from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class CrmConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crm'
    verbose_name = _('Gestion de la Relation Client (CRM)')
    
    def ready(self):
        import crm.signals