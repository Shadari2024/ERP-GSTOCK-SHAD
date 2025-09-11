# management/commands/verifier_integrite_comptable.py
from django.core.management.base import BaseCommand
from comptabilite.models import EcritureComptable, LigneEcriture
from achats.models import FactureFournisseur
from decimal import Decimal
from django.db.models import Sum, Q

class Command(BaseCommand):
    help = 'Vérifie l\'intégrité complète du système comptable'

    def handle(self, *args, **options):
        self.stdout.write("=== VÉRIFICATION DE L'INTÉGRITÉ COMPTABLE ===")
        
        # 1. Vérifier l'équilibre général
        self.verifier_equilibre_general()
        
        # 2. Vérifier les incohérences factures/écritures
        self.verifier_incoherences_factures()
        
        # 3. Vérifier les écritures non équilibrées
        self.verifier_ecritures_non_equilibrees()
        
        # 4. Vérifier les montants incohérents
        self.verifier_montants_incoherents()
        
        self.stdout.write("=== VÉRIFICATION TERMINÉE ===")

    def verifier_equilibre_general(self):
        """Vérifie l'équilibre débit/crédit global"""
        total_debit = LigneEcriture.objects.aggregate(
            total=Sum('debit')
        )['total'] or Decimal('0.00')
        
        total_credit = LigneEcriture.objects.aggregate(
            total=Sum('credit')
        )['total'] or Decimal('0.00')
        
        if total_debit == total_credit:
            self.stdout.write(self.style.SUCCESS(
                f"✓ Équilibre global: {total_debit} = {total_credit}"
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f"✗ Déséquilibre global: {total_debit} ≠ {total_credit}"
            ))

    def verifier_incoherences_factures(self):
        """Vérifie les incohérences entre factures et écritures"""
        factures = FactureFournisseur.objects.filter(
            statut__in=['validee', 'payee', 'partiellement_payee']
        )
        
        incohérences = 0
        
        for facture in factures:
            ecritures = facture.get_ecritures_comptables()
            
            for ecriture in ecritures:
                if ecriture.montant_devise != facture.montant_ttc:
                    incohérences += 1
                    self.stdout.write(self.style.WARNING(
                        f"Incohérence: {facture.numero_facture} - "
                        f"Écriture: {ecriture.montant_devise} ≠ Facture: {facture.montant_ttc}"
                    ))
        
        if incohérences == 0:
            self.stdout.write(self.style.SUCCESS("✓ Aucune incohérence facture/écriture"))

    def verifier_ecritures_non_equilibrees(self):
        """Vérifie les écritures non équilibrées"""
        ecritures_non_equilibrees = []
        
        for ecriture in EcritureComptable.objects.all():
            if not ecriture.est_equilibree:
                ecritures_non_equilibrees.append(ecriture.numero)
        
        if ecritures_non_equilibrees:
            self.stdout.write(self.style.ERROR(
                f"✗ Écritures non équilibrées: {len(ecritures_non_equilibrees)}"
            ))
            for numero in ecritures_non_equilibrees[:5]:  # Afficher les 5 premières
                self.stdout.write(f"  - {numero}")
        else:
            self.stdout.write(self.style.SUCCESS("✓ Toutes les écritures sont équilibrées"))

    def verifier_montants_incoherents(self):
        """Vérifie les incohérences de montants"""
        incohérences = []
        
        for ecriture in EcritureComptable.objects.all():
            total_debit = ecriture.total_debit
            if ecriture.montant_devise != total_debit:
                incohérences.append(
                    f"{ecriture.numero}: {ecriture.montant_devise} ≠ {total_debit}"
                )
        
        if incohérences:
            self.stdout.write(self.style.ERROR(
                f"✗ Incohérences de montants: {len(incohérences)}"
            ))
            for incohérence in incohérences[:5]:  # Afficher les 5 premières
                self.stdout.write(f"  - {incohérence}")
        else:
            self.stdout.write(self.style.SUCCESS("✓ Aucune incohérence de montants"))