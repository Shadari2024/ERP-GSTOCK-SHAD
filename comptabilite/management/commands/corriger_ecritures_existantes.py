# management/commands/corriger_ecritures_existantes.py
from django.core.management.base import BaseCommand
from comptabilite.models import EcritureComptable, LigneEcriture
from decimal import Decimal

class Command(BaseCommand):
    help = 'Corrige les écritures comptables existantes avec des problèmes'

    def handle(self, *args, **options):
        self.stdout.write("=== CORRECTION DES ÉCRITURES EXISTANTES ===")
        
        # 1. Corriger les écritures sans numéro
        ecritures_sans_numero = EcritureComptable.objects.filter(numero__isnull=True) | EcritureComptable.objects.filter(numero='')
        
        self.stdout.write(f"Écritures sans numéro trouvées: {ecritures_sans_numero.count()}")
        
        for ecriture in ecritures_sans_numero:
            ancien_numero = ecriture.numero
            ecriture.numero = ecriture.generate_numero_unique()
            ecriture.save()
            self.stdout.write(f"  → {ancien_numero} → {ecriture.numero}")
        
        # 2. Corriger les incohérences de montant_devise
        ecritures_problemes = []
        for ecriture in EcritureComptable.objects.all():
            total_debit = sum(ligne.debit for ligne in ecriture.lignes.all())
            if abs(ecriture.montant_devise - total_debit) > Decimal('0.01'):
                ecritures_problemes.append(ecriture)
        
        self.stdout.write(f"Écritures avec incohérence de montant: {len(ecritures_problemes)}")
        
        for ecriture in ecritures_problemes:
            ancien_montant = ecriture.montant_devise
            total_debit = sum(ligne.debit for ligne in ecriture.lignes.all())
            ecriture.montant_devise = total_debit
            ecriture.save(update_fields=['montant_devise'])
            self.stdout.write(f"  → {ecriture.numero}: {ancien_montant} → {total_debit}")
        
        self.stdout.write("✓ Correction terminée")