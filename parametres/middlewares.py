import logging
from datetime import timedelta
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy # Import reverse_lazy for potential future use
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from parametres.models import Entreprise, Abonnement, ModuleEntreprise, ConfigurationSAAS

logger = logging.getLogger(__name__)

class CurrentEntrepriseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # URLs exemptées de la vérification d'entreprise et d'abonnement
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
            # Ajoutez ici d'autres URL que les superutilisateurs devraient pouvoir accéder
            # sans entreprise sélectionnée, par exemple une page de gestion des entreprises.
            # 'parametres:gestion_super_entreprise', # Exemple
        ]

        # Exclusion des assets statiques et média
        if settings.STATIC_URL and request.path_info.startswith(settings.STATIC_URL):
            return self.get_response(request)
        if settings.MEDIA_URL and request.path_info.startswith(settings.MEDIA_URL):
            return self.get_response(request)

        # Vérification des URLs exemptées
        for url_name in EXEMPT_URLS:
            try:
                if request.path_info.startswith(reverse(url_name)):
                    return self.get_response(request)
            except Exception as e:
                logger.debug(f"URL non résolue dans EXEMPT_URLS: {url_name} - {e}")
                continue

        # Gestion des utilisateurs authentifiés
        if request.user.is_authenticated:
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
                
                # --- DÉSACIVATION DE LA REDIRECTION OBLIGATOIRE POUR SUPERUSER ---
                # Un superutilisateur n'est PAS FORCÉ à avoir une entreprise sélectionnée.
                # Il peut accéder à certaines pages sans entreprise.
                # Le code ci-dessous est supprimé ou commenté pour permettre cela.
                # if not request.entreprise and request.path_info != reverse('parametres:entreprise_select'):
                #     messages.info(request, _("Veuillez sélectionner une entreprise."))
                #     return redirect('parametres:entreprise_select')
                # ------------------------------------------------------------------
                
            # Cas 2: Utilisateur normal - entreprise définie dans son profil (obligatoire)
            elif hasattr(request.user, 'entreprise') and request.user.entreprise:
                request.entreprise = request.user.entreprise
                
            # Cas 3: Utilisateur sans entreprise associée (non superuser)
            else:
                # Si l'utilisateur n'est pas lié à une entreprise, rediriger vers la page de lien.
                if request.path_info != reverse('parametres:account_not_linked_to_entreprise'):
                    messages.error(request, _("Votre compte n'est associé à aucune entreprise."))
                    return redirect('parametres:account_not_linked_to_entreprise')
            
            # Si aucune entreprise n'a été déterminée pour un utilisateur authentifié NON-SUPERUSER,
            # et qu'il n'est pas sur une page d'exception, on le redirige.
            # Pour les superusers, request.entreprise peut être None ici, et c'est voulu.
            if not request.entreprise and not request.user.is_superuser and request.path_info not in [reverse(url) for url in EXEMPT_URLS if url.startswith('parametres:')]:
                messages.error(request, _("Impossible de déterminer l'entreprise pour votre session."))
                return redirect('parametres:entreprise_select') # Ou une autre page appropriée

            # 2. VÉRIFICATION DES MODULES ACTIFS et 3. GESTION DE L'ABONNEMENT
            # Ces sections ne doivent s'exécuter que si une entreprise est effectivement sélectionnée/liée.
            if request.entreprise:
                # Récupération des modules activés pour cette entreprise
                modules_actifs = ModuleEntreprise.objects.filter(
                    entreprise=request.entreprise,
                    est_actif=True
                ).select_related('module')
                
                request.modules_actifs = [ma.module.code for ma in modules_actifs]
                
                # Vérification d'accès au module courant
                app_label = None
                if request.resolver_match:
                    app_label = request.resolver_match.app_name

                # Redirection si le module n'est pas actif et n'est pas 'parametres'
                # La page 'parametres:abonnement_expirer' est gérée séparément par EXEMPT_URLS
                # Les superusers NE SONT PAS AFFECTÉS par cette logique de module/abonnement
                # si request.entreprise est None. S'ils sélectionnent une entreprise,
                # cette logique s'applique à cette entreprise.
                if not request.user.is_superuser and app_label and app_label != 'parametres' and app_label not in request.modules_actifs:
                    messages.error(request, _("Vous n'avez pas accès à ce module."))
                    return redirect('security:dashboard') # Ou une page de présentation des modules
                
                # GESTION DE L'ABONNEMENT (uniquement si une entreprise est présente)
                try:
                    now = timezone.now()
                    request.abonnement = Abonnement.objects.filter(
                        Q(entreprise=request.entreprise) &
                        Q(est_actif=True) &
                        Q(date_debut__lte=now) &
                        (Q(date_fin__isnull=True) | Q(date_fin__gte=now))
                    ).order_by('-date_debut').first()
                    
                    # Logique de redirection si pas d'abonnement actif (et pas en essai)
                    # S'applique uniquement aux utilisateurs NON-SUPERUSER OU si un superuser a sélectionné une entreprise
                    # et que cette entreprise n'est pas en essai et n'a pas d'abonnement actif.
                    if not request.user.is_superuser and not request.abonnement and request.entreprise.statut != Entreprise.StatutEntreprise.ESSAI:
                        if request.path_info != reverse('parametres:abonnement_expirer'):
                            messages.error(request, _("Aucun abonnement actif. Veuillez souscrire à un abonnement."))
                            return redirect('parametres:abonnement_expirer')
                        else:
                            logger.info(f"Entreprise {request.entreprise.nom} sur page d'expiration, pas de redirection.")
                    elif not request.abonnement and request.entreprise.statut == Entreprise.StatutEntreprise.ESSAI:
                        logger.info(f"Entreprise {request.entreprise.nom} en période d'essai, pas d'abonnement requis.")

                except Exception as e:
                    logger.error(f"Erreur vérification abonnement pour entreprise {request.entreprise.nom}: {str(e)}", exc_info=True)


        # Gestion des utilisateurs non authentifiés
        else:
            is_exempt_or_login_url = False
            for url_name in EXEMPT_URLS:
                try:
                    if request.path_info.startswith(reverse(url_name)):
                        is_exempt_or_login_url = True
                        break
                except Exception as e:
                    logger.debug(f"URL non résolue dans EXEMPT_URLS pour non-authentifié: {url_name} - {e}")
                    continue
            
            if not is_exempt_or_login_url and not request.path_info.startswith(settings.LOGIN_URL):
                return redirect(settings.LOGIN_URL)

        response = self.get_response(request)
        return response
    
# Votre EnsureSAASConfigMiddleware reste inchangé.
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
                    complexite_mdp=ConfigurationSAAS.ComplexiteMDP.MOYEN
                )
        return self.get_response(request)
    
    
    
    
    
    
    
    
    
    
    
    
# saas/middleware.py
import threading
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from parametres.models import ConfigurationSAAS

thread_local = threading.local()

class SAASMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """Configure les settings dynamiquement selon l'entreprise"""
        if hasattr(request, 'user') and hasattr(request.user, 'entreprise'):
            try:
                # Récupérer la configuration SAAS de l'entreprise
                config_saas = ConfigurationSAAS.objects.get(entreprise=request.user.entreprise)
                
                # Stocker la configuration dans le thread local
                thread_local.saas_config = config_saas
                
                # Mettre à jour les settings dynamiquement
                self._update_email_settings(config_saas)
                
            except ConfigurationSAAS.DoesNotExist:
                # Utiliser les settings par défaut si aucune configuration
                thread_local.saas_config = None
                self._reset_email_settings()
        
        return None
    
    def _update_email_settings(self, config_saas):
        """Met à jour les settings email selon la configuration SAAS"""
        # Configuration SMTP
        settings.EMAIL_BACKEND = config_saas.email_backend
        settings.EMAIL_HOST = config_saas.email_host
        settings.EMAIL_PORT = config_saas.email_port
        settings.EMAIL_USE_TLS = config_saas.email_use_tls
        settings.EMAIL_USE_SSL = config_saas.email_use_ssl
        settings.EMAIL_HOST_USER = config_saas.email_host_user
        settings.EMAIL_HOST_PASSWORD = config_saas.email_host_password
        settings.DEFAULT_FROM_EMAIL = config_saas.default_from_email
        settings.EMAIL_TIMEOUT = config_saas.email_timeout
        
        # Configuration devise
        if config_saas.devise_principale:
            settings.DEFAULT_CURRENCY = config_saas.devise_principale.symbole
            settings.DEFAULT_CURRENCY_CODE = config_saas.devise_principale.code
    
    def _reset_email_settings(self):
        """Réinitialise les settings email aux valeurs par défaut"""
        # Vous pouvez définir des valeurs par défaut dans vos settings.py
        pass
    
    def process_response(self, request, response):
        """Nettoie le thread local après la requête"""
        if hasattr(thread_local, 'saas_config'):
            del thread_local.saas_config
        return response

def get_current_saas_config():
    """Retourne la configuration SAAS actuelle du thread"""
    return getattr(thread_local, 'saas_config', None)
    