from django.shortcuts import render
from django.views.generic import TemplateView, CreateView
from django.shortcuts import redirect

from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.utils.translation import gettext_lazy as _
from parametres.models import ConfigurationSAAS
from .mixins import EntrepriseAccessMixin
from .models import DemandeDemo
from .forms import DemandeDemoForm
class AccueilView(TemplateView):
    template_name = "vitrine/index.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer la devise principale pour l'affichage des tarifs
        devise_symbole = "€"  # valeur par défaut
        
        if self.request.user.is_authenticated and hasattr(self.request.user, 'entreprise'):
            try:
                config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
                if config_saas and hasattr(config_saas, 'devise_principale') and config_saas.devise_principale:
                    devise_symbole = config_saas.devise_principale.symbole
            except (ConfigurationSAAS.DoesNotExist, AttributeError):
                pass
                
        context['devise_symbole'] = devise_symbole
        return context
    
class FeaturesView(TemplateView):
    template_name = "vitrine/features.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Modules disponibles avec descriptions
        modules = [
            {
                'nom': _('Achats'),
                'icone': 'fas fa-shopping-cart',
                'description': _('Gérez vos achats, fournisseurs et commandes d\'approvisionnement'),
                'avantages': [
                    _('Gestion des fournisseurs'),
                    _('Suivi des commandes'),
                    _('Réception des marchandises'),
                    _('Factures fournisseurs'),
                ]
            },
            {
                'nom': _('Ventes'),
                'icone': 'fas fa-cash-register',
                'description': _('Optimisez votre processus de vente et relation client'),
                'avantages': [
                    _('Devis et facturation'),
                    _('Gestion des clients'),
                    _('Suivi des commandes clients'),
                    _('Statistiques de vente'),
                ]
            },
            {
                'nom': _('Stock'),
                'icone': 'fas fa-boxes',
                'description': _('Contrôlez votre inventaire en temps réel'),
                'avantages': [
                    _('Gestion des inventaires'),
                    _('Mouvements de stock'),
                    _('Alertes de seuil'),
                    _('Valuation du stock'),
                ]
            },
            {
                'nom': _('Comptabilité'),
                'icone': 'fas fa-calculator',
                'description': _('Tenez une comptabilité auxiliaire complète'),
                'avantages': [
                    _('Grand livre général'),
                    _('Comptes auxiliaires'),
                    _('Balance comptable'),
                    _('États financiers'),
                ]
            },
            {
                'nom': _('GRH'),
                'icone': 'fas fa-users',
                'description': _('Managez vos ressources humaines efficacement'),
                'avantages': [
                    _('Gestion du personnel'),
                    _('Paie et congés'),
                    _('Contrats'),
                    _('Évaluations'),
                ]
            },
            {
                'nom': _('Paramètres'),
                'icone': 'fas fa-cogs',
                'description': _('Personnalisez votre ERP selon vos besoins'),
                'avantages': [
                    _('Configuration multi-entreprise'),
                    _('Gestion des utilisateurs'),
                    _('Personnalisation des devises'),
                    _('Sécurité et permissions'),
                ]
            },
        ]
        
        context['modules'] = modules
        return context

class PricingView(LoginRequiredMixin, EntrepriseAccessMixin, TemplateView):
    template_name = "vitrine/pricing.html"
    permission_required = "vitrine.view_pricing"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.user.entreprise
        
        # Récupérer la devise principale depuis ConfigurationSAAS
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            devise_symbole = "€"
        
        # Forfaits avec prix dans la devise de l'entreprise
        forfaits = [
            {
                'nom': _('Essentiel'),
                'prix': f"75 000 {devise_symbole}",
                'periode': _('/mois'),
                'features': [
                    _('Achats et Ventes'),
                    _('Gestion de stock basique'),
                    _('Support email'),
                    _('1 utilisateur'),
                ],
                'populaire': False
            },
            {
                'nom': _('Professionnel'),
                'prix': f"150 000 {devise_symbole}",
                'periode': _('/mois'),
                'features': [
                    _('Tous les modules'),
                    _('Gestion multi-entrepôts'),
                    _('Support prioritaire'),
                    _('5 utilisateurs'),
                    _('Rapports avancés'),
                ],
                'populaire': True
            },
            {
                'nom': _('Enterprise'),
                'prix': _('Sur devis'),
                'periode': '',
                'features': [
                    _('Personnalisation avancée'),
                    _('Formation dédiée'),
                    _('Support 24/7'),
                    _('Utilisateurs illimités'),
                    _('Intégrations API'),
                ],
                'populaire': False
            },
        ]
        
        context['forfaits'] = forfaits
        context['devise_symbole'] = devise_symbole
        return context
# views.py
from django.views.generic import TemplateView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import DemandeDemo
from .forms import DemandeDemoForm
# views.py - Ajoutez cette vue
from django.core.mail import send_mail
from django.conf import settings

class ContactView(TemplateView):
    template_name = "vitrine/contact.html"
    
    def post(self, request, *args, **kwargs):
        # Récupérer les données du formulaire
        nom = request.POST.get('nom')
        email = request.POST.get('email')
        telephone = request.POST.get('telephone')
        sujet = request.POST.get('sujet')
        message = request.POST.get('message')
        entreprise = request.POST.get('entreprise')
        
        # Envoyer l'email
        try:
            send_mail(
                f"Contact CongoERP - {sujet}",
                f"""
                Nouveau message de contact:
                
                Nom: {nom}
                Entreprise: {entreprise}
                Email: {email}
                Téléphone: {telephone}
                Sujet: {sujet}
                
                Message:
                {message}
                """,
                settings.DEFAULT_FROM_EMAIL,
                ['shadarijerome13@gmail.com'],
                fail_silently=False,
            )
            messages.success(request, "Votre message a été envoyé avec succès !")
        except Exception as e:
            messages.error(request, "Une erreur est survenue. Veuillez réessayer.")
        
        return self.get(request, *args, **kwargs)

class DemandeDemoCreateView(CreateView):
    model = DemandeDemo
    form_class = DemandeDemoForm
    template_name = "vitrine/demo.html"
    
    def get_success_url(self):
        # 🔥 CORRECTION : Rediriger vers la page de succès
        return reverse_lazy('vitrine:demo_success')
    
    def form_valid(self, form):
        # Sauvegarder l'instance
        response = super().form_valid(form)
        
        # Envoyer l'email de notification
        try:
            self.object.envoyer_notification_admin()
            print(f"Email envoyé à l'admin pour la demande de {self.object.nom}")
        except Exception as e:
            print(f"Erreur envoi email: {e}")
        
        # 🔥 CORRECTION : Ajouter le message AVANT la redirection
        messages.success(
            self.request, 
            "Votre demande a été envoyée avec succès à shadarijerome13@gmail.com ! Nous vous contacterons rapidement."
        )
        
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, "Veuillez corriger les erreurs dans le formulaire.")
        return super().form_invalid(form)

class DemoSuccessView(TemplateView):
    template_name = "vitrine/demo_success.html"
    
    def get(self, request, *args, **kwargs):
        # 🔥 CORRECTION : Vérifier s'il y a un message de succès
        # Si non, rediriger vers la page de démo
        storage = messages.get_messages(request)
        has_success_message = any(message.tags == 'success' for message in storage)
        
        if not has_success_message:
            return redirect('vitrine:demo')
        
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 🔥 Ajouter des données supplémentaires si besoin
        context['page_title'] = "Demande Envoyée - CongoERP"
        return context
    
    
    
from django.views.generic.base import TemplateView
from django.http import HttpResponse

class RobotsTxtView(TemplateView):
    template_name = "vitrine/robots.txt"
    content_type = "text/plain"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["domain"] = "https://congoerp-shad-954o.onrender.com"
        return context