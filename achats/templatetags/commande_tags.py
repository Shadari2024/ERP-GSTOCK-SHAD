from django import template

register = template.Library()

@register.filter(name='display_statut')
def display_statut(value):
    statuts = {
        'brouillon': 'Brouillon',
        'envoyee': 'Envoyée',
        'recue': 'Reçue', 
        'annulee': 'Annulée'
    }
    return statuts.get(value, value)