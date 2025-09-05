# security/middleware.py
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
import re

class PosAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # URLs qui nécessitent un accès POS
        self.pos_urls = [
            r'^/ventes/pos/',
            r'^/ventes/caisse/',
            r'^/ventes/vente/',
        ]

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Vérifier si l'URL nécessite un accès POS
        path = request.path_info
        requires_pos_access = any(re.match(pattern, path) for pattern in self.pos_urls)
        
        if requires_pos_access and request.user.is_authenticated:
            user = request.user
            
            # Les admins et managers ont toujours accès
            if user.role in ['ADMIN', 'MANAGER']:
                return None
                
            # Pour les caissiers, vérifier qu'ils ont au moins un POS assigné
            if user.role == 'CAISSIER':
                if not user.get_assigned_pos().exists():
                    return HttpResponseForbidden(
                        "Vous n'êtes assigné à aucun point de vente. Contactez votre administrateur."
                    )
            
            # Pour les autres rôles, refuser l'accès
            if user.role not in ['ADMIN', 'MANAGER', 'CAISSIER']:
                return HttpResponseForbidden(
                    "Vous n'avez pas les permissions nécessaires pour accéder aux points de vente."
                )
        
        return None