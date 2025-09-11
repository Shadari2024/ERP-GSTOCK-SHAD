# management/commands/corriger_montants_ecritures.py
from django.core.management.base import BaseCommand
from comptabilite.models import EcritureComptable
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Corrige les montants des écritures comptables qui affichent 0'

    def handle(self, *args, **options):
        self.stdout.write("=== CORRECTION DES MONTANTS D'ÉCRITURES COMPTABLES ===")
        
        ecritures_corrigees = 0
        
        # Trouver les écritures avec montant_devise = 0 mais ayant des lignes
        ecritures_problematiques = EcritureComptable.objects.filter(
            montant_devise=Decimal('0.00')
        ).prefetch_related('lignes')
        
        for ecriture in ecritures_problematiques:
            if ecriture.lignes.exists():
                # Recalculer le montant à partir des lignes
                total_debit = sum(ligne.debit for ligne in ecriture.lignes.all())
                
                if total_debit > Decimal('0.00'):
                    ancien_montant = ecriture.montant_devise
                    ecriture.montant_devise = total_debit
                    ecriture.save(update_fields=['montant_devise'])
                    
                    ecritures_corrigees += 1
                    
                    self.stdout.write(
                        f"Écriture {ecriture.numero} CORRIGÉE: "
                        f"{ancien_montant}→{total_debit}"
                    )
        
        self.stdout.write(self.style.SUCCESS(f"=== {ecritures_corrigees} ÉCRITURES CORRIGÉES ==="))