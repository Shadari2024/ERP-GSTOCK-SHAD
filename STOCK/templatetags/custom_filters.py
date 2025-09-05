# STOCK/templatetags/custom_filters.py
from django import template
from urllib.parse import urlencode
from django.http import QueryDict

register = template.Library()

@register.simple_tag
def param_replace(request, **kwargs):
    """
    Template tag pour conserver les paramètres GET existants tout en en modifiant certains.
    """
    params = request.GET.copy()
    for key, value in kwargs.items():
        params[key] = value
    return urlencode(params)

from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def percentage(value, total):
    try:
        value = float(value)
        total = float(total)
        if total == 0:
            return "0%"
        return "{:.2f}%".format((value / total) * 100)
    except (ValueError, TypeError):
        return ''
    
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

from django import template
from urllib.parse import urlencode

register = template.Library()

@register.simple_tag
def param_replace(request, **kwargs):
    """
    Preserve query parameters while replacing others
    """
    params = request.GET.copy()
    for key, value in kwargs.items():
        params[key] = value
    return params.urlencode()



from django import template
from urllib.parse import urlencode

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Permet d'accéder à une valeur de dictionnaire dans un template"""
    return dictionary.get(key, '')

@register.simple_tag
def param_replace(request, **kwargs):
    """Préserve les paramètres de requête tout en en remplaçant certains"""
    params = request.GET.copy()
    for key, value in kwargs.items():
        params[key] = value
    return params.urlencode()


# STOCK/templatetags/custom_filters.py
from django import template
from decimal import Decimal

register = template.Library()




from django import template

register = template.Library()

@register.filter
def format_devise(value, param):
    return param.format_devise(value, param.devise_principale)






register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(str(key))

# STOCK/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter(name='div')
def div(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0  # ou None selon votre besoin
    