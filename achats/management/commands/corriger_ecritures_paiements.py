# management/commands/corriger_ecritures_paiements.py
from django.core.management.base import BaseCommand
from achats.models import PaiementFournisseur
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Corrige les écritures comptables manquantes pour les paiements'

    def handle(self, *args, **options):
        # Paiements sans écriture comptable
        paiements = PaiementFournisseur.objects.filter(
            statut='valide',
            montant__gt=Decimal('0.00')
        )
        
        total = paiements.count()
        self.stdout.write(f"Vérification de {total} paiements...")
        
        for i, paiement in enumerate(paiements, 1):
            try:
                # Vérifier si une écriture existe déjà
                from comptabilite.models import EcritureComptable
                ecriture_existante = EcritureComptable.objects.filter(
                    facture_fournisseur_liee=paiement.facture,
                    libelle__icontains=paiement.reference
                ).exists()
                
                if not ecriture_existante:
                    self.stdout.write(f"Création écriture pour paiement {paiement.reference}...")
                    ecriture = paiement.creer_ecriture_comptable()
                    if ecriture:
                        self.stdout.write(
                            self.style.SUCCESS(f"Écriture créée: {ecriture.numero}")
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"Échec création écriture pour {paiement.reference}")
                        )
                
                if i % 10 == 0:
                    self.stdout.write(f"Progression: {i}/{total}")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Erreur avec paiement {paiement.reference}: {e}")
                )
        
        self.stdout.write(
            self.style.SUCCESS("Correction des écritures terminée")
        )