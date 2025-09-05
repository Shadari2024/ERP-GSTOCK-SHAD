from django.core.management.base import BaseCommand
from django.conf import settings
from parametres.models import Module

class Command(BaseCommand):
    help = 'Synchronise les modules avec les applications installées'

    def handle(self, *args, **options):
        installed_apps = [app.split('.')[0] for app in settings.INSTALLED_APPS 
                        if not app.startswith('django.')]
        
        created_count = 0
        for app in installed_apps:
            module, created = Module.objects.get_or_create(
                code=app,
                defaults={
                    'nom': app.capitalize(),
                    'categorie': 'STOCK' if app == 'STOCK' else 'PARAMETRAGE',
                    'actif_par_defaut': True,
                    'ordre_affichage': 10
                }
            )
            if created:
                created_count += 1
                self.stdout.write(f"Créé module pour {app}")
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Synchronisation terminée. {created_count} nouveaux modules créés."
            )
        )