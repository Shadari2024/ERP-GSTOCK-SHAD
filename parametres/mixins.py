# parametres/mixins.py
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages

class EntrepriseAccessMixin:
    """Vérifie que l'utilisateur a accès à l'entreprise courante"""
    def dispatch(self, request, *args, **kwargs):
        # Ajout de messages d'erreur explicites
        if not hasattr(request, 'entreprise') or not request.entreprise:
            messages.error(request, "Veuillez sélectionner une entreprise d'abord")
            return redirect('parametres:entreprise_select')
        
        # Pour les non-superusers, vérifier que l'utilisateur appartient à l'entreprise
        if not request.user.is_superuser and hasattr(request.user, 'entreprise'):
            if request.user.entreprise != request.entreprise:
                raise PermissionDenied("Vous n'avez pas les permissions pour accéder à cette entreprise")
        
        return super().dispatch(request, *args, **kwargs)