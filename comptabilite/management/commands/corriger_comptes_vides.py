# management/commands/corriger_comptes_vides.py
from django.core.management.base import BaseCommand
from comptabilite.models import PlanComptableOHADA
from django.db import transaction

class Command(BaseCommand):
    help = 'Corrige les comptes comptables avec des numéros vides'

    def handle(self, *args, **options):
        self.stdout.write("=== CORRECTION DES COMPTES AVEC NUMÉROS VIDES ===")
        
        # Trouver les comptes avec des numéros vides
        comptes_vides = PlanComptableOHADA.objects.filter(numero__isnull=True) | PlanComptableOHADA.objects.filter(numero='')
        
        self.stdout.write(f"Comptes avec numéros vides trouvés: {comptes_vides.count()}")
        
        for compte in comptes_vides:
            self.stdout.write(f"Correction du compte: {compte.intitule} (ID: {compte.id})")
            
            # Assigner un numéro temporaire basé sur l'ID
            nouveau_numero = f"TEMP-{compte.id:04d}"
            compte.numero = nouveau_numero
            compte.save()
            
            self.stdout.write(f"  → Numéro assigné: {nouveau_numero}")
        
        self.stdout.write("✓ Correction terminée")