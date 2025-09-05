# security/mixins.py
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404
from parametres.models import Entreprise

class EntrepriseAccessMixin(UserPassesTestMixin):
    """Mixin pour vérifier l'accès à une entreprise spécifique"""
    
    def test_func(self):
        user = self.request.user
        
        # Admins SaaS et superusers ont accès à tout
        if user.is_superuser or (hasattr(user, 'is_saas_admin') and user.is_saas_admin):
            return True
        
        # Récupérer l'entreprise cible
        entreprise = self.get_entreprise()
        if not entreprise:
            return False
        
        # Vérifier que l'utilisateur appartient à cette entreprise
        return hasattr(user, 'entreprise') and user.entreprise == entreprise
    
    def get_entreprise(self):
        """Méthode à surcharger pour spécifier comment récupérer l'entreprise"""
        # Par défaut, essaye de récupérer depuis les kwargs ou l'attribut de requête
        entreprise_id = self.kwargs.get('entreprise_id') or self.kwargs.get('pk')
        if entreprise_id:
            return get_object_or_404(Entreprise, id=entreprise_id)
        
        # Sinon, utilise l'entreprise de la session
        if hasattr(self.request, 'entreprise'):
            return self.request.entreprise
        
        return None
    
    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas accès à cette entreprise")
        return redirect('security:acces_refuse')


class SAASAdminRequiredMixin(UserPassesTestMixin):
    """Mixin pour restreindre l'accès aux administrateurs SaaS"""
    
    def test_func(self):
        user = self.request.user
        return user.is_superuser or (hasattr(user, 'is_saas_admin') and user.is_saas_admin)
    
    def handle_no_permission(self):
        messages.error(self.request, "Accès réservé aux administrateurs SaaS")
        return redirect('security:acces_refuse')


class EntrepriseFilterMixin:
    """Mixin pour filtrer les querysets par entreprise"""
    
    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        
        # Admins SaaS et superusers voient tout
        if user.is_superuser or (hasattr(user, 'is_saas_admin') and user.is_saas_admin):
            return queryset
        
        # Filtrer par entreprise de l'utilisateur
        if hasattr(user, 'entreprise') and user.entreprise:
            # Vérifier différents patterns de relation
            if hasattr(queryset.model, 'entreprise'):
                return queryset.filter(entreprise=user.entreprise)
            elif hasattr(queryset.model, 'utilisateur') and hasattr(queryset.model.utilisateur.field.related_model, 'entreprise'):
                return queryset.filter(utilisateur__entreprise=user.entreprise)
            elif hasattr(queryset.model, 'user') and hasattr(queryset.model.user.field.related_model, 'entreprise'):
                return queryset.filter(user__entreprise=user.entreprise)
        
        return queryset.none()  # Par sécurité, retourner un queryset vide


class RoleRequiredMixin(UserPassesTestMixin):
    """Mixin pour vérifier le rôle de l'utilisateur"""
    
    roles_required = []
    
    def test_func(self):
        user = self.request.user
        
        # Admins SaaS et superusers ont tous les droits
        if user.is_superuser or (hasattr(user, 'is_saas_admin') and user.is_saas_admin):
            return True
        
        # Vérifier le rôle
        return hasattr(user, 'role') and user.role in self.roles_required
    
    def handle_no_permission(self):
        messages.error(self.request, f"Rôle requis: {', '.join(self.roles_required)}")
        return redirect('security:acces_refuse')


class PermissionRequiredMixin(UserPassesTestMixin):
    """Mixin pour vérifier une permission spécifique"""
    
    permission_required = None
    
    def test_func(self):
        user = self.request.user
        
        # Admins SaaS et superusers ont tous les droits
        if user.is_superuser or (hasattr(user, 'is_saas_admin') and user.is_saas_admin):
            return True
        
        # Vérifier la permission
        return user.has_perm(self.permission_required) if self.permission_required else False
    
    def handle_no_permission(self):
        messages.error(self.request, f"Permission requise: {self.permission_required}")
        return redirect('security:acces_refuse')


class MultiEntrepriseContextMixin:
    """Ajoute le contexte multi-entreprises aux vues"""
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Informations sur les entreprises accessibles
        if hasattr(user, 'get_visible_entreprises'):
            context['entreprises_accessibles'] = user.get_visible_entreprises()
        else:
            from parametres.models import Entreprise
            if user.is_superuser or (hasattr(user, 'is_saas_admin') and user.is_saas_admin):
                context['entreprises_accessibles'] = Entreprise.objects.all()
            elif hasattr(user, 'entreprise'):
                context['entreprises_accessibles'] = Entreprise.objects.filter(id=user.entreprise.id)
            else:
                context['entreprises_accessibles'] = Entreprise.objects.none()
        
        # Entreprise courante
        if hasattr(self.request, 'entreprise'):
            context['current_entreprise'] = self.request.entreprise
        elif hasattr(user, 'entreprise'):
            context['current_entreprise'] = user.entreprise
        
        # Statut admin SaaS
        context['is_saas_admin'] = user.is_superuser or (hasattr(user, 'is_saas_admin') and user.is_saas_admin)
        
        return context