# ton_app/templatetags/comptoir_tags.py
from django import template

register = template.Library()

@register.filter
def example(value):
    return f"Exemple: {value}"
