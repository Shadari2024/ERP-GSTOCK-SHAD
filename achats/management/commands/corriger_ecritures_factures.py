# management/commands/corriger_ecritures_factures.py
from django.core.management.base import BaseCommand
from achats.models import FactureFournisseur
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Corrige les écritures comptables manquantes pour les factures'

    def handle(self, *args, **options):
        # Inclure tous les statuts sauf brouillon et annulée
        factures = FactureFournisseur.objects.filter(
            statut__in=['validee', 'payee', 'partiellement_payee'],
            montant_ttc__gt=Decimal('0.00')
        )
        
        total = factures.count()
        self.stdout.write(f"Vérification de {total} factures...")
        
        for i, facture in enumerate(factures, 1):
            try:
                # Vérifier si une écriture existe déjà
                from comptabilite.models import EcritureComptable
                ecriture_existante = EcritureComptable.objects.filter(
                    facture_fournisseur_liee=facture
                ).exists()
                
                if not ecriture_existante:
                    self.stdout.write(f"Création écriture pour facture {facture.numero_facture}...")
                    ecriture = facture.creer_ecriture_comptable()
                    if ecriture:
                        self.stdout.write(
                            self.style.SUCCESS(f"Écriture créée: {ecriture.numero} - {facture.montant_ttc}")
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"Échec création écriture pour {facture.numero_facture}")
                        )
                else:
                    # Vérifier si l'écriture existante a le bon montant
                    ecritures = EcritureComptable.objects.filter(facture_fournisseur_liee=facture)
                    for ecriture in ecritures:
                        if ecriture.montant_devise != facture.montant_ttc:
                            ancien_montant = ecriture.montant_devise
                            ecriture.montant_devise = facture.montant_ttc
                            ecriture.save()
                            self.stdout.write(
                                self.style.SUCCESS(f"Montant corrigé: {ecriture.numero} - {ancien_montant} → {facture.montant_ttc}")
                            )
                
                if i % 10 == 0:
                    self.stdout.write(f"Progression: {i}/{total}")
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Erreur avec facture {facture.numero_facture}: {e}")
                )
        
        self.stdout.write(
            self.style.SUCCESS("Correction des écritures de factures terminée")
        )