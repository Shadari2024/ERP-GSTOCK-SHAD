# management/commands/corriger_incoherences_comptables.py
from django.core.management.base import BaseCommand
from comptabilite.models import EcritureComptable, LigneEcriture
from achats.models import FactureFournisseur
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Corrige toutes les incohérences comptables de manière complète'

    def handle(self, *args, **options):
        self.stdout.write("=== CORRECTION COMPLÈTE DES INCOHÉRENCES COMPTABLES ===")
        
        # 1. Corriger les écritures avec la facture FF-2025-0005
        self.corriger_ecriture_ff_2025_0005()
        
        # 2. Corriger les écritures avec des montants incohérents
        self.corriger_montants_incoherents()
        
        # 3. Équilibrer toutes les écritures
        self.equilibrer_toutes_ecritures()
        
        # 4. Corriger les incohérences facture/écriture
        self.corriger_incoherences_factures()
        
        # 5. Supprimer les doublons
        self.supprimer_doublons()
        
        self.stdout.write(self.style.SUCCESS("Correction complète terminée"))

    def corriger_ecriture_ff_2025_0005(self):
        """Corrige spécifiquement l'écriture de la facture FF-2025-0005"""
        try:
            facture = FactureFournisseur.objects.get(numero_facture='FF-2025-0005')
            ecriture = EcritureComptable.objects.get(facture_fournisseur_liee=facture)
            
            # Vérifier et corriger les lignes
            ligne_tva = ecriture.lignes.filter(compte__numero='4455').first()
            if ligne_tva and ligne_tva.debit != facture.montant_tva:
                ancien_montant = ligne_tva.debit
                ligne_tva.debit = facture.montant_tva
                ligne_tva.save()
                self.stdout.write(
                    f"Correction TVA FF-2025-0005: {ancien_montant} → {facture.montant_tva}"
                )
            
            # Corriger le total crédit
            ligne_fournisseur = ecriture.lignes.filter(compte__numero='401').first()
            if ligne_fournisseur:
                nouveau_credit = facture.montant_ht + facture.montant_tva
                if ligne_fournisseur.credit != nouveau_credit:
                    ancien_credit = ligne_fournisseur.credit
                    ligne_fournisseur.credit = nouveau_credit
                    ligne_fournisseur.save()
                    self.stdout.write(
                        f"Correction crédit fournisseur: {ancien_credit} → {nouveau_credit}"
                    )
            
            # Recalculer le montant devise
            ecriture.recalculer_montant_devise()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur correction FF-2025-0005: {e}"))

    def corriger_montants_incoherents(self):
        """Corrige les montants incohérents entre les écritures et leurs lignes"""
        ecritures = EcritureComptable.objects.all()
        
        for ecriture in ecritures:
            try:
                total_debit = ecriture.total_debit
                
                if ecriture.montant_devise != total_debit:
                    ancien_montant = ecriture.montant_devise
                    ecriture.montant_devise = total_debit
                    ecriture.save(update_fields=['montant_devise'])
                    self.stdout.write(
                        f"Montant corrigé: {ecriture.numero} - {ancien_montant} → {total_debit}"
                    )
                    
            except Exception as e:
                self.stdout.write(f"Erreur correction {ecriture.numero}: {e}")

    def equilibrer_toutes_ecritures(self):
        """Équilibre toutes les écritures qui ne le sont pas"""
        ecritures = EcritureComptable.objects.all()
        
        for ecriture in ecritures:
            try:
                if not ecriture.est_equilibree:
                    ecriture.equilibrer_ecriture()
                    self.stdout.write(
                        f"Écriture équilibrée: {ecriture.numero}"
                    )
                    
            except Exception as e:
                self.stdout.write(f"Erreur équilibrage {ecriture.numero}: {e}")

    def corriger_incoherences_factures(self):
        """Corrige les incohérences entre les factures et leurs écritures"""
        factures = FactureFournisseur.objects.filter(
            statut__in=['validee', 'payee', 'partiellement_payee']
        )
        
        for facture in factures:
            try:
                ecritures = facture.get_ecritures_comptables()
                
                for ecriture in ecritures:
                    # Vérifier que le montant de l'écriture correspond à la facture
                    if ecriture.montant_devise != facture.montant_ttc:
                        # Corriger les lignes de l'écriture
                        for ligne in ecriture.lignes.all():
                            if ligne.compte.numero == '607':  # Achats
                                if ligne.debit != facture.montant_ht:
                                    ligne.debit = facture.montant_ht
                                    ligne.save()
                            elif ligne.compte.numero == '4456':  # TVA déductible
                                if ligne.debit != facture.montant_tva:
                                    ligne.debit = facture.montant_tva
                                    ligne.save()
                            elif ligne.compte.numero == '401':  # Fournisseurs
                                if ligne.credit != facture.montant_ttc:
                                    ligne.credit = facture.montant_ttc
                                    ligne.save()
                        
                        # Recalculer le montant devise
                        ecriture.recalculer_montant_devise()
                        self.stdout.write(
                            f"Facture {facture.numero_facture} corrigée"
                        )
                        
            except Exception as e:
                self.stdout.write(f"Erreur correction facture {facture.numero_facture}: {e}")

    def supprimer_doublons(self):
        """Supprime les écritures en double"""
        from django.db.models import Count
        
        # Doublons par pièce justificative
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
            
            # Garder la première, supprimer les autres
            premiere = ecritures.first()
            for doublon_ecriture in ecritures[1:]:
                doublon_ecriture.delete()
                self.stdout.write(f"Doublon supprimé: {doublon_ecriture.numero}")

    def corriger_ecritures_anciennes(self):
        """Corrige spécifiquement les anciennes écritures problématiques"""
        corrections = [
            {'numero': 'ACH-20250910-0001', 'montant_correct': Decimal('3540.00')},
            {'numero': 'ACH-20250908-0001', 'montant_correct': Decimal('6637.50')},
            {'numero': 'ACH-20250907-0001', 'montant_correct': Decimal('4248.00')},
            {'numero': 'PAIE-2025-09-00148', 'montant_correct': Decimal('0.00')},
            {'numero': '2025-000001', 'montant_correct': Decimal('800.00')},
        ]
        
        for correction in corrections:
            try:
                ecriture = EcritureComptable.objects.get(numero=correction['numero'])
                
                # Corriger le montant devise
                if ecriture.montant_devise != correction['montant_correct']:
                    ancien_montant = ecriture.montant_devise
                    ecriture.montant_devise = correction['montant_correct']
                    ecriture.save(update_fields=['montant_devise'])
                    self.stdout.write(
                        f"Ancienne écriture corrigée: {ecriture.numero} - {ancien_montant} → {correction['montant_correct']}"
                    )
                
                # Équilibrer l'écriture
                if not ecriture.est_equilibree:
                    ecriture.equilibrer_ecriture()
                    
            except EcritureComptable.DoesNotExist:
                self.stdout.write(f"Écriture introuvable: {correction['numero']}")
            except Exception as e:
                self.stdout.write(f"Erreur correction {correction['numero']}: {e}")