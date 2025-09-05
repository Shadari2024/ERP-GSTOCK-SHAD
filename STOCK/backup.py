import os
import zipfile
import logging
from datetime import datetime
from django.conf import settings
from django.core.management import call_command
from django.contrib.auth.models import User
from STOCK.models import Notification

logger = logging.getLogger(__name__)

class BackupManager:
    
    @staticmethod
    def create_backup(manual_request=False):
        """Version robuste avec vérification étape par étape"""
        try:
            backup_dir = os.path.join(settings.BASE_DIR, 'backups')
            
            # 1. Vérification/Création du dossier
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
                logger.info(f"Dossier créé : {backup_dir}")
            
            # Test d'écriture
            test_file = os.path.join(backup_dir, 'test_write.tmp')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            
            # 2. Création du fichier de sauvegarde
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{timestamp}.zip"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            logger.info(f"Création de : {backup_path}")
            
            # 3. Sauvegarde DB
            db_file = f"db_backup_{timestamp}.json"
            db_path = os.path.join(settings.BASE_DIR, db_file)
            
            excluded_models = [
                'contenttypes.ContentType',
                'auth.Permission',
                'sessions.Session',
                'admin.LogEntry',
                'django_apscheduler.DjangoJobExecution'
            ]
            
            call_command('dumpdata', 
                       exclude=excluded_models,
                       indent=2,
                       output=db_path)
            
            # Vérification fichier DB
            if not os.path.exists(db_path):
                raise Exception("Échec création dump DB")
            
            # 4. Création ZIP
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Ajout DB
                zipf.write(db_path, os.path.basename(db_path))
                
                # Ajout MEDIA
                if hasattr(settings, 'MEDIA_ROOT'):
                    media_root = settings.MEDIA_ROOT
                    if os.path.exists(media_root):
                        for root, dirs, files in os.walk(media_root):
                            for file in files:
                                full_path = os.path.join(root, file)
                                arcname = os.path.relpath(full_path, media_root)
                                zipf.write(full_path, f"media/{arcname}")
            
            # 5. Nettoyage
            os.remove(db_path)
            
            # Vérification finale
            if not os.path.exists(backup_path):
                raise Exception("Le fichier ZIP final n'a pas été créé")
            
            logger.success(f"Sauvegarde réussie : {backup_path} ({os.path.getsize(backup_path)} octets)")
            return backup_path
            
        except Exception as e:
            logger.error(f"ERREUR Sauvegarde : {str(e)}", exc_info=True)
            # Nettoyage en cas d'échec
            if 'db_path' in locals() and os.path.exists(db_path):
                os.remove(db_path)
            if 'backup_path' in locals() and os.path.exists(backup_path):
                os.remove(backup_path)
            raise