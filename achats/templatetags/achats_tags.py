from django import template
from achats.models import CommandeAchat

register = template.Library()

@register.filter
def get_statut_display(statut):
    return dict(CommandeAchat.STATUT_CHOICES).get(statut, statut)

@register.filter
def get_statut_color(statut):
    colors = {
        'brouillon': 'secondary',
        'envoyee': 'info',
        'recue': 'primary',
        'partiellement_livree': 'warning',
        'livree': 'success',
        'annulee': 'danger',
    }
    return colors.get(statut, 'secondary')

@register.filter
def get_statut_color_hex(statut):
    colors = {
        'brouillon': '#6c757d',
        'envoyee': '#17a2b8',
        'recue': '#007bff',
        'partiellement_livree': '#ffc107',
        'livree': '#28a745',
        'annulee': '#dc3545',
    }
    return colors.get(statut, '#6c757d')