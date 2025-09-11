# achats/templatetags/calcul_filters.py
from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def avec_remise(prix, remise):
    """Applique une remise en pourcentage au prix"""
    remise_factor = Decimal('1') - (Decimal(str(remise)) / Decimal('100'))
    return (Decimal(str(prix)) * remise_factor).quantize(Decimal('0.01'))

@register.filter
def calculer_tva(montant_ht, taux_tva):
    """Calcule la TVA à partir d'un montant HT et d'un taux"""
    return (Decimal(str(montant_ht)) * (Decimal(str(taux_tva)) / Decimal('100'))).quantize(Decimal('0.01'))

@register.filter
def calculer_ttc(montant_ht, taux_tva):
    """Calcule le TTC à partir d'un montant HT et d'un taux TVA"""
    tva = calculer_tva(montant_ht, taux_tva)
    return (Decimal(str(montant_ht)) + tva).quantize(Decimal('0.01'))