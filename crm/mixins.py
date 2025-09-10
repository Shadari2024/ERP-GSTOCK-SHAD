
from parametres.models import Entreprise, ConfigurationSAAS

class EntrepriseAccessMixin:
    """Mixin pour gérer l'accès aux données par entreprise"""
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'entreprise'):
            return queryset.filter(entreprise=self.request.user.entreprise)
        return queryset.none()
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['entreprise'] = self.request.user.entreprise
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entreprise'] = self.request.user.entreprise
        
        # Récupérer la devise principale
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            devise_symbole = "€"
        
        context['devise_principale_symbole'] = devise_symbole
        return context

