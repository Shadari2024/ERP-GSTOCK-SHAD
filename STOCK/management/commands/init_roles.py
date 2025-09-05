# gestion/management/commands/init_roles.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from STOCK.models import Commande, Produit, ClotureCaisse

class Command(BaseCommand):
   

    def handle(self, *args, **kwargs):
        # Crée les groupes
        admin, _ = Group.objects.get_or_create(name='Admin')
        caissier, _ = Group.objects.get_or_create(name='Caissier')
        stock, _ = Group.objects.get_or_create(name='Stock')

        # Permissions globales
        all_perms = Permission.objects.all()
        admin.permissions.set(all_perms)

        # Caissier : peut vendre, voir ses commandes
        caissier_perms = Permission.objects.filter(
            content_type__model__in=['commande', 'cloturecaisse']
        )
        caissier.permissions.set(caissier_perms)

        # Responsable Stock : accès aux produits
        stock_perms = Permission.objects.filter(
            content_type__model='produit'
        )
        stock.permissions.set(stock_perms)

        self.stdout.write(self.style.SUCCESS("Groupes et permissions créés avec succès."))

