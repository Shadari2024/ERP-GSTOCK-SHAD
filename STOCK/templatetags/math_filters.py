from django import template
import math

register = template.Library()

@register.filter(name='subtract')
def subtract(value, arg):
    return value - arg



@register.filter
def multiply(value, arg):
    """Multiplies the value by the arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
    
    
    
    
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, '')



@register.filter
def div(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return ''
    
    
@register.filter
def absolute(value):
    try:
        return math.fabs(float(value))
    except (ValueError, TypeError):
        return value
    
    
    
@register.filter
def abs(value):
    """Safe absolute value filter that won't cause recursion"""
    try:
        return math.fabs(float(value))
    except (ValueError, TypeError):
        return value
    
    
    
    
# Dans votre fichier templatetags/custom_tags.py
@register.filter
def get_taux(taux_change, devise_cible):
    try:
        return taux_change.get(devise_source=devise_cible).taux
    except:
        return 1

@register.filter
def get_symbole(parametres, devise):
    return parametres.format_devise(1, devise).split(' ')[0]