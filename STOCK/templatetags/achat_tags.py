# STOCK/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Récupère un élément d'un dictionnaire par sa clé"""
    return dictionary.get(key, '')