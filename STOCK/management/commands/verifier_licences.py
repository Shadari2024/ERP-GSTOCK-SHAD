from django.core.management.base import BaseCommand
from STOCK.models import SystemeLicence
from django.utils import timezone

class Command(BaseCommand):
    help = 'Vérifie les licences expirées et envoie des notifications'

    def handle(self, *args, **options):
        licences = SystemeLicence.objects.filter(est_active=True)
        maintenant = timezone.now()
        
        for licence in licences:
            if licence.date_expiration < maintenant:
                licence.est_active = False
                licence.bloque = True
                licence.save()
                self.stdout.write(f"Licence {licence.id} désactivée (expirée)")
            elif (licence.date_expiration - maintenant).days < 7:
                if not licence.derniere_notification or (maintenant - licence.derniere_notification).days >= 1:
                    licence.envoyer_notification_expiration()
                    licence.derniere_notification = maintenant
                    licence.save()
                    self.stdout.write(f"Notification envoyée pour licence {licence.id}")