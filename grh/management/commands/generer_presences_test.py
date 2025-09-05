from django.core.management.base import BaseCommand
from django.utils import timezone
from grh.models import Presence, Employe
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Génère des données de présence factices pour tester la paie'
    
    def handle(self, *args, **options):
        # Récupérer tous les employés actifs
        employes = Employe.objects.filter(statut='ACTIF')
        
        # Générer des présences pour le mois en cours
        maintenant = timezone.now()
        debut_mois = maintenant.replace(day=1, hour=8, minute=0, second=0, microsecond=0)
        
        for employe in employes:
            # Générer des présences pour tous les jours ouvrables du mois
            date_courante = debut_mois
            while date_courante.month == maintenant.month:
                # Sauter les weekends
                if date_courante.weekday() < 5:  # 0-4 = lundi-vendredi
                    # Créer une présence
                    Presence.objects.get_or_create(
                        entreprise=employe.entreprise,
                        employe=employe,
                        date=date_courante.date(),
                        defaults={
                            'heure_arrivee': datetime.strptime('08:00', '%H:%M').time(),
                            'heure_depart': datetime.strptime('17:00', '%H:%M').time(),
                            'statut': 'PRESENT',
                            'heures_travaillees': 9.0  # 8h + 1h pause
                        }
                    )
                
                date_courante += timedelta(days=1)
        
        self.stdout.write(
            self.style.SUCCESS(f'Données de présence générées pour {employes.count()} employés')
        )