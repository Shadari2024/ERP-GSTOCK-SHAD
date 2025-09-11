# management/commands/surveillance_ecritures.py
from django.core.management.base import BaseCommand
from comptabilite.models import EcritureComptable
from django.db.models import Sum
from decimal import Decimal

class Command(BaseCommand):
    help = 'Surveille les incohérences dans les écritures comptables'

    def handle(self, *args, **options):
        incohérences = []
        
        # Vérifier les écritures avec montant 0
        ecritures_zero = EcritureComptable.objects.filter(montant_devise=0)
        if ecritures_zero.exists():
            incohérences.append(f"{ecritures_zero.count()} écritures avec montant 0")
        
        # Vérifier les incohérences débit/crédit
        for ecriture in EcritureComptable.objects.all():
            total_debit = ecriture.lignes.aggregate(total=Sum('debit'))['total'] or Decimal('0')
            total_credit = ecriture.lignes.aggregate(total=Sum('credit'))['total'] or Decimal('0')
            
            if total_debit != total_credit:
                incohérences.append(f"Écriture {ecriture.numero}: débit {total_debit} ≠ crédit {total_credit}")
            
            if ecriture.montant_devise != total_debit:
                incohérences.append(f"Écriture {ecriture.numero}: montant {ecriture.montant_devise} ≠ débit {total_debit}")
        
        if incohérences:
            self.stdout.write(self.style.ERROR("Incohérences détectées:"))
            for incohérence in incohérences:
                self.stdout.write(f"  - {incohérence}")
        else:
            self.stdout.write(self.style.SUCCESS("Aucune incohérence détectée"))