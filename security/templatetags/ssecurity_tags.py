from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    """Vérifie si l'utilisateur appartient à un groupe spécifique"""
    return user.groups.filter(name=group_name).exists() if user.is_authenticated else False

@register.filter(name='type_utilisateur_color')
def type_utilisateur_color(value):
    """Retourne une classe CSS selon le type d'utilisateur"""
    color_map = {
        'admin': 'primary',
        'manager': 'success',
        'vendeur': 'info',
        'default': 'secondary'
    }
    return color_map.get(str(value).lower(), color_map['default'])

@register.filter(name='niveau_acces_color')
def niveau_acces_color(niveau):
    """Retourne une couleur Bootstrap en fonction du niveau d'accès"""
    colors = {
        1: 'secondary',    # Lecture seule
        2: 'info',        # Édition limitée
        3: 'primary',     # Édition complète
        4: 'warning',     # Administration
        5: 'danger'       # Super admin
    }
    return colors.get(niveau, 'light')

@register.filter(name='action_color')
def action_color(action):
    """Retourne une couleur Bootstrap en fonction du type d'action"""
    color_map = {
        'connexion': 'success',
        'deconnexion': 'danger',
        'creation': 'primary',
        'modification': 'warning',
        'suppression': 'dark',
        'default': 'info'
    }
    return color_map.get(action.lower(), color_map['default'])


@register.filter(name='role_badge_color')
def role_badge_color(role):
    color_map = {
        'ADMIN': 'danger',
        'MANAGER': 'warning',
        'CAISSIER': 'info',
        'VENDEUR': 'primary',
        'STOCK': 'success'
    }
    return color_map.get(role, 'secondary')

# Your other filters can remain as they are
@register.filter(name='has_group')
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists() if user.is_authenticated else False

@register.filter(name='action_icon')
def action_icon(action_type):
    icons = {
        'CONNEXION': 'fa-sign-in-alt',
        'DECONNEXION': 'fa-sign-out-alt',
        'CREATION': 'fa-plus-circle',
        'MODIFICATION': 'fa-edit',
        'SUPPRESSION': 'fa-trash-alt',
        'ACCES': 'fa-eye'
    }
    return icons.get(action_type, 'fa-info-circle')




@register.filter
def format_app_name(value):
    """Formate les noms d'applications pour l'affichage"""
    return value.replace('_', ' ').title()


@register.filter(name='action_badge_color')
def action_badge_color(action):
    """Retourne une couleur Bootstrap en fonction du type d'action"""
    color_map = {
        'CONNEXION': 'success',
        'DECONNEXION': 'danger',
        'CREATION': 'primary',
        'MODIFICATION': 'warning',
        'SUPPRESSION': 'dark',
        'default': 'info'
    }
    return color_map.get(str(action).upper(), color_map['default'])