from django import template

register = template.Library()

@register.filter
def get_statut_display(commande):
    return commande.get_statut_display()