# management/commands/init_securite.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from security.models import UtilisateurPersonnalise  # Remplace par ton nom d’app

class Command(BaseCommand):
    help = 'Initialise les groupes et permissions de base pour le système de sécurité'
    
    def handle(self, *args, **options):
        self.stdout.write("🔐 Initialisation des groupes et permissions...")

        # Définir les rôles et leurs permissions
        roles_permissions = {
            'ADMIN': Permission.objects.all(),
            'MANAGER': Permission.objects.filter(codename__in=[
                'view_client', 'view_commande', 'view_produit', 'view_rapport'
            ]),
            'CAISSIER': Permission.objects.filter(codename__in=[
                'view_tresorerie', 'manage_tresorerie'
            ]),
            'VENDEUR': Permission.objects.filter(codename__in=[
                'view_client', 'add_commande', 'view_commande', 'effectuer_vente'
            ]),
            'STOCK': Permission.objects.filter(codename__in=[
                'view_produit', 'add_produit', 'change_produit', 'view_achat', 'add_achat'
            ]),
        }

        for role, permissions in roles_permissions.items():
            group, created = Group.objects.get_or_create(name=role)
            group.permissions.set(permissions)
            self.stdout.write(self.style.SUCCESS(f"Groupe {'créé' if created else 'mis à jour'} : {role}"))

        self.stdout.write(self.style.SUCCESS("✅ Configuration de sécurité initialisée avec succès"))
