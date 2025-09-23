# management/commands/diagnostic_factures.py
from django.core.management.base import BaseCommand
from achats.models import FactureFournisseur
from decimal import Decimal
import logging
from django.db import models

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Diagnostique les problèmes de création de factures'

    def handle(self, *args, **options):
        self.stdout.write("=== DIAGNOSTIC DES FACTURES ===")
        
        # Vérifier les comptes nécessaires
        self.verifier_comptes_comptables()
        
        # Vérifier les factures problématiques
        self.verifier_factures_problematiques()

    def verifier_comptes_comptables(self):
        """Vérifie que les comptes comptables nécessaires existent"""
        self.stdout.write("\n1. VÉRIFICATION DES COMPTES COMPTABLES")
        
        try:
            from comptabilite.models import PlanComptableOHADA, JournalComptable
            
            # Vérifier les comptes pour chaque entreprise
            entreprises = FactureFournisseur.objects.values_list('entreprise', flat=True).distinct()
            
            for entreprise_id in entreprises:
                self.stdout.write(f"\nEntreprise ID: {entreprise_id}")
                
                # Compte 607 - Achats
                try:
                    compte_607 = PlanComptableOHADA.objects.get(numero='607', entreprise_id=entreprise_id)
                    self.stdout.write("✓ Compte 607 (Achats) trouvé")
                except PlanComptableOHADA.DoesNotExist:
                    self.stdout.write("✗ Compte 607 (Achats) INTROUVABLE")
                
                # Compte 4456 - TVA
                try:
                    compte_4456 = PlanComptableOHADA.objects.get(numero='4456', entreprise_id=entreprise_id)
                    self.stdout.write("✓ Compte 4456 (TVA) trouvé")
                except PlanComptableOHADA.DoesNotExist:
                    self.stdout.write("✗ Compte 4456 (TVA) INTROUVABLE")
                
                # Compte 401 - Fournisseurs
                try:
                    compte_401 = PlanComptableOHADA.objects.get(numero='401', entreprise_id=entreprise_id)
                    self.stdout.write("✓ Compte 401 (Fournisseurs) trouvé")
                except PlanComptableOHADA.DoesNotExist:
                    self.stdout.write("✗ Compte 401 (Fournisseurs) INTROUVABLE")
                
                # Journal ACH
                try:
                    journal_ach = JournalComptable.objects.get(code='ACH', entreprise_id=entreprise_id)
                    self.stdout.write("✓ Journal ACH trouvé")
                except JournalComptable.DoesNotExist:
                    self.stdout.write("✗ Journal ACH INTROUVABLE")
                    
        except Exception as e:
            self.stdout.write(f"Erreur lors de la vérification des comptes: {e}")

    def verifier_factures_problematiques(self):
        """Vérifie les factures avec des données problématiques"""
        self.stdout.write("\n2. VÉRIFICATION DES FACTURES PROBLÉMATIQUES")
        
        # Factures avec montants invalides
        factures_invalides = FactureFournisseur.objects.filter(
            models.Q(montant_ht__lt=0) | 
            models.Q(montant_tva__lt=0) | 
            models.Q(montant_ttc__lt=0)
        )
        
        self.stdout.write(f"Factures avec montants négatifs: {factures_invalides.count()}")
        for facture in factures_invalides:
            self.stdout.write(f"  - {facture.numero_facture}: HT={facture.montant_ht}, TVA={facture.montant_tva}, TTC={facture.montant_ttc}")
        
        # Factures avec incohérence de totaux
        factures_incoherentes = FactureFournisseur.objects.annotate(
            total_calcule=models.F('montant_ht') + models.F('montant_tva')
        ).filter(
            models.Q(montant_ttc__gt=models.F('total_calcule') + Decimal('0.01')) |
            models.Q(montant_ttc__lt=models.F('total_calcule') - Decimal('0.01'))
        )
        
        self.stdout.write(f"\nFactures avec incohérence de totaux: {factures_incoherentes.count()}")
        for facture in factures_incoherentes:
            total_calcule = facture.montant_ht + facture.montant_tva
            self.stdout.write(f"  - {facture.numero_facture}: TTC={facture.montant_ttc}, Calculé={total_calcule}")