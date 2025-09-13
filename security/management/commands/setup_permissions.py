# management/commands/setup_permissions.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.apps import apps

class Command(BaseCommand):
    help = 'Setup default groups and permissions for production'

    def handle(self, *args, **options):
        self.stdout.write('Setting up default permissions...')
        
        # Créer ou mettre à jour les groupes
        manager_group, created = Group.objects.get_or_create(name='Manager')
        vendeur_group, created = Group.objects.get_or_create(name='Vendeur')
        caissier_group, created = Group.objects.get_or_create(name='Caissier')
        stock_group, created = Group.objects.get_or_create(name='Stock')
        
        # Assigner les permissions au groupe Manager
        manager_permissions = [
            'view_produit', 'add_produit', 'change_produit',  # STOCK
            'view_client', 'add_client', 'change_client',     # STOCK
            'view_categorie', 'add_categorie', 'change_categorie',  # STOCK
            'acces_dashboard', 'voir_statistiques',           # security
            'gerer_stock', 'effectuer_vente',                 # security
        ]
        
        for perm_codename in manager_permissions:
            try:
                # Essayer de trouver la permission
                if '.' in perm_codename:
                    app_label, codename = perm_codename.split('.')
                    perm = Permission.objects.get(content_type__app_label=app_label, codename=codename)
                else:
                    # Chercher dans toutes les apps
                    perm = Permission.objects.get(codename=perm_codename)
                
                manager_group.permissions.add(perm)
                self.stdout.write(f'Added {perm_codename} to Manager group')
            except Permission.DoesNotExist:
                self.stdout.write(f'Warning: Permission {perm_codename} not found')
        
        self.stdout.write('✅ Default permissions setup completed!')