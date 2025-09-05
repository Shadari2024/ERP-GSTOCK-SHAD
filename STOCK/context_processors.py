from .models import Parametre

def parametre_context(request):
    try:
        parametre = Parametre.objects.first()
    except Parametre.DoesNotExist:
        parametre = None
    return {
        'parametre': parametre
    }
