# Créer un fichier templatetags/custom_filters.py dans votre app
from django import template
from django.contrib.humanize.templatetags.humanize import intcomma
from decimal import Decimal

register = template.Library()

@register.filter
def french_floatformat(value, decimal_places=2):
    """Formatte un nombre avec des espaces comme séparateurs de milliers et une virgule comme séparateur décimal"""
    try:
        if value is None:
            return "0,00"
        
        # Convertir en Decimal pour une manipulation précise
        if isinstance(value, (int, float, str)):
            value = Decimal(str(value))
        
        # Formater avec 2 décimales
        formatted = f"{value:,.{decimal_places}f}"
        
        # Remplacer les séparateurs pour le format français
        formatted = formatted.replace(",", " ").replace(".", ",")
        
        return formatted
    except (ValueError, TypeError):
        return "0,00"

@register.filter
def input_number_format(value):
    """Formatte un nombre pour l'utilisation dans les inputs de type number"""
    try:
        if value is None:
            return "0.00"
        
        # Convertir en Decimal
        if isinstance(value, (int, float, str)):
            value = Decimal(str(value))
        
        # Format compatible avec input type="number"
        return f"{value:.2f}"
    except (ValueError, TypeError):
        return "0.00"