# comptabilite/templatetags/math_filters.py

from django import template

register = template.Library()

@register.filter
def absolute_value(value):
    """Returns the absolute value of a number, correctly."""
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return value

@register.filter
def div(value, arg):
    """Divides the value by the arg."""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return None

@register.filter
def multiply(value, arg):
    """Multiplies the value by the arg."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return None