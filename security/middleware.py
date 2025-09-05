from django.shortcuts import redirect
from django.urls import reverse, resolve
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils.deprecation import MiddlewareMixin
from .models import JournalActivite
from .utils import get_client_ip

class VerificationAccesMiddleware(MiddlewareMixin):
    """Middleware pour vérifier les accès en fonction des rôles et permissions"""

    def process_request(self, request):
        # URLs publiques (sans authentification requise)
        public_urls = [
            reverse('security:connexion'),
            reverse('security:deconnexion'),
            '/static/',
            '/media/',
            '/favicon.ico',
        ]

        # Vérifie accès public
        if any(request.path.startswith(url) for url in public_urls):
            return None

        # Redirection si non connecté
        if not request.user.is_authenticated:
            return redirect(f"{reverse('security:connexion')}?next={request.path}")

        # Accès libre pour les super utilisateurs SaaS
        if getattr(request.user, 'is_saas_admin', False):
            return None

        # Vues accessibles à tout utilisateur connecté
        allowed_common = [
            reverse('security:mon_profil'),
            reverse('security:changement_mdp'),
            reverse('security:dashboard_redirect'),
        ]
        if any(request.path.startswith(url) for url in allowed_common):
            return None

        # Vérification spécifique pour les admins d'entreprise
        if getattr(request.user, 'role', None) == 'ENTREPRISE_ADMIN':
            # Vérifier si l'admin essaie d'accéder à une vue SaaS réservée
            if request.path.startswith('/saas/') or 'saas' in resolve(request.path_info).app_names:
                return self.handle_unauthorized_access(request)

        # Vérification de permission via nom de vue
        try:
            resolved_view = resolve(request.path_info)
            view_name = resolved_view.url_name
            app_name = resolved_view.app_name
            model_permission_map = {
                'liste_client': 'STOCK.view_client',
                'vente_au_comptoir': 'STOCK.effectuer_vente',
                'produits_par_categorie': 'STOCK.view_produit',
                # Gestion des entreprises (réservé aux super admins)
                'gestion_entreprises': 'auth.view_entreprise',
                'creer_entreprise': 'auth.add_entreprise',
                # Ajoutez d'autres mappages si nécessaire
            }

            required_perm = model_permission_map.get(view_name)

            if required_perm:
                # Vérification spéciale pour les permissions d'entreprise
                if required_perm.startswith('auth.') and not request.user.is_saas_admin:
                    return self.handle_unauthorized_access(request)
                
                if not request.user.has_perm(required_perm):
                    return self.handle_unauthorized_access(request)

        except Exception:
            # Si resolve échoue ou vue non mappée
            pass

        return None

    def handle_unauthorized_access(self, request):
        """Gère les tentatives d'accès non autorisées"""
        messages.error(request, "Accès refusé : permission manquante.")
        JournalActivite.objects.create(
            utilisateur=request.user,
            action='ACCES',
            details=f"Tentative d'accès non autorisé à {request.path}",
            ip_address=get_client_ip(request)
        )
        
        # Redirection différente selon le type d'utilisateur
        if getattr(request.user, 'is_saas_admin', False):
            return redirect('saas:dashboard')
        return redirect('security:dashboard_redirect')


class JournalisationMiddleware(MiddlewareMixin):
    """Middleware pour journaliser les modifications"""

    def process_response(self, request, response):
        # Ignorer les fichiers statiques
        if request.path.startswith(('/static/', '/media/', '/favicon.ico')):
            return response

        if request.user.is_authenticated and request.method in ['POST', 'PUT', 'DELETE']:
            try:
                action_type = {
                    'POST': 'CREATION',
                    'PUT': 'MODIFICATION',
                    'DELETE': 'SUPPRESSION',
                }.get(request.method)

                if action_type:
                    details = f"{action_type} sur {request.path}"
                    
                    # Ajout d'informations supplémentaires pour les super admins
                    if getattr(request.user, 'is_saas_admin', False):
                        details = f"[SAAS ADMIN] {details}"
                    elif getattr(request.user, 'role', None) == 'ENTREPRISE_ADMIN':
                        details = f"[ENTREPRISE ADMIN] {details}"

                    JournalActivite.objects.create(
                        utilisateur=request.user,
                        action=action_type,
                        details=details,
                        ip_address=get_client_ip(request)
                    )
            except Exception:
                pass

        return response