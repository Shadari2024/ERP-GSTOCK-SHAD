# management/commands/corriger_relations_factures.py
from django.core.management.base import BaseCommand
from achats.models import FactureFournisseur
from comptabilite.models import EcritureComptable

class Command(BaseCommand):
    help = 'Corrige les relations entre les écritures et les factures'

    def handle(self, *args, **options):
        # 1. Trouver les écritures avec des références de facture invalides
        ecritures = EcritureComptable.objects.filter(
            facture_fournisseur_liee__isnull=False
        )
        
        for ecriture in ecritures:
            try:
                # Vérifier si la facture existe vraiment
                facture = FactureFournisseur.objects.get(id=ecriture.facture_fournisseur_liee_id)
                # Si oui, mettre à jour le montant
                if ecriture.montant_devise != facture.montant_ttc:
                    self.stdout.write(
                        f"Correction montant: {ecriture.numero} - {ecriture.montant_devise} → {facture.montant_ttc}"
                    )
                    ecriture.montant_devise = facture.montant_ttc
                    ecriture.save()
                    
            except FactureFournisseur.DoesNotExist:
                self.stdout.write(
                    f"Facture introuvable pour écriture {ecriture.numero}: ID {ecriture.facture_fournisseur_liee_id}"
                )
                # Optionnel: supprimer la référence invalide
                # ecriture.facture_fournisseur_liee = None
                # ecriture.save()
        
        # 2. Trouver les factures sans écriture
        factures_sans_ecriture = FactureFournisseur.objects.filter(
            statut__in=['validee', 'payee', 'partiellement_payee'],
            montant_ttc__gt=0
        ).exclude(
            id__in=EcritureComptable.objects.values('facture_fournisseur_liee')
        )
        
        self.stdout.write(f"\nFactures sans écriture: {factures_sans_ecriture.count()}")
        for facture in factures_sans_ecriture:
            self.stdout.write(f"Création écriture pour {facture.numero_facture}")
            ecriture = facture.creer_ecriture_comptable()
            if ecriture:
                self.stdout.write(f"Écriture créée: {ecriture.numero}")