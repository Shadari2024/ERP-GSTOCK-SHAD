from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
import logging

logger = logging.getLogger(__name__)

@receiver(post_migrate)
def create_bi_groups_and_permissions(sender, **kwargs):
    """Crée les groupes et permissions pour le module BI"""
    if sender.name == 'bi':
        try:
            # Créer les groupes
            group_bi_user, created = Group.objects.get_or_create(name='BI_User')
            group_bi_manager, created = Group.objects.get_or_create(name='BI_Manager')
            
            # Récupérer le content type pour les modèles BI
            from .models import KPI, Report, DataExport, DataImport
            
            content_types = ContentType.objects.filter(
                app_label='bi',
                model__in=['kpi', 'report', 'dataexport', 'dataimport', 'aiintegration']
            )
            
            # Permissions pour BI_User
            user_permissions = Permission.objects.filter(
                content_type__in=content_types,
                codename__in=[
                    'view_kpi', 'add_kpi', 'change_kpi',
                    'view_report', 'add_report', 'change_report',
                    'view_dataexport', 'add_dataexport',
                    'view_kpi_dashboard', 'export_kpi_data'
                ]
            )
            group_bi_user.permissions.set(user_permissions)
            
            # Permissions pour BI_Manager (toutes les permissions)
            manager_permissions = Permission.objects.filter(
                content_type__in=content_types
            )
            group_bi_manager.permissions.set(manager_permissions)
            
            logger.info("Groupes et permissions BI créés avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création des groupes BI: {e}")

@receiver(post_migrate)
def create_default_kpis(sender, **kwargs):
    """Crée les KPIs par défaut après la migration"""
    if sender.name == 'bi':
        try:
            from .models import KPI
            from parametres.models import Entreprise
            
            # Créer des KPIs par défaut pour chaque entreprise existante
            for entreprise in Entreprise.objects.all():
                default_kpis = [
                    {
                        'nom': _('Chiffre d\'Affaires Mensuel'),
                        'code': 'ca_mensuel',
                        'description': _('Chiffre d\'affaires total du mois en cours'),
                        'type_kpi': 'financial',
                        'formule': 'ventes__montant_total',
                        'periodicite': 'monthly',
                        'unite': '{{devise}}',
                        'cible': 1000000,
                        'seuil_alerte': 500000,
                        'module_lie': 'ventes'
                    },
                    {
                        'nom': _('Marge Brute'),
                        'code': 'marge_brute',
                        'description': _('Marge brute en pourcentage'),
                        'type_kpi': 'financial',
                        'formule': '(ventes__montant_total - achats__cout_total) / ventes__montant_total * 100',
                        'periodicite': 'monthly',
                        'unite': '%',
                        'cible': 30,
                        'seuil_alerte': 20,
                        'module_lie': 'ventes'
                    },
                    {
                        'nom': _('Rotation des Stocks'),
                        'code': 'rotation_stocks',
                        'description': _('Nombre de fois que le stock est renouvelé dans une période'),
                        'type_kpi': 'stock',
                        'formule': 'ventes__cout_des_marchandises_vendues / stock__valeur_moyenne',
                        'periodicite': 'monthly',
                        'unite': _('fois'),
                        'cible': 3,
                        'seuil_alerte': 1.5,
                        'module_lie': 'stock'
                    },
                    {
                        'nom': _('Délai Moyen de Paiement Clients'),
                        'code': 'dmp_clients',
                        'description': _('Délai moyen de paiement des clients en jours'),
                        'type_kpi': 'financial',
                        'formule': 'compta__creances_clients / ventes__montant_total_journalier',
                        'periodicite': 'monthly',
                        'unite': _('jours'),
                        'cible': 45,
                        'seuil_alerte': 60,
                        'module_lie': 'compta'
                    }
                ]
                
                for kpi_data in default_kpis:
                    KPI.objects.get_or_create(
                        code=kpi_data['code'],
                        entreprise=entreprise,
                        defaults=kpi_data
                    )
            
            logger.info("KPIs par défaut créés avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création des KPIs par défaut: {e}")