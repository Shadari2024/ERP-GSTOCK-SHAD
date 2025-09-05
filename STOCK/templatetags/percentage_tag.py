from django import template

register = template.Library()

@register.filter
def percentage(value, decimals=2):
    try:
        value = float(value) * 100
        return f"{value:.{decimals}f}%"
    except (ValueError, TypeError):
        return ""

