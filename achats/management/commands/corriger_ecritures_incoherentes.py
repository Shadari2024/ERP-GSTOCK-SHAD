# management/commands/corriger_ecritures_incoherentes.py
from django.core.management.base import BaseCommand
from comptabilite.models import EcritureComptable
from achats.models import FactureFournisseur, PaiementFournisseur
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Corrige les écritures comptables incohérentes'

    def handle(self, *args, **options):
        # 1. Corriger les écritures de paiement avec des montants incorrects
        ecritures_paiement = EcritureComptable.objects.filter(
            journal__code__in=['BQ', 'CA'],
            libelle__icontains='Paiement'
        )
        
        for ecriture in ecritures_paiement:
            try:
                # Trouver le paiement correspondant
                paiement = None
                if ecriture.piece_justificative:
                    paiement = PaiementFournisseur.objects.filter(
                        reference=ecriture.piece_justificative
                    ).first()
                
                if paiement and ecriture.montant_devise != paiement.montant:
                    ancien_montant = ecriture.montant_devise
                    ecriture.montant_devise = paiement.montant
                    ecriture.save()
                    
                    # Corriger aussi les lignes d'écriture
                    for ligne in ecriture.lignes.all():
                        if ligne.debit > 0:
                            ligne.debit = paiement.montant
                        if ligne.credit > 0:
                            ligne.credit = paiement.montant
                        ligne.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Correction paiement {ecriture.numero}: "
                            f"{ancien_montant} → {paiement.montant}"
                        )
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Erreur correction écriture {ecriture.numero}: {e}")
                )
        
        # 2. Corriger les écritures de facture avec des montants incorrects
        ecritures_facture = EcritureComptable.objects.filter(
            journal__code='ACH',
            libelle__icontains='Facture'
        )
        
        for ecriture in ecritures_facture:
            try:
                if ecriture.facture_fournisseur_liee:
                    facture = ecriture.facture_fournisseur_liee
                    if ecriture.montant_devise != facture.montant_ttc:
                        ancien_montant = ecriture.montant_devise
                        ecriture.montant_devise = facture.montant_ttc
                        ecriture.save()
                        
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Correction facture {ecriture.numero}: "
                                f"{ancien_montant} → {facture.montant_ttc}"
                            )
                        )
                        
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Erreur correction écriture {ecriture.numero}: {e}")
                )
        
        # 3. Supprimer les écritures en double
        from django.db.models import Count
        doublons = EcritureComptable.objects.values(
            'piece_justificative', 'journal__code'
        ).annotate(
            count=Count('id')
        ).filter(
            count__gt=1,
            piece_justificative__isnull=False
        )
        
        for doublon in doublons:
            ecritures = EcritureComptable.objects.filter(
                piece_justificative=doublon['piece_justificative'],
                journal__code=doublon['journal__code']
            ).order_by('created_at')
            
            # Garder la première, supprimer les doublons
            premiere = ecritures.first()
            for doublon in ecritures[1:]:
                self.stdout.write(f"Suppression doublon: {doublon.numero}")
                doublon.delete()
        
        self.stdout.write(
            self.style.SUCCESS("Correction des écritures incohérentes terminée")
        )