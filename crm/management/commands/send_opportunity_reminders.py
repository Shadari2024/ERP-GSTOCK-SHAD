from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

from crm.models import Opportunite, TemplateEmail

class Command(BaseCommand):
    help = 'Envoie les rappels pour les opportunités approchant de leur date de fermeture'
    
    def handle(self, *args, **options):
        aujourdhui = timezone.now().date()
        
        # Opportunités qui ferment dans 3 jours
        opportunites = Opportunite.objects.filter(
            date_fermeture_prevue=aujourdhui + timedelta(days=3),
            statut__est_terminee=False
        )
        
        for opportunite in opportunites:
            if opportunite.assigne_a and opportunite.assigne_a.email:
                try:
                    # Envoyer email de rappel
                    sujet = f"Rappel: Opportunité {opportunite.nom} approche de sa date de fermeture"
                    message = render_to_string('crm/emails/rappel_opportunite.txt', {
                        'opportunite': opportunite,
                        'jours_restants': 3
                    })
                    
                    send_mail(
                        sujet,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [opportunite.assigne_a.email],
                        fail_silently=False,
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(f"Rappel envoyé pour {opportunite.nom}")
                    )
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Erreur pour {opportunite.nom}: {str(e)}")
                    )