import os
from celery import Celery

# Définir le module de configuration Django par défaut pour Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erp_gstock.settings')

app = Celery('erp_gstock')

# Charger la configuration depuis settings.py, avec le préfixe 'CELERY_'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-découvrir les tâches dans les apps Django
app.autodiscover_tasks()



from celery import shared_task
from django.core.management import call_command
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_daily_greetings():
    """Tâche pour envoyer les emails de bonjour quotidiens"""
    try:
        call_command('send_daily_greetings')
        logger.info("Emails de bonjour quotidiens envoyés avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi des emails de bonjour: {str(e)}")