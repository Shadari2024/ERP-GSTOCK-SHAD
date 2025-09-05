from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """
    Multiplies the value with the argument.
    Usage: {{ value|mul:arg }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return '' # Or handle error more explicitly if needed