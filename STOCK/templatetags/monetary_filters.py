from django import template

register = template.Library()

@register.filter
def diviser(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return None
