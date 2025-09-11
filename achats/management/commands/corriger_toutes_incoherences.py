# management/commands/corriger_toutes_incoherences.py
from django.core.management.base import BaseCommand
from comptabilite.models import EcritureComptable, LigneEcriture, PlanComptableOHADA
from achats.models import FactureFournisseur
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Corrige toutes les incohérences comptables de manière définitive'

    def handle(self, *args, **options):
        self.stdout.write("=== CORRECTION DÉFINITIVE DES INCOHÉRENCES COMPTABLES ===")
        
        # 1. S'assurer que le compte de régularisation existe
        self.creer_compte_regularisation()
        
        # 2. Corriger les écritures spécifiques problématiques
        self.corriger_ecritures_specifiques()
        
        # 3. Équilibrer toutes les écritures
        self.equilibrer_toutes_ecritures()
        
        # 4. Corriger les incohérences facture/écriture
        self.corriger_incoherences_factures()
        
        # 5. Recalculer tous les montants devise
        self.recalculer_tous_montants_devise()
        
        self.stdout.write(self.style.SUCCESS("=== CORRECTION DÉFINITIVE TERMINÉE ==="))

    def creer_compte_regularisation(self):
        """Crée le compte de régularisation 471 pour toutes les entreprises"""
        from parametres.models import Entreprise
        
        for entreprise in Entreprise.objects.all():
            try:
                PlanComptableOHADA.objects.get_or_create(
                    numero='471',
                    entreprise=entreprise,
                    defaults={
                        'classe': '4',
                        'intitule': 'Compte de régularisation',
                        'type_compte': 'passif',
                        'description': 'Compte utilisé pour équilibrer les écritures comptables'
                    }
                )
                self.stdout.write(f"Compte 471 créé pour {entreprise.nom}")
            except Exception as e:
                self.stdout.write(f"Erreur création compte 471 pour {entreprise.nom}: {e}")

    def corriger_ecritures_specifiques(self):
        """Corrige les écritures spécifiques identifiées comme problématiques"""
        corrections = {
            'CA-20250911-20250910230203': {
                'montant_correct': Decimal('3.48'),
                'lignes_correction': {
                    '401': {'debit': Decimal('3.48'), 'credit': Decimal('0.00')},
                    '53': {'debit': Decimal('0.00'), 'credit': Decimal('3.48')}
                }
            },
            'ACH-20250910-0001': {
                'montant_correct': Decimal('160.00'),
                'lignes_correction': {
                    '607': {'debit': Decimal('160.00'), 'credit': Decimal('0.00')},
                    '401': {'debit': Decimal('0.00'), 'credit': Decimal('160.00')}
                }
            },
            'ACH-20250908-0001': {
                'montant_correct': Decimal('380.00'),
                'lignes_correction': {
                    '607': {'debit': Decimal('380.00'), 'credit': Decimal('0.00')},
                    '401': {'debit': Decimal('0.00'), 'credit': Decimal('380.00')}
                }
            },
            'ACH-20250907-0001': {
                'montant_correct': Decimal('640.00'),
                'lignes_correction': {
                    '607': {'debit': Decimal('640.00'), 'credit': Decimal('0.00')},
                    '401': {'debit': Decimal('0.00'), 'credit': Decimal('640.00')}
                }
            }
        }
        
        for numero_ecriture, correction in corrections.items():
            try:
                ecriture = EcritureComptable.objects.get(numero=numero_ecriture)
                
                # Corriger les lignes
                for compte_numero, valeurs in correction['lignes_correction'].items():
                    ligne = ecriture.lignes.filter(compte__numero=compte_numero).first()
                    if ligne:
                        ligne.debit = valeurs['debit']
                        ligne.credit = valeurs['credit']
                        ligne.save()
                
                # Corriger le montant devise
                ecriture.montant_devise = correction['montant_correct']
                ecriture.save(update_fields=['montant_devise'])
                
                self.stdout.write(f"Écriture {numero_ecriture} corrigée")
                
            except EcritureComptable.DoesNotExist:
                self.stdout.write(f"Écriture introuvable: {numero_ecriture}")
            except Exception as e:
                self.stdout.write(f"Erreur correction {numero_ecriture}: {e}")

    def equilibrer_toutes_ecritures(self):
        """Équilibre toutes les écritures"""
        for ecriture in EcritureComptable.objects.all():
            try:
                if not ecriture.est_equilibree:
                    ecriture.equilibrer_ecriture()
                    self.stdout.write(f"Écriture équilibrée: {ecriture.numero}")
            except Exception as e:
                self.stdout.write(f"Erreur équilibrage {ecriture.numero}: {e}")

    def corriger_incoherences_factures(self):
        """Corrige les incohérences entre factures et écritures"""
        for facture in FactureFournisseur.objects.all():
            try:
                for ecriture in facture.get_ecritures_comptables():
                    if ecriture.montant_devise != facture.montant_ttc:
                        # Mettre à jour le montant de l'écriture
                        ecriture.montant_devise = facture.montant_ttc
                        ecriture.save(update_fields=['montant_devise'])
                        self.stdout.write(f"Facture {facture.numero_facture} synchronisée")
            except Exception as e:
                self.stdout.write(f"Erreur synchronisation facture {facture.numero_facture}: {e}")

    def recalculer_tous_montants_devise(self):
        """Recalcule tous les montants devise basés sur les lignes"""
        for ecriture in EcritureComptable.objects.all():
            try:
                ecriture.recalculer_montant_devise()
            except Exception as e:
                self.stdout.write(f"Erreur recalcul {ecriture.numero}: {e}")