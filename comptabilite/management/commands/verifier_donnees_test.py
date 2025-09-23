# management/commands/verifier_donnees_test.py
from django.core.management.base import BaseCommand
from comptabilite.models import PlanComptableOHADA, JournalComptable
from decimal import Decimal

class Command(BaseCommand):
    help = 'Vérifie les données de test pour les écritures comptables'

    def handle(self, *args, **options):
        self.stdout.write("=== VÉRIFICATION DES DONNÉES DE TEST ===")
        
        # Vérifier toutes les entreprises
        from parametres.models import Entreprise
        
        for entreprise in Entreprise.objects.all():
            self.stdout.write(f"\nEntreprise: {entreprise.nom}")
            
            # Vérifier les comptes essentiels
            comptes_essentiels = ['607', '4456', '401']
            for numero in comptes_essentiels:
                try:
                    compte = PlanComptableOHADA.objects.get(numero=numero, entreprise=entreprise)
                    self.stdout.write(f"✓ Compte {numero} ({compte.intitule}) trouvé")
                    
                    # Vérifier que le numéro n'est pas vide
                    if not compte.numero or compte.numero.strip() == '':
                        self.stdout.write(f"✗ Compte {numero} a un numéro vide!")
                        compte.numero = numero
                        compte.save()
                        self.stdout.write(f"  → Numéro corrigé: {numero}")
                        
                except PlanComptableOHADA.DoesNotExist:
                    self.stdout.write(f"✗ Compte {numero} INTROUVABLE")
            
            # Vérifier le journal ACH
            try:
                journal = JournalComptable.objects.get(code='ACH', entreprise=entreprise)
                self.stdout.write(f"✓ Journal ACH trouvé")
            except JournalComptable.DoesNotExist:
                self.stdout.write(f"✗ Journal ACH INTROUVABLE")