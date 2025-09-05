from django import template

register = template.Library()

@register.filter
def role_color(role):
    colors = {
        'ADMIN': 'bg-admin',
        'MANAGER': 'bg-manager',
        'CAISSIER': 'bg-caissier',
        'VENDEUR': 'bg-vendeur',
        'STOCK': 'bg-stock'
    }
    return colors.get(role, 'bg-default')



