from django import template

register = template.Library()

@register.filter
def div(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return None

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except ValueError:
        return None
    
    


@register.filter
def get_item(dictionary, key):
    """Récupère une valeur d'un dictionnaire par sa clé"""
    return dictionary.get(key)


register = template.Library()
@register.filter
def div(value, arg):
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return None
    
    
    
register = template.Library()

@register.filter
def sum_debit(lignes):
    """Calcule la somme des débits d'une liste de lignes d'écriture"""
    return sum(ligne.debit for ligne in lignes if ligne.debit)

@register.filter
def sum_credit(lignes):
    """Calcule la somme des crédits d'une liste de lignes d'écriture"""
    return sum(ligne.credit for ligne in lignes if ligne.credit)

