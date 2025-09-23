from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from .models import JournalActivite
from .utils import get_client_ip

class VerificationAccesMiddleware(MiddlewareMixin):
    """
    🔥 MIDDLEWARE SIMPLIFIÉ - NE FAIT RIEN POUR LES URLS PUBLIQUES
    """
    
    def process_request(self, request):
        print(f"🔍 SECURITY MIDDLEWARE: Path={request.path}, Authentifié={request.user.is_authenticated}")
        
        # 🔥 CORRECTION : URLs PUBLIQUES COMPLÈTES
        PUBLIC_URLS = [
            '/',                          # Racine
            '/vitrine/',                  # Toute la vitrine
            '/dashboard/connexion/',      # Page de connexion
            '/dashboard/deconnexion/',    # Page de déconnexion
            '/static/',                   # Fichiers statiques
            '/media/',                    # Médias
            '/favicon.ico',               # Favicon
            '/admin/login/',              # Admin login
            '/admin/logout/',             # Admin logout
        ]

        # 🔥 CORRECTION : SI URL PUBLIQUE → AUTORISER IMMÉDIATEMENT
        if any(request.path.startswith(url) for url in PUBLIC_URLS) or request.path == '/':
            print(f"🔍 SECURITY MIDDLEWARE: URL publique → ACCÈS IMMÉDIAT")
            return None  # 🔥 PAS DE REDIRECTION

        # 🔥 CORRECTION : Pour les URLs privées, laisser le middleware d'entreprise gérer
        print(f"🔍 SECURITY MIDDLEWARE: URL privée → LAISSER PASSER")
        return None

    def handle_unauthorized_access(self, request):
        """Gère les tentatives d'accès non autorisées"""
        messages.error(request, "Accès refusé : permission manquante.")
        JournalActivite.objects.create(
            utilisateur=request.user if request.user.is_authenticated else None,
            action='ACCES_REFUSE',
            details=f"Tentative d'accès non autorisé à {request.path}",
            ip_address=get_client_ip(request)
        )
        return redirect(reverse('security:acces_refuse'))


class JournalisationMiddleware(MiddlewareMixin):
    """Middleware pour journaliser les modifications"""

    def process_response(self, request, response):
        # Ignorer les fichiers statiques et les requêtes non authentifiées
        if (request.path.startswith(('/static/', '/media/', '/favicon.ico')) or 
            not request.user.is_authenticated):
            return response

        # Journaliser seulement les modifications importantes
        if request.method in ['POST', 'PUT', 'DELETE'] and response.status_code < 400:
            try:
                action_type = {
                    'POST': 'CREATION',
                    'PUT': 'MODIFICATION', 
                    'DELETE': 'SUPPRESSION',
                }.get(request.method)

                if action_type:
                    # Éviter de journaliser les actions triviales
                    excluded_paths = ['/ajax/', '/api/', '/notifications/']
                    if any(request.path.startswith(path) for path in excluded_paths):
                        return response
                    
                    details = f"{action_type} sur {request.path}"
                    
                    # Ajout d'informations contextuelles
                    if request.user.is_superuser:
                        details = f"[SUPERADMIN] {details}"
                    elif request.user.is_staff:
                        details = f"[STAFF] {details}"
                    elif hasattr(request.user, 'role'):
                        details = f"[{request.user.role}] {details}"

                    JournalActivite.objects.create(
                        utilisateur=request.user,
                        action=action_type,
                        details=details,
                        ip_address=get_client_ip(request)
                    )
            except Exception as e:
                print(f"Erreur journalisation: {e}")

        return response