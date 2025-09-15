from django.shortcuts import redirect
from django.urls import reverse, resolve
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from .models import JournalActivite
from .utils import get_client_ip
import re

class VerificationAccesMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Injecter l'entreprise dans la requête
        if request.user.is_authenticated and hasattr(request.user, "entreprise"):
            request.entreprise = request.user.entreprise
        else:
            request.entreprise = None

        # --- Ton code actuel ici ---
        public_urls = [
            reverse('security:connexion'),
            reverse('security:deconnexion'),
            '/static/',
            '/media/',
            '/favicon.ico',
            '/admin/',
        ]

        if any(request.path.startswith(url) for url in public_urls):
            return None

        if not request.user.is_authenticated:
            return redirect(f"{reverse('security:connexion')}?next={request.path}")

        if request.user.is_superuser or request.user.is_staff:
            return None

        # Vues accessibles à tout utilisateur connecté
        allowed_common = [
            reverse('security:mon_profil'),
            reverse('security:changement_mdp'),
            reverse('security:dashboard_redirect'),
            reverse('security:acces_refuse'),  # ✅ CORRECTION : Ajout de la page d'accès refusé
        ]
        
        # Vérification avec correspondance exacte ou préfixe
        if any(request.path == url or request.path.startswith(url + '/') for url in allowed_common):
            return None

        # Vérification des tableaux de bord par rôle
        dashboard_urls = [
            reverse('security:admin_dashboard'),
            reverse('security:manager_dashboard'),
            reverse('security:caissier_dashboard'),
            reverse('security:vendeur_dashboard'),
            reverse('security:stock_dashboard'),
        ]
        
        if request.path in dashboard_urls:
            # L'accès aux dashboards est déjà géré par les décorateurs de vues
            return None

        # Vérification de permission via nom de vue - APPROCHE PLUS PERMISSIVE
        try:
            resolved_view = resolve(request.path_info)
            view_name = resolved_view.url_name
            app_name = resolved_view.app_name
            
            # Liste des vues qui nécessitent une permission explicite
            restricted_views = {
                'liste_client': 'STOCK.view_client',
                'vente_au_comptoir': 'STOCK.effectuer_vente',
                'gestion_entreprises': 'auth.view_entreprise',
                'creer_entreprise': 'auth.add_entreprise',
            }

            required_perm = restricted_views.get(view_name)

            if required_perm:
                # Vérification spéciale pour les permissions d'entreprise
                if required_perm.startswith('auth.') and not (request.user.is_superuser or request.user.is_staff):
                    return self.handle_unauthorized_access(request)
                
                if not request.user.has_perm(required_perm):
                    return self.handle_unauthorized_access(request)

        except Exception as e:
            # Si resolve échoue, on autorise par défaut (évite de bloquer le site)
            print(f"Middleware resolve error: {e}")
            pass

        # ✅ AUTORISER L'ACCÈS PAR DÉFAUT AUX AUTRES URLS
        # Les permissions spécifiques seront vérifiées dans les vues
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
        
        # ✅ CORRECTION : Utiliser le bon nom d'URL
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