# management/commands/corriger_tous_les_bons.py
from django.core.management.base import BaseCommand
from achats.models import BonReception
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Corrige les totaux de tous les bons de réception'

    def handle(self, *args, **options):
        bons = BonReception.objects.all()
        total = bons.count()
        
        self.stdout.write(f'Correction des totaux pour {total} bons de réception...')
        
        for i, bon in enumerate(bons, 1):
            try:
                # Sauvegarder les anciennes valeurs pour comparaison
                ancien_ht = bon.total_ht
                ancien_tva = bon.total_tva
                ancien_ttc = bon.total_ttc
                
                # Recalculer
                bon.calculer_totaux()
                
                # Vérifier les changements
                if (ancien_ht != bon.total_ht or ancien_tva != bon.total_tva or 
                    ancien_ttc != bon.total_ttc):
                    self.stdout.write(
                        f"Bon {bon.numero_bon}: "
                        f"HT {ancien_ht}→{bon.total_ht}, "
                        f"TVA {ancien_tva}→{bon.total_tva}, "
                        f"TTC {ancien_ttc}→{bon.total_ttc}"
                    )
                
                if i % 10 == 0:
                    self.stdout.write(f'Progression: {i}/{total}')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Erreur avec le bon {bon.numero_bon}: {e}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Correction terminée pour {total} bons de réception')
        )