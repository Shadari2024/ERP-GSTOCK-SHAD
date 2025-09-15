import os
from django.core.management.base import BaseCommand
from django.conf import settings
import cloudinary.uploader

class Command(BaseCommand):
    help = "Upload tous les fichiers du dossier MEDIA_ROOT vers Cloudinary"

    def handle(self, *args, **kwargs):
        media_path = settings.MEDIA_ROOT

        if not os.path.exists(media_path):
            self.stdout.write(self.style.ERROR("❌ Le dossier MEDIA_ROOT n'existe pas"))
            return

        self.stdout.write(self.style.WARNING(f"📂 Dossier media : {media_path}"))

        for root, dirs, files in os.walk(media_path):
            for file in files:
                file_path = os.path.join(root, file)

                try:
                    result = cloudinary.uploader.upload(file_path, folder="django_media")
                    self.stdout.write(self.style.SUCCESS(
                        f"✅ {file_path} → {result['secure_url']}"
                    ))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f"❌ Erreur upload {file_path} : {e}"
                    ))
