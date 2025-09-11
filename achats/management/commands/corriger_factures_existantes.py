# management/commands/corriger_factures_existantes.py
from django.core.management.base import BaseCommand
from achats.models import FactureFournisseur, BonReception
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Corrige les factures existantes avec les totaux recalculés des bons'

    def handle(self, *args, **options):
        self.stdout.write("=== CORRECTION DES FACTURES EXISTANTES ===")
        
        factures_corrigees = 0
        
        for facture in FactureFournisseur.objects.filter(bon_reception__isnull=False):
            bon = facture.bon_reception
            
            # Recalculer les totaux du bon
            bon.calculer_totaux()
            bon.refresh_from_db()
            
            # Vérifier si correction nécessaire
            if (facture.montant_ht != bon.total_ht or 
                facture.montant_tva != bon.total_tva or 
                facture.montant_ttc != bon.total_ttc):
                
                ancien_ht = facture.montant_ht
                ancien_tva = facture.montant_tva
                ancien_ttc = facture.montant_ttc
                
                # Mettre à jour la facture
                facture.montant_ht = bon.total_ht
                facture.montant_tva = bon.total_tva
                facture.montant_ttc = bon.total_ttc
                facture.save()
                
                factures_corrigees += 1
                
                self.stdout.write(
                    f"Facture {facture.numero_facture} CORRIGÉE: "
                    f"HT {ancien_ht}→{bon.total_ht}, "
                    f"TVA {ancien_tva}→{bon.total_tva}, "
                    f"TTC {ancien_ttc}→{bon.total_ttc}"
                )
        
        self.stdout.write(self.style.SUCCESS(f"=== {factures_corrigees} FACTURES CORRIGÉES ==="))