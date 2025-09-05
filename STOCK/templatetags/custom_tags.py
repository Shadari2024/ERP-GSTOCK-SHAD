# STOCK/templatetags/custom_tags.py
from django import template
from urllib.parse import urlencode

register = template.Library()

@register.simple_tag
def param_replace(request, **kwargs):
    """
    Encodes les paramètres URL tout en conservant ceux existants
    """
    params = request.GET.copy()
    for key, value in kwargs.items():
        params[key] = value
    return params.urlencode()




