from django import template
from ..models import Parametre

register = template.Library()

@register.filter
def format_devise(montant, devise=None):
    parametres = Parametre.objects.first()
    if not parametres:
        return f"{montant:.2f}"
    
    devise = devise or parametres.devise_principale
    symboles = {
        'USD': '$',
        'EUR': '€',
        'CDF': 'FC',
        'FC': 'FC'
    }
    return f"{symboles.get(devise, devise)} {montant:,.2f}"



from django import template
from decimal import Decimal
from ..models import TauxChange

register = template.Library()

@register.filter
def convertir_devise(montant, devise_source):
    if not montant or not devise_source:
        return montant
    
    devise_cible = template.Variable('devise_affichee').resolve({'devise_affichee': 'USD'})  # Valeur par défaut
    parametres = Parametre.objects.first()
    
    if not parametres or devise_source == devise_cible:
        return montant
    
    taux = TauxChange.get_taux(devise_source, devise_cible)
    return montant * taux if taux else montant




