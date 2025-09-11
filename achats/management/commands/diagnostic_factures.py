# management/commands/diagnostic_factures.py
from django.core.management.base import BaseCommand
from achats.models import FactureFournisseur
from comptabilite.models import EcritureComptable
from decimal import Decimal

class Command(BaseCommand):
    help = 'Diagnostic complet des factures et écritures'

    def handle(self, *args, **options):
        # 1. Vérifier toutes les factures
        factures = FactureFournisseur.objects.all()
        self.stdout.write(f"=== DIAGNOSTIC DES FACTURES ===")
        self.stdout.write(f"Total factures: {factures.count()}")
        
        for facture in factures:
            self.stdout.write(
                f"\nFacture {facture.numero_facture}: "
                f"Statut: {facture.statut}, "
                f"HT: {facture.montant_ht}, "
                f"TVA: {facture.montant_tva}, "
                f"TTC: {facture.montant_ttc}"
            )
            
            # Vérifier les écritures liées
            ecritures = EcritureComptable.objects.filter(facture_fournisseur_liee=facture)
            self.stdout.write(f"  Écritures liées: {ecritures.count()}")
            
            for ecriture in ecritures:
                self.stdout.write(
                    f"    Écriture {ecriture.numero}: "
                    f"Montant: {ecriture.montant_devise}, "
                    f"Journal: {ecriture.journal.code}"
                )
                
                # Vérifier les lignes d'écriture
                for ligne in ecriture.lignes.all():
                    self.stdout.write(
                        f"      Ligne {ligne.compte.numero}: "
                        f"Débit: {ligne.debit}, "
                        f"Crédit: {ligne.credit}"
                    )
        
        # 2. Vérifier les écritures sans facture
        ecritures_sans_facture = EcritureComptable.objects.filter(
            facture_fournisseur_liee__isnull=False
        ).exclude(
            facture_fournisseur_liee__in=factures
        )
        
        self.stdout.write(f"\n=== ÉCRITURES AVEC FACTURE INEXISTANTE ===")
        self.stdout.write(f"Count: {ecritures_sans_facture.count()}")
        for ecriture in ecritures_sans_facture:
            self.stdout.write(f"Écriture {ecriture.numero} référence facture ID: {ecriture.facture_fournisseur_liee_id}")