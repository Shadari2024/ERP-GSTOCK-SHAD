import builtins
from django import template

register = template.Library()

@register.filter
def abs(value):
    try:
        return builtins.abs(value)  # 👈 on appelle la vraie fonction Python ici
    except (TypeError, ValueError):
        return value
