    
from django import template
from django.db.models import Sum

register = template.Library()

@register.filter
def sum_attr(queryset, attr):
    """Somme les valeurs d'un attribut d'un queryset"""
    return sum(getattr(item, attr, 0) or 0 for item in queryset)