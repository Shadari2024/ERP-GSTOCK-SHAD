from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

class EntrepriseAccessMixin(AccessMixin):
    """Vérifie que l'utilisateur a accès à l'entreprise"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not hasattr(request.user, 'entreprise'):
            messages.error(request, _("Aucune entreprise associée à votre compte."))
            return redirect('login')
            
        return super().dispatch(request, *args, **kwargs)