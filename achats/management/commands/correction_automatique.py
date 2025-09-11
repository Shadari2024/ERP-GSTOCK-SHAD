# management/commands/correction_automatique.py
from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Exécute toutes les corrections comptables automatiquement'

    def handle(self, *args, **options):
        self.stdout.write("=== LANCEMENT DES CORRECTIONS AUTOMATIQUES ===")
        
        # 1. Correction des incohérences
        self.stdout.write("1. Correction des incohérences...")
        call_command('corriger_incoherences_comptables')
        
        # 2. Vérification de l'intégrité
        self.stdout.write("2. Vérification de l'intégrité...")
        call_command('verifier_integrite_comptable')
        
        # 3. Correction des écritures anciennes
        self.stdout.write("3. Correction des écritures anciennes...")
        call_command('corriger_ecritures_anciennes')
        
        self.stdout.write(self.style.SUCCESS("=== CORRECTIONS AUTOMATIQUES TERMINÉES ==="))