import logging
from datetime import timedelta
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from parametres.models import Entreprise, Abonnement, ModuleEntreprise, ConfigurationSAAS

logger = logging.getLogger(__name__)

class CurrentEntrepriseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 🔥 CORRECTION COMPLÈTE : URLs PUBLIQUES (vitrine + connexion)
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

        # 🔥 CORRECTION : Vérifier d'abord si l'URL est PUBLIQUE
        if any(request.path.startswith(url) for url in PUBLIC_URLS) or request.path == '/':
            print(f"🔍 CURRENT_ENTREPRISE MIDDLEWARE: URL publique → PAS DE VÉRIFICATION")
            return self.get_response(request)

        # Exclusion des assets statiques et média
        if settings.STATIC_URL and request.path.startswith(settings.STATIC_URL):
            return self.get_response(request)
        if settings.MEDIA_URL and request.path.startswith(settings.MEDIA_URL):
            return self.get_response(request)

        # 🔥 CORRECTION : URLs exemptées de la vérification d'entreprise
        EXEMPT_URLS = [
            'security:connexion',
            'security:deconnexion',
            'security:inscription',
            'security:password_reset',
            'parametres:entreprise_select',
            'parametres:account_not_linked_to_entreprise',
            'parametres:abonnement_expirer',
            'admin:index',
            'admin:login',
        ]

        # Vérification des URLs exemptées
        for url_name in EXEMPT_URLS:
            try:
                if request.path.startswith(reverse(url_name)):
                    print(f"🔍 CURRENT_ENTREPRISE MIDDLEWARE: URL exemptée → PAS DE VÉRIFICATION")
                    return self.get_response(request)
            except Exception as e:
                logger.debug(f"URL non résolue dans EXEMPT_URLS: {url_name} - {e}")
                continue

        # 🔥 Gestion des utilisateurs NON AUTHENTIFIÉS
        if not request.user.is_authenticated:
            print(f"🔍 CURRENT_ENTREPRISE MIDDLEWARE: Utilisateur non authentifié → REDIRECTION VERS VITRINE")
            # 🔥 CORRECTION : Rediriger vers la vitrine au lieu de la connexion
            return redirect('/vitrine/')

        # 🔥 Gestion des utilisateurs AUTHENTIFIÉS
        print(f"🔍 CURRENT_ENTREPRISE MIDDLEWARE: Utilisateur authentifié → {request.user.username}")

        # Initialisation des attributs
        request.entreprise = None
        request.abonnement = None
        request.modules_actifs = []

        # 1. DÉTERMINATION DE L'ENTREPRISE COURANTE
        # -----------------------------------------
        
        # Cas 1: Superutilisateur - sélection facultative
        if request.user.is_superuser:
            entreprise_id = request.session.get('current_entreprise_id')
            if entreprise_id:
                try:
                    request.entreprise = Entreprise.objects.get(pk=entreprise_id)
                except Entreprise.DoesNotExist:
                    request.session.pop('current_entreprise_id', None)
                    messages.warning(request, _("L'entreprise sélectionnée n'existe plus."))
        
        # Cas 2: Utilisateur normal - entreprise définie dans son profil
        elif hasattr(request.user, 'entreprise') and request.user.entreprise:
            request.entreprise = request.user.entreprise
        
        # Cas 3: Utilisateur sans entreprise associée
        else:
            if request.path != reverse('parametres:account_not_linked_to_entreprise'):
                messages.error(request, _("Votre compte n'est associé à aucune entreprise."))
                return redirect('parametres:account_not_linked_to_entreprise')
        
        # Si aucune entreprise pour un utilisateur normal
        if not request.entreprise and not request.user.is_superuser:
            if request.path != reverse('parametres:entreprise_select'):
                messages.error(request, _("Impossible de déterminer l'entreprise pour votre session."))
                return redirect('parametres:entreprise_select')

        # 2. VÉRIFICATION DES MODULES ACTIFS (si entreprise présente)
        if request.entreprise:
            modules_actifs = ModuleEntreprise.objects.filter(
                entreprise=request.entreprise,
                est_actif=True
            ).select_related('module')
            
            request.modules_actifs = [ma.module.code for ma in modules_actifs]
            
            # Vérification d'accès au module courant
            app_label = None
            if request.resolver_match:
                app_label = request.resolver_match.app_name

            if not request.user.is_superuser and app_label and app_label != 'parametres' and app_label not in request.modules_actifs:
                messages.error(request, _("Vous n'avez pas accès à ce module."))
                return redirect('security:dashboard')
            
            # 3. GESTION DE L'ABONNEMENT
            try:
                now = timezone.now()
                request.abonnement = Abonnement.objects.filter(
                    Q(entreprise=request.entreprise) &
                    Q(est_actif=True) &
                    Q(date_debut__lte=now) &
                    (Q(date_fin__isnull=True) | Q(date_fin__gte=now))
                ).order_by('-date_debut').first()
                
                if not request.user.is_superuser and not request.abonnement and request.entreprise.statut != Entreprise.StatutEntreprise.ESSAI:
                    if request.path != reverse('parametres:abonnement_expirer'):
                        messages.error(request, _("Aucun abonnement actif. Veuillez souscrire à un abonnement."))
                        return redirect('parametres:abonnement_expirer')

            except Exception as e:
                logger.error(f"Erreur vérification abonnement: {str(e)}")

        response = self.get_response(request)
        return response

class EnsureSAASConfigMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if hasattr(request, 'entreprise') and request.entreprise:
            try:
                request.entreprise.config_saas
            except ObjectDoesNotExist:
                ConfigurationSAAS.objects.create(
                    entreprise=request.entreprise,
                    fuseau_horaire='UTC',
                    langue='fr',
                    expiration_session=30,
                    complexite_mdp=ConfigurationSAAS.ComplexiteMdp.MOYEN
                )
        return self.get_response(request)