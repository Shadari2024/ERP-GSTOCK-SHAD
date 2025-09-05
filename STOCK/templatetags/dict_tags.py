
from django import template

register = template.Library()

@register.filter(name='get_dict_item')
def get_dict_item(dictionary, key):
    """Récupère un élément d'un dictionnaire par sa clé"""
    return dictionary.get(key, '')



@register.filter
def get_dict_item(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''