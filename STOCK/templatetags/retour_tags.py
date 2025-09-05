from django import template

register = template.Library()

@register.filter
def get_status_badge_class(statut):
    mapping = {
        'en_attente': 'warning',
        'recu': 'primary',
        'traite': 'info',
        'rembourse': 'success',
        'annule': 'secondary',
    }
    return mapping.get(statut, 'dark')
