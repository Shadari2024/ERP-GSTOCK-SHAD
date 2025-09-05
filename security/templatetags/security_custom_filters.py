from django import template
from django.contrib.auth.models import Group

register = template.Library()

@register.filter(name='has_group')
def has_group(user, group_name):
    """Vérifie si l'utilisateur appartient à un groupe"""
    return user.groups.filter(name=group_name).exists() if user.is_authenticated else False

@register.filter(name='type_utilisateur_color')
def type_utilisateur_color(value):
    """Retourne une classe CSS selon le type d'utilisateur"""
    color_map = {
        'admin': 'bg-primary',
        'manager': 'bg-success',
        'vendeur': 'bg-info'
    }
    return color_map.get(str(value).lower(), 'bg-secondary')




@register.filter
def type_utilisateur_color(value):
    colors = {
        'admin': 'primary',
        'manager': 'info',
        'employee': 'success',
        'client': 'secondary',
        # Ajoutez d'autres types selon vos besoins
    }
    return colors.get(value.lower(), 'secondary')



@register.filter
def add_class(field, css_class):
    """Ajoute une classe CSS à un champ de formulaire"""
    return field.as_widget(attrs={"class": css_class})


import os



@register.filter
def basename(value):
    
    """Retourne le nom du fichier sans le chemin"""
    return os.path.basename(str(value))


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)



@register.filter
def devis_status_color(statut):
    colors = {
        'brouillon': 'info',
        'envoye': 'warning',
        'accepte': 'success',
        'refuse': 'danger',
        'annule': 'secondary'
    }
    return colors.get(statut, 'secondary')

@register.filter
def commande_status_color(statut):
    colors = {
        'brouillon': 'info',
        'Confirmee': 'primary',
        'expedie': 'warning',
        'livre': 'success',
        'annule': 'danger'
    }
    return colors.get(statut, 'secondary')

@register.filter
def facture_status_color(statut):
    colors = {
        'brouillon': 'info',
        'validee': 'warning',
        'paye_partiel': 'primary',
        'paye': 'success',
        'annulee': 'danger'
    }
    return colors.get(statut, 'secondary')