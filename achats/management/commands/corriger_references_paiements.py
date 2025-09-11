# management/commands/corriger_references_paiements.py
from django.core.management.base import BaseCommand
from achats.models import PaiementFournisseur
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Corrige les références invalides des paiements'

    def handle(self, *args, **options):
        # Paiements avec référence invalide
        paiements_invalides = PaiementFournisseur.objects.filter(
            reference__in=['oui', 'non', '']
        )
        
        total = paiements_invalides.count()
        self.stdout.write(f"Correction de {total} paiements avec référence invalide...")
        
        for i, paiement in enumerate(paiements_invalides, 1):
            try:
                # Générer une nouvelle référence valide
                ancienne_ref = paiement.reference
                paiement.reference = paiement.generate_reference()
                paiement.save()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Paiement {paiement.id}: '{ancienne_ref}' → '{paiement.reference}'"
                    )
                )
                
                if i % 10 == 0:
                    self.stdout.write(f"Progression: {i}/{total}")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Erreur avec paiement {paiement.id}: {e}")
                )
        
        self.stdout.write(
            self.style.SUCCESS("Correction des références terminée")
        )