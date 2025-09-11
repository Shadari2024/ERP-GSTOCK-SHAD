# management/commands/verifier_comptes.py
from django.core.management.base import BaseCommand
from comptabilite.models import PlanComptableOHADA, JournalComptable
from parametres.models import Entreprise
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Vérifie et corrige les comptes comptables nécessaires'

    def handle(self, *args, **options):
        for entreprise in Entreprise.objects.all():
            self.stdout.write(f"\n=== Vérification de l'entreprise: {entreprise.nom} ===")
            
            # Réinitialiser complètement le plan comptable
            self.stdout.write("Initialisation du plan comptable...")
            PlanComptableOHADA.initialiser_plan_comptable(entreprise)
            JournalComptable.initialiser_journaux(entreprise)
            
            # Vérifier tous les comptes nécessaires
            comptes_necessaires = ['401', '511', '521', '531', '4456', '607']
            for numero in comptes_necessaires:
                try:
                    compte = PlanComptableOHADA.objects.get(
                        numero=numero, 
                        entreprise=entreprise
                    )
                    self.stdout.write(f"✓ Compte {numero} - {compte.intitule}")
                except PlanComptableOHADA.DoesNotExist:
                    self.stdout.write(f"✗ Compte {numero} MANQUANT - création urgente nécessaire")
            
            # Vérifier les journaux nécessaires
            journaux_necessaires = ['ACH', 'TRS', 'BQ', 'CA']
            for code in journaux_necessaires:
                try:
                    journal = JournalComptable.objects.get(
                        code=code, 
                        entreprise=entreprise
                    )
                    self.stdout.write(f"✓ Journal {code} - {journal.intitule}")
                except JournalComptable.DoesNotExist:
                    self.stdout.write(f"✗ Journal {code} MANQUANT - création urgente nécessaire")
            
            self.stdout.write("=== Vérification terminée ===\n")