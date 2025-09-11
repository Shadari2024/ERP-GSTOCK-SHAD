# management/commands/corriger_nouvelles_ecritures.py
from django.core.management.base import BaseCommand
from comptabilite.models import EcritureComptable
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Corrige manuellement les nouvelles écritures avec montant 0'

    def handle(self, *args, **options):
        self.stdout.write("=== CORRECTION MANUELLE DES NOUVELLES ÉCRITURES ===")
        
        # Trouver les écritures récentes avec montant 0 mais ayant des lignes
        from django.utils import timezone
        from datetime import timedelta
        
        date_limite = timezone.now() - timedelta(hours=1)  # Écritures des dernières heures
        
        ecritures_problematiques = EcritureComptable.objects.filter(
            montant_devise=Decimal('0.00'),
            created_at__gte=date_limite
        ).prefetch_related('lignes')
        
        ecritures_corrigees = 0
        
        for ecriture in ecritures_problematiques:
            if ecriture.lignes.exists():
                # Recalculer manuellement
                total_debit = sum(ligne.debit for ligne in ecriture.lignes.all())
                
                if total_debit > Decimal('0.00'):
                    # Mettre à jour l'écriture
                    ecriture.montant_devise = total_debit
                    ecriture.save(update_fields=['montant_devise'])
                    
                    ecritures_corrigees += 1
                    
                    self.stdout.write(
                        f"Écriture {ecriture.numero} CORRIGÉE MANUELLEMENT: "
                        f"0.00→{total_debit}"
                    )
        
        self.stdout.write(self.style.SUCCESS(f"=== {ecritures_corrigees} NOUVELLES ÉCRITURES CORRIGÉES ==="))