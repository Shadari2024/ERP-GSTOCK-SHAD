# paiement_tags.py
from django import template

register = template.Library()

@register.filter
def get_method_icon(methode):
    mapping = {
        'cash': 'fas fa-money-bill-wave',
        'card': 'fas fa-credit-card',
        'mobile': 'fas fa-mobile-alt',
        'bank': 'fas fa-university',
        # Ajoute d'autres méthodes selon ton modèle
    }
    return mapping.get(methode, 'fas fa-question-circle')
