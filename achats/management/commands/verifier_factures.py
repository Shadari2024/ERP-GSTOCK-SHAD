# management/commands/verifier_factures.py
from django.core.management.base import BaseCommand
from achats.models import FactureFournisseur
from decimal import Decimal

class Command(BaseCommand):
    help = 'Vérifie l\'état des factures fournisseurs'

    def handle(self, *args, **options):
        factures = FactureFournisseur.objects.all()
        
        self.stdout.write(f"Total des factures: {factures.count()}")
        
        for facture in factures:
            self.stdout.write(
                f"Facture {facture.numero_facture}: "
                f"Statut={facture.statut}, "
                f"HT={facture.montant_ht}, "
                f"TVA={facture.montant_tva}, "
                f"TTC={facture.montant_ttc}, "
                f"Bon réception={facture.bon_reception_id}"
            )