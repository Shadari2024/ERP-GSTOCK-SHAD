from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from STOCK.models import Client
from parametres.models import Entreprise
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Envoie un email de bonjour quotidien à tous les clients actifs de chaque entreprise'
    
    def handle(self, *args, **options):
        self.stdout.write("Début de l'envoi des emails de bonjour...")
        
        # Récupérer toutes les entreprises actives
        entreprises = Entreprise.objects.filter(actif=True)
        
        for entreprise in entreprises:
            try:
                self.envoyer_bonjour_entreprise(entreprise)
                self.stdout.write(
                    self.style.SUCCESS(f"Emails envoyés pour l'entreprise {entreprise.nom}")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Erreur pour {entreprise.nom}: {str(e)}")
                )
                logger.error(f"Erreur lors de l'envoi des emails pour {entreprise.nom}: {str(e)}")
        
        self.stdout.write(self.style.SUCCESS("Processus d'envoi des emails de bonjour terminé"))
    
    def envoyer_bonjour_entreprise(self, entreprise):
        """Envoie les emails de bonjour pour une entreprise spécifique"""
        # Récupérer tous les clients actifs de l'entreprise
        clients = Client.objects.filter(
            entreprise=entreprise,
            statut='ACT',  # Clients actifs seulement
            email__isnull=False
        ).exclude(email='')
        
        self.stdout.write(f"Envoi à {clients.count()} clients pour {entreprise.nom}")
        
        for client in clients:
            try:
                self.envoyer_email_bonjour(client, entreprise)
                logger.info(f"Email de bonjour envoyé à {client.email}")
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi à {client.email}: {str(e)}")
                continue
    
    def envoyer_email_bonjour(self, client, entreprise):
        """Envoie un email de bonjour personnalisé à un client"""
        # Préparer le contenu de l'email
        sujet = f"Bonjour de la part de {entreprise.nom} !"
        
        message = render_to_string('emails/bonjour_quotidien.txt', {
            'client': client,
            'entreprise': entreprise,
            'date': timezone.now().date(),
        })
        
        # Envoyer l'email
        send_mail(
            sujet,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [client.email],
            fail_silently=False,
            html_message=render_to_string('emails/bonjour_quotidien.html', {
                'client': client,
                'entreprise': entreprise,
                'date': timezone.now().date(),
            })
        )