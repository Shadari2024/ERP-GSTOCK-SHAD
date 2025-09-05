from django import template

register = template.Library()

@register.filter
def devise_symbole(parametre, devise=None):
    try:
        # Appelle format_devise avec 1 pour récupérer le symbole
        return parametre.format_devise(1, devise).split()[0]
    except:
        return devise or ''
