from django.core.exceptions import PermissionDenied
from functools import wraps
from django.shortcuts import redirect
from django.contrib.auth.decorators import user_passes_test

def role_requis(roles_autorises):
    """Décorateur pour restreindre l'accès aux vues par rôle (groupes + champ role)"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('security:connexion')
            
            # ✅ Vérification des groupes D'ABORD
            user_groups = [group.name for group in request.user.groups.all()]
            
            # Mapping des noms de groupes vers les rôles
            group_to_role_map = {
                'Manager': 'MANAGER',
                'Vendeur': 'VENDEUR', 
                'Caissier': 'CAISSIER',
                'Stock': 'STOCK',
                'Admin': 'ADMIN'
            }
            
            # Convertir les groupes en rôles
            user_roles_from_groups = []
            for group_name in user_groups:
                if group_name in group_to_role_map:
                    user_roles_from_groups.append(group_to_role_map[group_name])
            
            # ✅ Combiner les rôles des groupes et le champ role
            user_all_roles = user_roles_from_groups.copy()
            if hasattr(request.user, 'role') and request.user.role:
                user_all_roles.append(request.user.role)
            
            print(f"🔍 ROLE REQUIS - User: {request.user.username}")
            print(f"🔍 ROLE REQUIS - Groups: {user_groups}")
            print(f"🔍 ROLE REQUIS - Roles from groups: {user_roles_from_groups}")
            print(f"🔍 ROLE REQUIS - Role field: {getattr(request.user, 'role', 'NOT_SET')}")
            print(f"🔍 ROLE REQUIS - All roles: {user_all_roles}")
            print(f"🔍 ROLE REQUIS - Required: {roles_autorises}")
            
            # ✅ Vérifier si l'utilisateur a un des rôles requis
            has_required_role = any(role in user_all_roles for role in roles_autorises)
            
            if has_required_role or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            raise PermissionDenied("Vous n'avez pas le rôle requis pour accéder à cette page")
        return _wrapped_view
    return decorator

def permission_requise(permission, raise_exception=False):
    """
    Décorateur pour vérifier une permission spécifique
    Args:
        permission (str|list): Permission requise (peut être une liste)
        raise_exception (bool): Si True, lève PermissionDenied au lieu de rediriger
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                if raise_exception:
                    raise PermissionDenied
                return redirect('security:connexion')
            
            # Gère à la fois une permission unique ou une liste de permissions
            if isinstance(permission, (list, tuple)):
                has_perm = any(request.user.has_perm(p) for p in permission)
            else:
                has_perm = request.user.has_perm(permission)
            
            if has_perm or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            if raise_exception:
                raise PermissionDenied("Permission refusée")
            
            # Redirection par défaut pour les utilisateurs non autorisés
            return redirect('security:acces_refuse')
        return _wrapped_view
    return decorator

def acces_module(nom_module):
    """Décorateur pour vérifier l'accès à un module spécifique"""
    # Mapping des modules vers les permissions requises
    MODULE_PERMISSIONS = {
        'dashboard': 'acces_dashboard',
        'clients': 'view_client',
        'produits': 'view_produit',
        'categories': 'view_categorie',
        'commandes': 'view_commande',
        'ventes': 'effectuer_vente',
        'fournisseurs': 'view_fournisseur',
        'achats': 'view_achat',
        'inventaires': 'view_inventaire',
        'parametres': 'view_parametre',
        'statistiques': 'voir_statistiques',
        'rapports': 'view_rapport',
        'tresorerie': 'view_tresorerie',
        'sauvegardes': 'view_backup',
        'promotions': 'view_promotion',
        'notifications': 'view_notification',
        'TauxEchange':'view_tauxchange'
    }
    
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('security:connexion')
            
            permission_requise = MODULE_PERMISSIONS.get(nom_module)
            
            if permission_requise and not request.user.has_perm(permission_requise):
                raise PermissionDenied(f"Accès au module {nom_module} refusé")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

# Décorateur utilitaire supplémentaire
def staff_required(view_func=None, redirect_field_name=None, login_url='security:connexion'):
    """
    Vérifie que l'utilisateur est authentifié et est un membre du staff
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and u.is_staff,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator