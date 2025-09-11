# management/commands/verifier_tva.py
from django.core.management.base import BaseCommand
from achats.models import LigneCommandeAchat, LigneBonReception, FactureFournisseur
from decimal import Decimal

class Command(BaseCommand):
    help = 'Vérifie la cohérence de la TVA dans le système'

    def handle(self, *args, **options):
        self.stdout.write("=== VÉRIFICATION DE LA COHÉRENCE TVA ===")
        
        # 1. Vérifier les lignes de commande
        problemes_commandes = self.verifier_lignes_commande()
        
        # 2. Vérifier les lignes de bon de réception
        problemes_bons = self.verifier_lignes_bon_reception()
        
        # 3. Vérifier la cohérence commande/bon/facture
        problemes_cohérence = self.verifier_cohérence_tva()
        
        if not any([problemes_commandes, problemes_bons, problemes_cohérence]):
            self.stdout.write(self.style.SUCCESS("✓ Aucun problème de TVA détecté"))
        else:
            self.stdout.write(self.style.WARNING("Problèmes de TVA détectés - Exécutez 'corriger_problemes_tva'"))

    def verifier_lignes_commande(self):
        """Vérifie les lignes de commande"""
        problemes = False
        
        # Lignes sans TVA
        lignes_sans_tva = LigneCommandeAchat.objects.filter(
            taux_tva__isnull=True
        ) | LigneCommandeAchat.objects.filter(
            taux_tva=Decimal('0.00')
        )
        
        if lignes_sans_tva.exists():
            self.stdout.write(self.style.WARNING(
                f"⚠️  {lignes_sans_tva.count()} lignes de commande sans TVA définie"
            ))
            problemes = True
        
        return problemes

    def verifier_lignes_bon_reception(self):
        """Vérifie les lignes de bon de réception"""
        problemes = False
        
        for ligne_bon in LigneBonReception.objects.all():
            if ligne_bon.ligne_commande and ligne_bon.taux_tva != ligne_bon.ligne_commande.taux_tva:
                self.stdout.write(self.style.WARNING(
                    f"⚠️  Incohérence TVA: Bon {ligne_bon.id} ({ligne_bon.taux_tva}%) ≠ "
                    f"Commande {ligne_bon.ligne_commande.id} ({ligne_bon.ligne_commande.taux_tva}%)"
                ))
                problemes = True
        
        return problemes

    def verifier_cohérence_tva(self):
        """Vérifie la cohérence entre commande, bon et facture"""
        problemes = False
        
        for facture in FactureFournisseur.objects.filter(bon_reception__isnull=False):
            bon = facture.bon_reception
            if bon:
                # Vérifier la cohérence des totaux
                if (facture.montant_ht != bon.total_ht or 
                    facture.montant_tva != bon.total_tva):
                    
                    self.stdout.write(self.style.WARNING(
                        f"⚠️  Incohérence facture/bon: {facture.numero_facture} - "
                        f"HT: {facture.montant_ht} ≠ {bon.total_ht}, "
                        f"TVA: {facture.montant_tva} ≠ {bon.total_tva}"
                    ))
                    problemes = True
        
        return problemes