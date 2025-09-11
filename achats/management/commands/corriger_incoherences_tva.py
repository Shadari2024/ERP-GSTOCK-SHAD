# management/commands/corriger_incoherences_tva.py
from django.core.management.base import BaseCommand
from achats.models import LigneCommandeAchat, LigneBonReception, FactureFournisseur
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Corrige les incohérences de TVA dans les données existantes'

    def handle(self, *args, **options):
        self.stdout.write("=== CORRECTION DES INCOHÉRENCES TVA ===")
        
        # 1. Corriger les lignes de commande sans TVA
        self.corriger_lignes_commande_sans_tva()
        
        # 2. Corriger les incohérences entre commande et bon
        self.corriger_incoherences_commande_bon()
        
        # 3. Synchroniser les factures avec les bons
        self.synchroniser_factures_bons()
        
        self.stdout.write(self.style.SUCCESS("=== CORRECTION TVA TERMINÉE ==="))

    def corriger_lignes_commande_sans_tva(self):
        """Corrige les lignes de commande sans taux TVA"""
        lignes_sans_tva = LigneCommandeAchat.objects.filter(
            taux_tva__isnull=True
        ) | LigneCommandeAchat.objects.filter(
            taux_tva=Decimal('0.00')
        )
        
        for ligne in lignes_sans_tva:
            ancien_taux = ligne.taux_tva
            ligne.taux_tva = Decimal('16.00')
            ligne.save()
            
            # Recalculer le montant TVA
            ligne.montant_tva_ligne = ligne.total_ht_ligne * (ligne.taux_tva / Decimal('100'))
            ligne.save()
            
            self.stdout.write(
                f"Ligne commande {ligne.id}: TVA {ancien_taux} → 16.00%, "
                f"Montant TVA: {ligne.montant_tva_ligne}"
            )

    def corriger_incoherences_commande_bon(self):
        """Corrige les incohérences TVA entre commande et bon"""
        for ligne_bon in LigneBonReception.objects.all():
            if (ligne_bon.ligne_commande and 
                ligne_bon.taux_tva != ligne_bon.ligne_commande.taux_tva):
                
                ancien_taux = ligne_bon.taux_tva
                ligne_bon.taux_tva = ligne_bon.ligne_commande.taux_tva
                ligne_bon.save()
                
                self.stdout.write(
                    f"Ligne bon {ligne_bon.id}: TVA {ancien_taux} → {ligne_bon.ligne_commande.taux_tva}%"
                )

    def synchroniser_factures_bons(self):
        """Synchronise les factures avec les totaux des bons"""
        for facture in FactureFournisseur.objects.filter(bon_reception__isnull=False):
            bon = facture.bon_reception
            if (facture.montant_ht != bon.total_ht or 
                facture.montant_tva != bon.total_tva):
                
                ancien_ht = facture.montant_ht
                ancien_tva = facture.montant_tva
                
                facture.montant_ht = bon.total_ht
                facture.montant_tva = bon.total_tva
                facture.montant_ttc = bon.total_ttc
                facture.save()
                
                self.stdout.write(
                    f"Facture {facture.numero_facture} synchronisée: "
                    f"HT {ancien_ht}→{bon.total_ht}, "
                    f"TVA {ancien_tva}→{bon.total_tva}"
                )