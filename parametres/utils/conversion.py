# utils/conversion.py
from typing import Tuple
from django.db.models import Q
from parametres.models import *

def obtenir_taux_conversion(devise_source_id: int, devise_cible_id: int, date: str = None) -> Tuple[float, str]:
    """
    Obtient le taux de conversion dans les deux directions si nécessaire.
    Retourne un tuple (taux, sens_conversion)
    """
    # Essayer directement
    taux_direct = TauxChange.objects.filter(
        devise_source_id=devise_source_id,
        devise_cible_id=devise_cible_id,
        est_actif=True,
        date_application__lte=date if date else Q()
    ).order_by('-date_application').first()

    if taux_direct:
        return float(taux_direct.taux), 'direct'

    # Si pas trouvé, essayer l'inverse et inverser le taux
    taux_inverse = TauxChange.objects.filter(
        devise_source_id=devise_cible_id,
        devise_cible_id=devise_source_id,
        est_actif=True,
        date_application__lte=date if date else Q()
    ).order_by('-date_application').first()

    if taux_inverse:
        return round(1 / float(taux_inverse.taux), 6), 'inverse'

    raise ValueError("Taux de conversion non disponible")