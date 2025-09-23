from django import template

register = template.Library()

@register.filter
def div(value, arg):
    try:
        return float(value) / float(arg) if arg else None
    except (ValueError, ZeroDivisionError):
        return None


@register.filter
def filter_classe(balance_data, classe):
    """Filtre les comptes par classe (1 à 7)"""
    return [data for data in balance_data if str(data['compte'].numero).startswith(str(classe))]