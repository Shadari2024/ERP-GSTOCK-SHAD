from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def abs(value):
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return ''

@register.filter(name='get_item')
def get_item(dictionary, key):
    return dictionary.get(key, '')



from django import template
from django.core.exceptions import ValidationError
from ..models import TauxChange

register = template.Library()

@register.filter(name='convertir_devise')
def convertir_devise(montant, devise_cible):
    try:
        # Ici vous devrez récupérer la devise source (peut-être via le contexte)
        # Ceci est une implémentation simplifiée
        devise_source = 'USD'  # À remplacer par la devise principale de l'entreprise
        if devise_source == devise_cible:
            return montant
        
        taux = TauxChange.get_taux(devise_source, devise_cible)
        if taux is None:
            return montant
        return float(montant) * float(taux)
    except (ValueError, TypeError, ValidationError):
        return montant