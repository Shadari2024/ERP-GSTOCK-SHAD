# parametres/context_processors.py
from django.conf import settings

def entreprise_info(request):
    if not request.user.is_authenticated:
        return {}
    
    entreprise = getattr(request, 'entreprise', None)
    if not entreprise:
        return {}
    
    return {
        'current_entreprise': entreprise,
        'entreprise_logo': entreprise.logo.url if entreprise.logo else settings.DEFAULT_LOGO,
        'entreprise_nom': entreprise.nom,
    }