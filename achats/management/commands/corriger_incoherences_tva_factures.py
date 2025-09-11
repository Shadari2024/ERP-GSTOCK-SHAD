# management/commands/corriger_incoherences_tva_factures.py
from django.core.management.base import BaseCommand
from achats.models import FactureFournisseur, BonReception
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Corrige les incohérences TVA entre les bons de réception et les factures'

    def handle(self, *args, **options):
        self.stdout.write("=== CORRECTION DES INCOHÉRENCES TVA FACTURES ===")
        
        # 1. Corriger les factures avec des incohérences TVA
        factures_problematiques = FactureFournisseur.objects.filter(
            bon_reception__isnull=False
        )
        
        for facture in factures_problematiques:
            bon = facture.bon_reception
            if (facture.montant_ht != bon.total_ht or 
                facture.montant_tva != bon.total_tva or 
                facture.montant_ttc != bon.total_ttc):
                
                # Recalculer les totaux du bon
                bon.calculer_totaux()
                bon.refresh_from_db()
                
                ancien_ht = facture.montant_ht
                ancien_tva = facture.montant_tva
                ancien_ttc = facture.montant_ttc
                
                # Mettre à jour la facture
                facture.montant_ht = bon.total_ht
                facture.montant_tva = bon.total_tva
                facture.montant_ttc = bon.total_ttc
                facture.save()
                
                self.stdout.write(
                    f"Facture {facture.numero_facture} corrigée: "
                    f"HT {ancien_ht}→{bon.total_ht}, "
                    f"TVA {ancien_tva}→{bon.total_tva}, "
                    f"TTC {ancien_ttc}→{bon.total_ttc}"
                )
        
        # 2. Corriger les écritures comptables avec montant 0
        factures_zero = FactureFournisseur.objects.filter(
            montant_ttc=Decimal('0.00')
        )
        
        for facture in factures_zero:
            if facture.bon_reception:
                # Recalculer depuis le bon
                facture.bon_reception.calculer_totaux()
                facture.bon_reception.refresh_from_db()
                
                facture.montant_ht = facture.bon_reception.total_ht
                facture.montant_tva = facture.bon_reception.total_tva
                facture.montant_ttc = facture.bon_reception.total_ttc
                facture.save()
                
                self.stdout.write(
                    f"Facture {facture.numero_facture} (montant 0) corrigée: "
                    f"HT={facture.montant_ht}, TVA={facture.montant_tva}, TTC={facture.montant_ttc}"
                )
        
        self.stdout.write(self.style.SUCCESS("=== CORRECTION TERMINÉE ==="))