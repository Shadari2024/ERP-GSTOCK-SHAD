from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .models import *
from .forms import *
from django.http import HttpResponse
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django.utils import timezone
import datetime
from django.conf import settings

class EntrepriseListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Entreprise
    template_name = 'parametres/entreprise/list.html'
    context_object_name = 'entreprises'
    permission_required = 'parametres.view_entreprise'
    paginate_by = 10

    def get_queryset(self):
        return Entreprise.objects.all().order_by('nom')

class EntrepriseCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Entreprise
    form_class = EntrepriseForm
    template_name = 'parametres/entreprise/form.html'
    permission_required = 'parametres.add_entreprise'
    success_url = reverse_lazy('parametres:entreprise_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Entreprise créée avec succès"))
        return response

class EntrepriseUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Entreprise
    form_class = EntrepriseForm
    template_name = 'parametres/entreprise/form.html'
    permission_required = 'parametres.change_entreprise'
    
    def get_success_url(self):
        return reverse_lazy('parametres:entreprise_detail', kwargs={'slug': self.object.slug})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Entreprise mise à jour avec succès"))
        return response

class EntrepriseDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Entreprise
    template_name = 'parametres/entreprise/detail.html'
    permission_required = 'parametres.view_entreprise'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['abonnement'] = getattr(self.object, 'abonnement', None)
        return context

class DeviseListView(LoginRequiredMixin, ListView):
    model = Devise
    template_name = 'parametres/devise/list.html'
    context_object_name = 'devises'
    paginate_by = 20

    def get_queryset(self):
        return Devise.objects.order_by('code')

class DeviseCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Devise
    fields = ['code', 'nom', 'symbole', 'taux_par_defaut', 'symbole_avant', 'decimales', 'active']
    template_name = 'parametres/devise/form.html'
    permission_required = 'parametres.add_devise'
    success_url = reverse_lazy('parametres:devise_list')

    def form_valid(self, form):
        form.instance.code = form.instance.code.upper()
        response = super().form_valid(form)
        messages.success(self.request, f"Devise {self.object.code} créée avec succès")
        return response

class DeviseUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Devise
    fields = ['nom', 'symbole', 'taux_par_defaut', 'symbole_avant', 'decimales', 'active']
    template_name = 'parametres/devise/form.html'
    permission_required = 'parametres.change_devise'
    success_url = reverse_lazy('parametres:devise_list')

class TauxChangeListView(LoginRequiredMixin, ListView):
    model = TauxChange
    template_name = 'parametres/tauxdechange/list.html'
    context_object_name = 'taux_list'
    paginate_by = 20

    def get_queryset(self):
        return TauxChange.objects.select_related(
            'devise_source', 
            'devise_cible'
        ).order_by('-date_application')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['devises'] = Devise.objects.filter(active=True)
        return context

class TauxChangeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = TauxChange
    fields = ['devise_source', 'devise_cible', 'taux', 'date_application', 'source', 'est_actif']
    template_name = 'parametres/tauxdechange/form.html'
    permission_required = 'parametres.add_tauxchange'
    success_url = reverse_lazy('parametres:tauxchange_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['devise_source'].queryset = Devise.objects.filter(active=True)
        form.fields['devise_cible'].queryset = Devise.objects.filter(active=True)
        form.fields['date_application'].initial = timezone.now().date()
        return form

    def form_valid(self, form):
        if form.cleaned_data['devise_source'] == form.cleaned_data['devise_cible']:
            form.add_error('devise_cible', "La devise source et cible doivent être différentes")
            return self.form_invalid(form)
        return super().form_valid(form)




class TauxChangeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = TauxChange
    fields = ['devise_source', 'devise_cible', 'taux', 'date_application', 'source', 'est_actif']
    template_name = 'parametres/tauxdechange/mod_taux.html'
    permission_required = 'parametres.change_tauxchange'
    success_url = reverse_lazy('parametres:tauxchange_list')

    def form_valid(self, form):
        if form.cleaned_data['devise_source'] == form.cleaned_data['devise_cible']:
            form.add_error('devise_cible', "La devise source et cible doivent être différentes")
            return self.form_invalid(form)
        return super().form_valid(form)

class TauxChangeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = TauxChange
    template_name = 'parametres/tauxdechange/delete.html'
    permission_required = 'parametres.delete_tauxchange'
    success_url = reverse_lazy('parametres:tauxchange_list')





from parametres.utils.conversion import obtenir_taux_conversion

def convertir_devise(request):
    if request.method == 'GET' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            montant = float(request.GET.get('montant', 0))
            devise_source_id = request.GET.get('devise_source')
            devise_cible_id = request.GET.get('devise_cible')
            date = request.GET.get('date')

            # Obtenir le taux et le sens de la conversion
            taux, sens = obtenir_taux_conversion(devise_source_id, devise_cible_id, date)

            # Calculer le montant converti
            montant_converti = montant * taux

            return JsonResponse({
                'montant': round(montant_converti, 6),
                'taux': str(taux),
                'date': date,
                'methode': sens  # Indique si c'est une conversion directe ou inverse
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Requête invalide'}, status=400)


class AbonnementListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Abonnement
    template_name = 'parametres/abonnement/abonnement_list.html'
    context_object_name = 'abonnements'
    permission_required = 'parametres.view_abonnement'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset() # Commence avec le queryset par défaut (tous les objets si pas de filtre)

        if self.request.user.is_superuser:
            # Un super-administrateur peut voir TOUS les abonnements.
            # AJOUTEZ UN ORDER_BY ICI
            return Abonnement.objects.all().select_related('entreprise', 'plan_actuel').order_by('-date_debut') # Ou un autre champ pertinent
        
        elif self.request.current_entreprise:
            # Pour un utilisateur normal, filtrer par son entreprise.
            # ET AJOUTEZ UN ORDER_BY ICI
            return Abonnement.objects.filter(
                entreprise=self.request.current_entreprise
            ).select_related('entreprise', 'plan_actuel').order_by('-date_debut') # Ordonnez par date de début décroissante, par exemple
        
        else:
            messages.warning(self.request, _("Vous n'êtes pas lié à une entreprise pour visualiser les abonnements."))
            return Abonnement.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Vous pouvez ajouter d'autres données au contexte si nécessaire
        # Par exemple, pour distinguer si l'utilisateur est un super-admin
        context['is_superuser'] = self.request.user.is_superuser
        return context

# ... (Vos autres vues AbonnementCreateView, AbonnementUpdateView, etc.)

# parametres/views.py
# parametres/views.py

from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView, TemplateView, FormView
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone # Assurez-vous d'importer timezone

# Assurez-vous d'importer tous les modèles et formulaires nécessaires
from .models import Abonnement, Entreprise, PlanTarification
from .forms import AbonnementForm, EntrepriseSelectForm

# Si vous avez un modèle d'utilisateur personnalisé
from django.contrib.auth import get_user_model
User = get_user_model()


# Ajoutez cette vue si vous ne l'avez pas déjà
class AbonnementExpirerView(TemplateView):
    template_name = 'parametres/abonnement/abonnement_expirer.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('security:connexion') # Ou votre URL de connexion

        if request.user.is_superuser:
            messages.info(request, _("Accès refusé pour les super-administrateurs à cette page d'abonnement expiré."))
            return redirect('security:connexion') # Ou votre URL de tableau de bord admin

        # À ce stade, le middleware a déjà dû gérer request.current_entreprise.
        # Si pour une raison quelconque current_entreprise n'est pas définie ou est None,
        # cela signifie que l'utilisateur n'est pas lié à une entreprise.
        if not hasattr(request, 'current_entreprise') or request.current_entreprise is None:
            messages.error(request, _("Votre compte n'est pas lié à une entreprise. Veuillez contacter l'administrateur."))
            return redirect(reverse('parametres:account_not_linked_to_entreprise')) # Assurez-vous que cette URL existe

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.request, 'current_entreprise') and self.request.current_entreprise:
            context['entreprise_nom'] = self.request.current_entreprise.nom
        else:
            context['entreprise_nom'] = _("votre entreprise")
        return context

# Ajoutez cette vue si vous ne l'avez pas déjà
class EntrepriseSelectView(LoginRequiredMixin, FormView):
    template_name = 'parametres/entreprise/entreprise_select.html'
    form_class = EntrepriseSelectForm
    success_url = reverse_lazy('home') # Redirige vers la page d'accueil après sélection (ou tableau de bord)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Assurez-vous que le queryset est filtré si l'utilisateur n'est pas super-admin et a accès à des entreprises spécifiques
        if not self.request.user.is_superuser:
            # Exemple si l'utilisateur a un ManyToManyField 'entreprises'
            # kwargs['queryset'] = self.request.user.entreprises.all()
            pass # Si seul le super-admin utilise cela, le queryset par défaut est suffisant
        return kwargs

    def form_valid(self, form):
        selected_entreprise = form.cleaned_data['entreprise']
        self.request.session['current_entreprise_id'] = selected_entreprise.id
        messages.success(self.request, _(f"Vous avez sélectionné l'entreprise '{selected_entreprise.nom}'."))
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.session.get('current_entreprise_id'):
            try:
                context['current_selected_entreprise'] = Entreprise.objects.get(pk=self.request.session['current_entreprise_id'])
            except Entreprise.DoesNotExist:
                context['current_selected_entreprise'] = None
        return context


from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import HttpResponseRedirect
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.translation import gettext_lazy as _
import logging
from django.utils import timezone # Make sure timezone is imported

# Assume these models are correctly imported
# from .models import Abonnement, PlanTarification, Entreprise
# from .forms import AbonnementForm

logger = logging.getLogger(__name__)

class AbonnementCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Abonnement
    form_class = AbonnementForm
    template_name = 'parametres/abonnement/abonnement_form.html'
    success_url = reverse_lazy('parametres:abonnement_list')
    permission_required = 'parametres.add_abonnement'
    processing_url = reverse_lazy('parametres:abonnement_processing')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        
        if self.request.user.is_superuser:
            current_entreprise = self.get_current_entreprise()
            if current_entreprise:
                if 'initial' not in kwargs:
                    kwargs['initial'] = {}
                kwargs['initial']['entreprise'] = current_entreprise
        return kwargs

    def get_form(self, form_class=None):
        try:
            form = super().get_form(form_class)
            return form
        except Exception as e:
            logger.error(f"Erreur lors de la création du formulaire: {str(e)}", exc_info=True)
            raise

    def form_valid(self, form):
        try:
            # 1. Call form.save(commit=False) to get the unsaved instance
            #    This is where AbonnementForm's logic for est_actif, prochain_paiement happens
            abonnement = form.save(commit=False)
            
            # 2. Determine and assign the enterprise
            entreprise = self.determine_entreprise(form)
            if not entreprise:
                logger.error("Impossible de déterminer l'entreprise pour l'abonnement")
                messages.error(self.request, _("Aucune entreprise valide n'a pu être déterminée pour l'abonnement."))
                return self.form_invalid(form) 
            
            # 3. Validation for non-superusers
            if not self.request.user.is_superuser:
                user_entreprise = getattr(self.request.user, 'entreprise', None)
                if user_entreprise and user_entreprise != entreprise:
                    raise PermissionDenied(_("Vous ne pouvez pas créer d'abonnement pour cette entreprise"))
                    
            abonnement.entreprise = entreprise
            
            # 4. Save the instance within an atomic transaction
            try:
                with transaction.atomic():
                    abonnement.save() # This performs the actual database save
                    form.save_m2m() # Save ManyToMany data if any (usually handled by form.save() directly)
                    logger.info(f"Abonnement créé: ID {abonnement.id} pour entreprise {entreprise.id}")
            except Exception as e:
                logger.error(f"Erreur lors de la sauvegarde de l'abonnement: {str(e)}")
                messages.error(self.request, _("Une erreur est survenue lors de l'enregistrement de l'abonnement"))
                form.add_error(None, _("Erreur lors de la sauvegarde de l'abonnement."))
                return self.form_invalid(form)
                
            # 5. Update session cache (only after successful database save)
            if self.request and hasattr(self.request, 'session'):
                if 'current_abonnement_id' in self.request.session:
                    del self.request.session['current_abonnement_id']
                self.request.session['new_abonnement_id'] = abonnement.id
            
            messages.success(self.request, _("L'abonnement a été créé avec succès."))
            return HttpResponseRedirect(self.get_success_url())
            
        except PermissionDenied as e:
            logger.warning(f"Permission denied: {str(e)}")
            messages.error(self.request, str(e))
            return self.form_invalid(form)
        except Exception as e:
            logger.error(f"Erreur création abonnement: {str(e)}", exc_info=True)
            messages.error(self.request, _("Une erreur est survenue lors de la création de l'abonnement."))
            form.add_error(None, str(e))
            return self.form_invalid(form)

    def determine_entreprise(self, form):
        # ... (unchanged)
        entreprise_form = form.cleaned_data.get('entreprise')
        if entreprise_form:
            return entreprise_form
            
        if hasattr(self.request.user, 'entreprise') and self.request.user.entreprise:
            return self.request.user.entreprise
            
        current_entreprise = self.get_current_entreprise()
        if current_entreprise:
            return current_entreprise
            
        return None

    def get_context_data(self, **kwargs):
        # ... (unchanged)
        context = super().get_context_data(**kwargs)
        context.update({
            'current_entreprise': self.get_current_entreprise(),
            'is_superuser': self.request.user.is_superuser,
            'now': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'title': _("Créer un nouvel abonnement")
        })
        return context

    def get_current_entreprise(self):
        # ... (unchanged)
        if hasattr(self.request, 'current_entreprise') and self.request.current_entreprise:
            return self.request.current_entreprise
            
        if hasattr(self.request.user, 'entreprise') and self.request.user.entreprise:
            return self.request.user.entreprise
            
        if self.request.user.is_superuser and 'current_entreprise_id' in self.request.session:
            try:
                return Entreprise.objects.get(pk=self.request.session['current_entreprise_id'])
            except Entreprise.DoesNotExist:
                logger.warning("Entreprise en session introuvable")
                return None
                
        return None

class AbonnementDeleteView(PermissionRequiredMixin, DeleteView):
    model = Abonnement
    template_name = 'parametres/abonnement/abonnement_confirm_delete.html'
    permission_required = 'parametres.delete_abonnement'
    success_url = reverse_lazy('parametres:abonnement_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Suppression d\'abonnement')
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _(
            'L\'abonnement a été désactivé avec succès.'
        ))
        return response

class AbonnementListView(LoginRequiredMixin, ListView):
    model = Abonnement
    template_name = 'parametres/abonnement/abonnement_list.html'
    context_object_name = 'abonnements'
    ordering = ['-date_debut']  # Tri par défaut
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('plan_actuel')
        # Ajoutez ici votre logique de filtrage par entreprise
        return queryset.order_by('-date_debut')
    
    def get_queryset(self):
        # Précharge les relations pour éviter les requêtes multiples
        queryset = Abonnement.objects.select_related(
            'entreprise',
            'plan_actuel'  # Ceci est crucial pour afficher le plan
        ).order_by('-date_debut')
        
        # Filtrage par entreprise
        if not self.request.user.is_superuser:
            if hasattr(self.request.user, 'entreprise') and self.request.user.entreprise:
                return queryset.filter(entreprise=self.request.user.entreprise)
            elif hasattr(self.request, 'current_entreprise') and self.request.current_entreprise:
                return queryset.filter(entreprise=self.request.current_entreprise)
            return Abonnement.objects.none()
        
        # Pour les superusers - filtre par entreprise sélectionnée si disponible
        if hasattr(self.request, 'current_entreprise') and self.request.current_entreprise:
            return queryset.filter(entreprise=self.request.current_entreprise)
        
        return queryset  # Tous les abonnements pour superuser sans filtre

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ajoute l'entreprise courante au contexte
        if hasattr(self.request, 'current_entreprise'):
            context['current_entreprise'] = self.request.current_entreprise
        elif hasattr(self.request.user, 'entreprise'):
            context['current_entreprise'] = self.request.user.entreprise
        
        # Vérification des permissions pour les boutons d'action
        context['can_add'] = self.request.user.has_perm('parametres.add_abonnement')
        context['can_change'] = self.request.user.has_perm('parametres.change_abonnement')
        context['can_delete'] = self.request.user.has_perm('parametres.delete_abonnement')
        
        return context
    
    
class AbonnementUpdateView(PermissionRequiredMixin, UpdateView):
    model = Abonnement
    form_class = AbonnementForm
    template_name = 'parametres/abonnement/abonnement_form.html'
    permission_required = 'parametres.change_abonnement'
    success_url = reverse_lazy('parametres:abonnement_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_queryset(self):
        # S'assure que l'utilisateur ne peut modifier que les abonnements de son entreprise
        if self.request.current_entreprise:
            return Abonnement.objects.filter(entreprise=self.request.current_entreprise)
        return Abonnement.objects.none() # Si pas d'entreprise, ne rien retourner

    def form_valid(self, form):
        # L'entreprise est déjà sur l'instance de l'objet, pas besoin de la réassigner.
        # On peut simplement appeler la méthode parent.
        response = super().form_valid(form)
        messages.success(self.request, _("Abonnement mis à jour avec succès."))
        return response

    def form_invalid(self, form):
        messages.error(self.request, _("Erreur lors de la mise à jour de l'abonnement. Veuillez vérifier les informations."))
        return super().form_invalid(form)


# ... (vos autres vues AbonnementListView, AbonnementDetailView, HistoriqueAbonnement, etc.)

class AbonnementDetailView(PermissionRequiredMixin, DetailView):
    model = Abonnement
    template_name = 'parametres/abonnement/abonnement_detail.html'
    permission_required = 'parametres.view_abonnement'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['prochain_paiement'] = self.object.prochain_paiement
        return context

def verifier_date_abonnement(request):
    """API pour vérifier si une date de paiement est valide"""
    date = request.GET.get('date')
    entreprise_id = request.GET.get('entreprise')
    
    if not date or not entreprise_id:
        return JsonResponse({'error': 'Date et entreprise requis'}, status=400)
    
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        entreprise = Entreprise.objects.get(id=entreprise_id)
        
        # Vérifier si l'entreprise a déjà un abonnement actif
        abonnement_actif = Abonnement.objects.filter(
            entreprise=entreprise,
            date_fin__isnull=True
        ).first()
        
        if abonnement_actif:
            return JsonResponse({
                'disponible': False,
                'message': _('Une date de paiement est déjà définie pour cette entreprise')
            })
        
        return JsonResponse({
            'disponible': True,
            'message': _('Date de paiement disponible')
        })
    except (ValueError, Entreprise.DoesNotExist) as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)

class HistoriqueAbonnementListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = HistoriqueAbonnement
    template_name = 'parametres/abonnement/historique.html'
    permission_required = 'parametres.view_historiqueabonnement'
    paginate_by = 20

    def get_queryset(self):
        return super().get_queryset().select_related('abonnement__entreprise', 'utilisateur')
    
    
    
    
from django.conf import settings
import pytz   

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from .models import PlanTarification
from .forms import PlanTarificationForm

class PlanTarificationListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = PlanTarification
    template_name = 'parametres/plantarification/list.html'
    context_object_name = 'plans'
    permission_required = 'parametres.view_plantarification'
    paginate_by = 10

    def get_queryset(self):
        return PlanTarification.objects.all().order_by('prix_mensuel')
    
from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
import pytz # Assuming pytz is installed and used for timezones
from django.conf import settings # Assuming settings is used for LANGUAGES



# Assuming you have a logger configured
import logging
logger = logging.getLogger(__name__)
class ConfigurationSAASUpdateView(LoginRequiredMixin, UpdateView):
    model = ConfigurationSAAS
    fields = [
        # Le champ 'modules_actifs' a été complètement retiré de cette liste.
        'fuseau_horaire',
        'langue',
        'expiration_session',
        'complexite_mdp',
        'devise_principale'
    ]
    template_name = 'parametres/config_saas_form.html'
    success_url = reverse_lazy('config_saas')
    
    def get_object(self):
        # Provide a default primary currency when creating a new ConfigurationSAAS
        default_devise = None
        try:
            # Try to get the first active currency as a sensible default
            # This ensures that a primary currency is always set upon first creation.
            default_devise = Devise.objects.filter(active=True).first()
            if not default_devise:
                logger.warning("No active currency found to set as default_devise for new ConfigurationSAAS. Please ensure active currencies are available.")
        except Exception as e:
            logger.error(f"Failed to retrieve a default currency for SAAS config: {e}")
            # If an error occurs (e.g., Devise table is empty), default_devise remains None.
            # The system will still flag "No primary currency configured", which is correct in this case.

        obj, created = ConfigurationSAAS.objects.get_or_create(
            entreprise=self.request.entreprise,
            defaults={
                'fuseau_horaire': 'UTC', # Sensible default
                'langue': 'fr',          # Sensible default
                'expiration_session': 30, # Sensible default
                'complexite_mdp': ConfigurationSAAS.ComplexiteMDP.MOYEN, # Sensible default
                'devise_principale': default_devise # Set the default here if a new object is created
            }
        )
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ensure these are correctly populated for the template
        context['timezones'] = pytz.all_timezones
        context['languages'] = settings.LANGUAGES
        context['devises'] = Devise.objects.filter(active=True) # Pass only active currencies to the form
        return context
    
    def form_valid(self, form):
        # Save the form instance to update the ConfigurationSAAS object
        self.object = form.save()
        messages.success(self.request, _("Configuration SAAS mise à jour avec succès"))
        return super().form_valid(form)

from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Entreprise

class EntrepriseSelectView(LoginRequiredMixin, ListView):
    template_name = 'parametres/entreprise_select.html'
    model = Entreprise
    
    def get_queryset(self):
        return self.request.user.entreprises.all()
    
    def post(self, request):
        entreprise_id = request.POST.get('entreprise')
        entreprise = self.get_queryset().filter(id=entreprise_id).first()
        if entreprise:
            request.session['current_entreprise_id'] = entreprise.id
            return redirect('dashboard')
        return self.get(request)



# views.py
class PlanTarificationCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = PlanTarification
    form_class = PlanTarificationForm
    template_name = 'parametres/plantarification/form.html'
    permission_required = 'parametres.add_plantarification'
    success_url = reverse_lazy('parametres:plantarification_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['installed_apps'] = [app.split('.')[0] for app in settings.INSTALLED_APPS 
                                   if not app.startswith('django.')]
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Plan tarifaire créé avec succès"))
        return response

class PlanTarificationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = PlanTarification
    form_class = PlanTarificationForm
    template_name = 'parametres/plantarification/form.html'
    permission_required = 'parametres.change_plantarification'
    success_url = reverse_lazy('parametres:plantarification_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _("Plan tarifaire mis à jour avec succès"))
        return response

class PlanTarificationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = PlanTarification
    template_name = 'parametres/plantarification/confirm_delete.html'
    permission_required = 'parametres.delete_plantarification'
    success_url = reverse_lazy('parametres:plantarification_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, _("Plan tarifaire supprimé avec succès"))
        return super().delete(request, *args, **kwargs)
    
    
    
    # parametres/views.py

# ... (vos imports existants)

from django.views.generic import TemplateView # Importez TemplateView

# ... (vos autres vues comme AbonnementListView, AbonnementCreateView, etc.)

# parametres/views.py - Dans AbonnementExpirerView

from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.urls import reverse # Importez reverse si vous l'utilisez pour les redirections

class AbonnementExpirerView(TemplateView):
    template_name = 'parametres/abonnement/abonnement_expirer.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            # Si l'utilisateur n'est pas authentifié, rediriger vers la page de connexion
            # Utilisez le nom correct de votre URL de connexion (ex: 'account_login' ou 'security:my_custom_login')
            return redirect(reverse('security:connexion')) 

        if request.user.is_superuser:
            # Un super-admin ne devrait pas être sur cette page, rediriger vers un tableau de bord.
            messages.info(request, _("Accès refusé pour les super-administrateurs à cette page d'abonnement expiré."))
            return redirect('admin:index') # Ou votre URL de tableau de bord d'administration

        # --- Gérer l'absence de request.current_entreprise de manière sûre ---
        # Si le middleware est exempté, request.current_entreprise pourrait ne pas être défini.
        # Nous devons le définir ici si l'utilisateur est authentifié et non super-admin.
        if not hasattr(request, 'current_entreprise') or request.current_entreprise is None:
            if hasattr(request.user, 'entreprise') and request.user.entreprise:
                request.current_entreprise = request.user.entreprise
            else:
                # L'utilisateur est authentifié, non super-admin, mais pas lié à une entreprise.
                messages.error(request, _("Votre compte n'est pas lié à une entreprise. Veuillez contacter l'administrateur."))
                return redirect(reverse('security:account_not_linked_to_entreprise')) # Assurez-vous que cette URL existe

        # À ce stade, request.current_entreprise devrait être défini (ou l'utilisateur a été redirigé).
        # Vous pouvez maintenant accéder en toute sécurité à request.current_entreprise.
        # Si vous voulez vérifier des choses comme l'abonnement même si l'utilisateur est sur cette page d'expiration,
        # c'est ici que vous le feriez, mais normalement, s'ils sont ici, c'est que l'abonnement est déjà expiré.

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Vous pouvez maintenant accéder à request.current_entreprise en toute sécurité ici
        if hasattr(self.request, 'current_entreprise') and self.request.current_entreprise:
            context['entreprise_nom'] = self.request.current_entreprise.nom
            # Optionnel: Récupérer le dernier abonnement expiré si l'entreprise en a un
            # try:
            #     context['dernie_abonnement'] = self.request.current_entreprise.abonnement_courant.order_by('-date_fin').first()
            # except AttributeError:
            #     context['dernie_abonnement'] = None # Au cas où abonnement_courant ne serait pas défini
        else:
            context['entreprise_nom'] = _("votre entreprise") # Fallback
        return context
    
from django.views.generic import FormView # Importez FormView
class EntrepriseSelectView(LoginRequiredMixin, FormView):
    template_name = 'parametres/entreprise/entreprise_select.html'
    form_class = EntrepriseSelectForm
    success_url = '/' # Redirige vers la page d'accueil après sélection

    def form_valid(self, form):
        selected_entreprise = form.cleaned_data['entreprise']
        # Sauvegarde l'ID de l'entreprise sélectionnée dans la session
        self.request.session['current_entreprise_id'] = selected_entreprise.id
        messages.success(self.request, _(f"Vous avez sélectionné l'entreprise '{selected_entreprise.nom}'."))
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Filtrez le queryset pour n'afficher que les entreprises auxquelles l'utilisateur a accès
        # (si l'utilisateur n'est pas super-admin)
        if not self.request.user.is_superuser:
            # Si un utilisateur est lié à plusieurs entreprises (par un ManyToMany ou autre)
            # kwargs['queryset'] = self.request.user.entreprises.all()
            # Pour l'instant, si vous gérez un seul ForeignKey, ce cas est moins pertinent pour un non-super-admin.
            # Laissez le queryset par défaut (toutes les entreprises) si seul le super-admin utilise ce sélecteur.
            pass
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.session.get('current_entreprise_id'):
            try:
                context['current_selected_entreprise'] = Entreprise.objects.get(pk=self.request.session['current_entreprise_id'])
            except Entreprise.DoesNotExist:
                context['current_selected_entreprise'] = None
        return context
    
    
#module
class ModuleListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Module
    template_name = 'parametres/module/list.html'
    context_object_name = 'modules'
    permission_required = 'parametres.view_module'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search')
        categorie = self.request.GET.get('categorie')

        # Filtrer par applications installées
        installed_apps = [app.split('.')[0] for app in settings.INSTALLED_APPS]
        queryset = queryset.filter(code__in=installed_apps)

        if search_query:
            queryset = queryset.filter(
                Q(nom__icontains=search_query) | 
                Q(code__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        if categorie:
            queryset = queryset.filter(categorie=categorie)
        
        return queryset.order_by('ordre_affichage')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Module.CategoriesModule.choices
        context['search_query'] = self.request.GET.get('search', '')
        context['selected_categorie'] = self.request.GET.get('categorie', '')
        
        # Ajouter la liste des apps installées pour référence
        context['installed_apps'] = [app.split('.')[0] for app in settings.INSTALLED_APPS]
        return context

class ModuleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Module
    form_class = ModuleForm
    template_name = 'parametres/module/create.html'
    permission_required = 'parametres.add_module'
    success_url = reverse_lazy('parametres:module_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Module {self.object.nom} créé avec succès!")
        return response

class ModuleUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Module
    form_class = ModuleForm
    template_name = 'parametres/module/update.html'
    permission_required = 'parametres.change_module'
    success_url = reverse_lazy('parametres:module_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Module {self.object.nom} mis à jour avec succès!")
        return response

class ModuleDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Module
    template_name = 'parametres/module/detail.html'
    permission_required = 'parametres.view_module'
    context_object_name = 'module'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['dependances'] = DependanceModule.objects.filter(
            Q(module_principal=self.object) | Q(module_dependance=self.object))
        context['entreprises'] = ModuleEntreprise.objects.filter(module=self.object)
        return context

class ModuleDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Module
    template_name = 'parametres/module/delete.html'
    permission_required = 'parametres.delete_module'
    success_url = reverse_lazy('parametres:module_list')

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, f"Module {self.object.nom} supprimé avec succès!")
        return response

# Views pour ModuleEntreprise
class ModuleEntrepriseCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ModuleEntreprise
    form_class = ModuleEntrepriseForm
    template_name = 'parametres/module/entreprise/create.html'
    permission_required = 'parametres.add_moduleentreprise'

    def get_success_url(self):
        return reverse_lazy('parametres:module_detail', kwargs={'pk': self.object.module.pk})

    def form_valid(self, form):
        form.instance.module = get_object_or_404(Module, pk=self.kwargs['module_pk'])
        response = super().form_valid(form)
        messages.success(self.request, "Module activé pour l'entreprise avec succès!")
        return response

class ModuleEntrepriseUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ModuleEntreprise
    form_class = ModuleEntrepriseForm
    template_name = 'parametres/module/entreprise/update.html'
    permission_required = 'parametres.change_moduleentreprise'

    def get_success_url(self):
        return reverse_lazy('parametres:module_detail', kwargs={'pk': self.object.module.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Association Module/Entreprise mise à jour avec succès!")
        return response

# Views pour DependanceModule
class DependanceModuleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = DependanceModule
    form_class = DependanceModuleForm
    template_name = 'parametres/module/dependance/create.html'
    permission_required = 'parametres.add_dependancemodule'

    def get_success_url(self):
        return reverse_lazy('parametres:module_detail', kwargs={'pk': self.object.module_principal.pk})

    def get_initial(self):
        initial = super().get_initial()
        if 'module_pk' in self.kwargs:
            initial['module_principal'] = get_object_or_404(Module, pk=self.kwargs['module_pk'])
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Dépendance créée avec succès!")
        return response

class DependanceModuleDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = DependanceModule
    template_name = 'parametres/module/dependance/delete.html'
    permission_required = 'parametres.delete_dependancemodule'

    def get_success_url(self):
        return reverse_lazy('parametres:module_detail', kwargs={'pk': self.object.module_principal.pk})

    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, "Dépendance supprimée avec succès!")
        return response