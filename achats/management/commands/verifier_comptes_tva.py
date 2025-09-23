# management/commands/verifier_comptes_tva.py
from django.core.management.base import BaseCommand
from comptabilite.models import PlanComptableOHADA
from django.contrib import messages

class Command(BaseCommand):
    help = 'Vérifie et corrige les comptes TVA'

    def handle(self, *args, **options):
        self.stdout.write("=== VÉRIFICATION DES COMPTES TVA ===")
        
        # Vérifier toutes les entreprises
        from parametres.models import Entreprise
        
        for entreprise in Entreprise.objects.all():
            self.stdout.write(f"\nEntreprise: {entreprise.nom}")
            
            # Vérifier le compte TVA déductible (4456)
            try:
                compte_tva_deductible = PlanComptableOHADA.objects.get(
                    numero='4456',
                    entreprise=entreprise
                )
                self.stdout.write("✓ Compte TVA déductible (4456) trouvé")
            except PlanComptableOHADA.DoesNotExist:
                self.stdout.write("✗ Compte TVA déductible (4456) INTROUVABLE - Création...")
                PlanComptableOHADA.objects.create(
                    numero='4456',
                    entreprise=entreprise,
                    classe='4',
                    intitule='TVA déductible',
                    type_compte='actif',
                    description='TVA déductible sur les achats'
                )
                self.stdout.write("✓ Compte TVA déductible (4456) créé")
            
            # Vérifier le compte Achats (607)
            try:
                compte_achats = PlanComptableOHADA.objects.get(
                    numero='607',
                    entreprise=entreprise
                )
                self.stdout.write("✓ Compte Achats (607) trouvé")
            except PlanComptableOHADA.DoesNotExist:
                self.stdout.write("✗ Compte Achats (607) INTROUVABLE - Création...")
                PlanComptableOHADA.objects.create(
                    numero='607',
                    entreprise=entreprise,
                    classe='6',
                    intitule='Achats de marchandises',
                    type_compte='charge',
                    description='Compte pour enregistrer les achats de marchandises'
                )
                self.stdout.write("✓ Compte Achats (607) créé")
            
            # Vérifier le compte Fournisseurs (401)
            try:
                compte_fournisseurs = PlanComptableOHADA.objects.get(
                    numero='401',
                    entreprise=entreprise
                )
                self.stdout.write("✓ Compte Fournisseurs (401) trouvé")
            except PlanComptableOHADA.DoesNotExist:
                self.stdout.write("✗ Compte Fournisseurs (401) INTROUVABLE - Création...")
                PlanComptableOHADA.objects.create(
                    numero='401',
                    entreprise=entreprise,
                    classe='4',
                    intitule='Fournisseurs',
                    type_compte='passif',
                    description='Compte des dettes envers les fournisseurs'
                )
                self.stdout.write("✓ Compte Fournisseurs (401) créé")