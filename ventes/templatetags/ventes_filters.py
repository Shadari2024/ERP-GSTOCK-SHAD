# ventes/templatetags/ventes_filters.py
from django import template
from django.db.models import Sum

register = template.Library()

@register.filter
def sum_paiements(queryset):
    """Calcule la somme des montants de paiement"""
    return sum(item.montant for item in queryset)

@register.filter
def sum_field(queryset, field_name):
    """Calcule la somme d'un champ spécifique dans un queryset"""
    return sum(getattr(item, field_name, 0) for item in queryset)






# ventes/templatetags/ventes_filters.py
from django import template
from django.db.models import Q

register = template.Library()

@register.filter
def filter_mode_paiement(queryset, mode):
    """Filtre les paiements par mode"""
    return queryset.filter(mode_paiement=mode)

@register.filter
def exclude_mode_paiement(queryset, mode):
    """Exclut les paiements par mode"""
    return queryset.exclude(mode_paiement=mode)

@register.filter
def subtract(value, arg):
    """Soustrait deux valeurs"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0
    
    
    

@register.filter
def div(value, arg):
    """
    Divise la valeur par l'argument.
    Exemple : {{ value|div:arg }}
    """
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return None

@register.filter
def mul(value, arg):
    """
    Multiplie la valeur par l'argument.
    Exemple : {{ value|mul:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, ZeroDivisionError):
        return None