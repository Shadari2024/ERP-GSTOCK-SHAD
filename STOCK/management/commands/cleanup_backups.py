import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Supprime les anciennes sauvegardes si leur nombre dépasse la limite définie'

    def handle(self, *args, **options):
        # Vérifier les constantes nécessaires
        backup_dir = getattr(settings, 'BACKUP_DIR', os.path.join(settings.BASE_DIR, 'backups'))
        max_backups = getattr(settings, 'MAX_BACKUP_FILES', 5)

        if not os.path.exists(backup_dir):
            self.stdout.write(self.style.WARNING(f"Dossier de sauvegarde non trouvé : {backup_dir}"))
            return

        backups = []
        for filename in os.listdir(backup_dir):
            if filename.startswith('backup_') and filename.endswith('.zip'):
                filepath = os.path.join(backup_dir, filename)
                try:
                    mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    backups.append((mtime, filepath))
                except Exception as e:
                    self.stderr.write(f"Erreur d'accès à {filepath}: {str(e)}")

        backups.sort()  # plus anciens d'abord

        excess = len(backups) - max_backups
        if excess > 0:
            self.stdout.write(f"{excess} sauvegarde(s) en trop. Suppression en cours...")
            for mtime, filepath in backups[:excess]:
                try:
                    os.remove(filepath)
                    self.stdout.write(self.style.SUCCESS(f"Supprimé : {filepath}"))
                except Exception as e:
                    self.stderr.write(self.style.ERROR(f"Erreur de suppression {filepath}: {str(e)}"))
        else:
            self.stdout.write("Aucune sauvegarde à supprimer.")
