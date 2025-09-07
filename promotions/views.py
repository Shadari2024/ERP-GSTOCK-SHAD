from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from parametres.mixins import EntrepriseAccessMixin
from .models import Promotion
from .forms import PromotionForm, PromotionLigneFormSet
from django.views.generic import TemplateView, View
from django.db.models import Count, Sum, Q
from django.utils import timezone
from django.http import JsonResponse
from django.db import models
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.http import JsonResponse


class PromotionDashboardView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, TemplateView):
    template_name = "promotions/dashboard.html"
    permission_required = "promotions.view_promotion"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.user.entreprise
        
        # Statistiques des promotions
        promotions = Promotion.objects.filter(entreprise=entreprise)
        active_promotions = promotions.filter(statut='active')
        planned_promotions = promotions.filter(statut='planifiee')
        expired_promotions = promotions.filter(statut='expiree')
        
        # Impact des promotions sur les ventes (à adapter selon vos modèles)
        try:
            from ventes.models import Vente, LigneVente
            ventes_avec_promotion = Vente.objects.filter(
                entreprise=entreprise,
                lignevente__promotion__isnull=False
            ).distinct().count()
            
            revenue_promotion = LigneVente.objects.filter(
                promotion__isnull=False,
                vente__entreprise=entreprise
            ).aggregate(total=Sum('montant_total'))['total'] or 0
        except:
            ventes_avec_promotion = 0
            revenue_promotion = 0
        
        # Récupérer la devise principale
        try:
            from parametres.models import ConfigurationSAAS
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except:
            devise_symbole = "€"
        
        context.update({
            "active_promotions_count": active_promotions.count(),
            "planned_promotions_count": planned_promotions.count(),
            "expired_promotions_count": expired_promotions.count(),
            "total_promotions": promotions.count(),
            "ventes_avec_promotion": ventes_avec_promotion,
            "revenue_promotion": revenue_promotion,
            "devise_principale_symbole": devise_symbole,
            "active_promotions": active_promotions[:5],
            "recent_promotions": promotions.order_by('-date_creation')[:5],
        })
        
        return context

class PromotionListView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, ListView):
    model = Promotion
    template_name = "promotions/promotion/list.html"
    permission_required = "promotions.view_promotion"
    context_object_name = "promotions"
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().filter(entreprise=self.request.user.entreprise)
        
        # Filtrage par statut
        statut = self.request.GET.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
            
        return queryset.order_by('-date_creation')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer la devise principale
        try:
            from parametres.models import ConfigurationSAAS
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except:
            devise_symbole = "€"
        
        context["devise_principale_symbole"] = devise_symbole
        return context
from .forms import PromotionForm, PromotionLigneFormSet
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from parametres.mixins import EntrepriseAccessMixin
from promotions.models import Promotion
from STOCK.models import Produit
from parametres.models import ConfigurationSAAS

class PromotionCreateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, CreateView):
    model = Promotion
    form_class = PromotionForm
    template_name = "promotions/promotion/form.html"
    permission_required = "promotions.add_promotion"
    success_url = reverse_lazy('promotions:promotion_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["entreprise"] = self.request.user.entreprise
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.user.entreprise
        
        if self.request.POST:
            formset = PromotionLigneFormSet(self.request.POST, prefix="form")
        else:
            formset = PromotionLigneFormSet(prefix="form")
        
        try:
            produits_queryset = Produit.objects.filter(entreprise=entreprise, actif=True)
            for form in formset:
                if 'produit' in form.fields:
                    form.fields['produit'].queryset = produits_queryset
        except Exception:
            for form in formset:
                if 'produit' in form.fields:
                    form.fields['produit'].queryset = Produit.objects.none()
        
        context["formset"] = formset
        
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except:
            devise_symbole = "€"
        
        context["devise_principale_symbole"] = devise_symbole
        context["entreprise"] = entreprise
        
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["formset"]
        
        if formset.is_valid():
            # 1. Sauvegarder la promotion principale
            self.object = form.save(commit=False)
            self.object.entreprise = self.request.user.entreprise
            self.object.save()
            
            # 2. Sauvegarder le formset avec l'instance de la promotion
            instances = formset.save(commit=False)
            for instance in instances:
                instance.promotion = self.object
                instance.save()
            
            # 3. Supprimer les instances marquées pour suppression
            for instance in formset.deleted_objects:
                instance.delete()
            
            messages.success(self.request, "Promotion créée avec succès.")
            return redirect(self.success_url)
        else:
            messages.error(self.request, "Veuillez corriger les erreurs ci-dessous.")
            return self.form_invalid(form)

class PromotionUpdateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, UpdateView):
    model = Promotion
    form_class = PromotionForm
    template_name = "promotions/promotion/form.html"
    permission_required = "promotions.change_promotion"
    success_url = reverse_lazy('promotions:promotion_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["entreprise"] = self.request.user.entreprise
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.user.entreprise
        
        if self.request.POST:
            context["formset"] = PromotionLigneFormSet(self.request.POST, instance=self.object, prefix="form")
        else:
            context["formset"] = PromotionLigneFormSet(instance=self.object, prefix="form")
        
        if 'formset' in context:
            try:
                from STOCK.models import Produit
                produits_queryset = Produit.objects.filter(entreprise=entreprise)
                for form in context['formset']:
                    if 'produit' in form.fields:
                        form.fields['produit'].queryset = produits_queryset
            except Exception:
                pass
        
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except:
            devise_symbole = "€"
        
        context["devise_principale_symbole"] = devise_symbole
        context["entreprise"] = entreprise
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["formset"]
        
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            
            messages.success(self.request, "Promotion modifiée avec succès.")
            return redirect(self.success_url)
        else:
            messages.error(self.request, "Veuillez corriger les erreurs ci-dessous.")
            return self.form_invalid(form)
# Les autres vues restent inchangées...
class PromotionDetailView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DetailView):
    model = Promotion
    template_name = "promotions/promotion/detail.html"
    permission_required = "promotions.view_promotion"
    context_object_name = "promotion"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer la devise principale
        try:
            from parametres.models import ConfigurationSAAS
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except:
            devise_symbole = "€"
        
        context["devise_principale_symbole"] = devise_symbole
        context["lignes"] = self.object.promotionligne_set.all()
        return context

class PromotionDeleteView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DeleteView):
    model = Promotion
    template_name = "promotions/promotion/confirm_delete.html"
    permission_required = "promotions.delete_promotion"
    success_url = reverse_lazy('promotions:promotion_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, "Promotion supprimée avec succès.")
# In promotions/views.py

from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Promotion

class PromotionActivateView(LoginRequiredMixin, EntrepriseAccessMixin, View):
    def post(self, request, *args, **kwargs):
        promotion = get_object_or_404(Promotion, pk=kwargs['pk'], entreprise=request.user.entreprise)
        promotion.statut = 'active'
        # Explicitly save only the 'statut' field
        promotion.save(update_fields=['statut'])
        messages.success(request, _("Promotion activée avec succès."))
        return redirect('promotions:promotion_list')

    def get(self, request, *args, **kwargs):
        # A GET request should not be used for data modification
        return redirect('promotions:promotion_list')

class PromotionDeactivateView(LoginRequiredMixin, EntrepriseAccessMixin, View):
    def post(self, request, *args, **kwargs):
        promotion = get_object_or_404(Promotion, pk=kwargs['pk'], entreprise=request.user.entreprise)
        promotion.statut = 'inactive'
        # Explicitly save only the 'statut' field
        promotion.save(update_fields=['statut'])
        messages.success(request, _("Promotion désactivée avec succès."))
        return redirect('promotions:promotion_list')

    def get(self, request, *args, **kwargs):
        # A GET request should not be used for data modification
        return redirect('promotions:promotion_list')
    
class PromotionStatsView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, TemplateView):
    template_name = "promotions/dashboard.html"
    permission_required = "promotions.view_promotion"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.user.entreprise
        
        # Récupérer la devise principale
        try:
            from parametres.models import ConfigurationSAAS
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except:
            devise_symbole = "€"
        
        context["devise_principale_symbole"] = devise_symbole
        return context

class PromotionReportView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, TemplateView):
    template_name = "promotions/rapports.html"
    permission_required = "promotions.view_promotion"

class ActivePromotionsAPIView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        entreprise = request.user.entreprise
        promotions = Promotion.objects.filter(
            entreprise=entreprise,
            statut='active',
            date_debut__lte=timezone.now(),
            date_fin__gte=timezone.now()
        ).values('id', 'nom', 'type_promotion', 'valeur')
        
        return JsonResponse(list(promotions), safe=False)

class ProductPromotionsAPIView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        produit_id = kwargs.get('produit_id')
        entreprise = request.user.entreprise
        
        promotions = Promotion.objects.filter(
            entreprise=entreprise,
            statut='active',
            date_debut__lte=timezone.now(),
            date_fin__gte=timezone.now(),
            promotionligne__produit_id=produit_id
        ).distinct().values('id', 'nom', 'type_promotion', 'valeur')
        
        return JsonResponse(list(promotions), safe=False)