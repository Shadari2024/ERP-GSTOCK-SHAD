# management/commands/supprimer_doublons_ecritures.py
from django.core.management.base import BaseCommand
from comptabilite.models import EcritureComptable
from django.db.models import Count

class Command(BaseCommand):
    help = 'Supprime les écritures comptables en double'

    def handle(self, *args, **options):
        # Trouver les écritures en double pour les mêmes factures
        doublons = EcritureComptable.objects.values(
            'facture_fournisseur_liee'
        ).annotate(
            count=Count('id')
        ).filter(
            count__gt=1,
            facture_fournisseur_liee__isnull=False
        )
        
        for doublon in doublons:
            facture_id = doublon['facture_fournisseur_liee']
            ecritures = EcritureComptable.objects.filter(
                facture_fournisseur_liee_id=facture_id
            ).order_by('created_at')
            
            # Garder la première écriture, supprimer les doublons
            premiere_ecriture = ecritures.first()
            doublons_a_supprimer = ecritures.exclude(id=premiere_ecriture.id)
            
            self.stdout.write(
                f"Facture {facture_id}: {doublons_a_supprimer.count()} doublons à supprimer"
            )
            
            for ecriture in doublons_a_supprimer:
                self.stdout.write(f"Suppression: {ecriture.numero}")
                ecriture.delete()
        
        self.stdout.write(
            self.style.SUCCESS("Nettoyage des doublons terminé")
        )