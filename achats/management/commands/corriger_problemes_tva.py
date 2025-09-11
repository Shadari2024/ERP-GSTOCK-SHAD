# management/commands/corriger_problemes_tva.py
from django.core.management.base import BaseCommand
from achats.models import LigneCommandeAchat, LigneBonReception, FactureFournisseur
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Corrige les problèmes de TVA entre commandes, bons de réception et factures'

    def handle(self, *args, **options):
        self.stdout.write("=== CORRECTION DES PROBLÈMES DE TVA ===")
        
        # 1. Corriger les lignes de commande avec TVA manquante
        self.corriger_lignes_commande_tva()
        
        # 2. Corriger les lignes de bon de réception avec TVA incohérente
        self.corriger_lignes_bon_reception_tva()
        
        # 3. Recalculer tous les totaux
        self.recalculer_tous_totaux()
        
        # 4. Synchroniser les factures avec les bons de réception
        self.synchroniser_factures_bons()
        
        self.stdout.write(self.style.SUCCESS("=== CORRECTION TVA TERMINÉE ==="))

    def corriger_lignes_commande_tva(self):
        """Corrige les lignes de commande avec des problèmes de TVA"""
        # Appliquer un taux de TVA par défaut de 16% si non défini
        lignes_sans_tva = LigneCommandeAchat.objects.filter(
            taux_tva__isnull=True
        ) | LigneCommandeAchat.objects.filter(
            taux_tva=Decimal('0.00')
        )
        
        for ligne in lignes_sans_tva:
            ancien_taux = ligne.taux_tva
            ligne.taux_tva = Decimal('16.00')  # Taux par défaut de 16%
            ligne.save()
            self.stdout.write(
                f"Ligne commande {ligne.id}: TVA {ancien_taux} → 16.00%"
            )

    def corriger_lignes_bon_reception_tva(self):
        """Corrige les incohérences de TVA entre commande et bon de réception"""
        for ligne_bon in LigneBonReception.objects.all():
            if ligne_bon.ligne_commande and ligne_bon.taux_tva != ligne_bon.ligne_commande.taux_tva:
                ancien_taux = ligne_bon.taux_tva
                ligne_bon.taux_tva = ligne_bon.ligne_commande.taux_tva
                ligne_bon.save()
                self.stdout.write(
                    f"Ligne bon {ligne_bon.id}: TVA {ancien_taux} → {ligne_bon.ligne_commande.taux_tva}%"
                )

    def recalculer_tous_totaux(self):
        """Recalcule tous les totaux des bons de réception"""
        from achats.models import BonReception
        
        for bon in BonReception.objects.all():
            bon.calculer_totaux()
            self.stdout.write(f"Totaux recalculés pour bon {bon.numero_bon}")

    def synchroniser_factures_bons(self):
        """Synchronise les factures avec les totaux des bons de réception"""
        for facture in FactureFournisseur.objects.filter(bon_reception__isnull=False):
            bon = facture.bon_reception
            if (facture.montant_ht != bon.total_ht or 
                facture.montant_tva != bon.total_tva or 
                facture.montant_ttc != bon.total_ttc):
                
                ancien_ht = facture.montant_ht
                ancien_tva = facture.montant_tva
                ancien_ttc = facture.montant_ttc
                
                facture.montant_ht = bon.total_ht
                facture.montant_tva = bon.total_tva
                facture.montant_ttc = bon.total_ttc
                facture.save()
                
                self.stdout.write(
                    f"Facture {facture.numero_facture} synchronisée: "
                    f"HT {ancien_ht}→{bon.total_ht}, "
                    f"TVA {ancien_tva}→{bon.total_tva}, "
                    f"TTC {ancien_ttc}→{bon.total_ttc}"
                )