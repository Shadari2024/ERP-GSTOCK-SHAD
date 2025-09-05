from django.apps import AppConfig
from django.conf import settings

class StockConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'STOCK'


class TresorerieConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tresorerie'

    def ready(self):
        # Import des signaux
        import STOCK.signals
        
        

from django.apps import AppConfig

class YourAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'your_app_name'
    
    def ready(self):
        if not settings.DEBUG:
            from .backup import BackupManager
            BackupManager.schedule_backups()
            BackupManager.schedule_cleanup()