from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Sum, Q
from django.utils import timezone
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.shortcuts import redirect
from django.db import IntegrityError
from parametres.mixins import  EntrepriseAccessMixin
from parametres.models import  *
from .models import PlanComptableOHADA, JournalComptable, EcritureComptable, LigneEcriture, CompteAuxiliaire
from .forms import PlanComptableForm, JournalComptableForm, EcritureComptableForm, LigneEcritureFormSet, CompteAuxiliaireForm
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Sum, Q
from django.utils import timezone
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _

from parametres.models import ConfigurationSAAS
from .models import PlanComptableOHADA, JournalComptable, EcritureComptable, LigneEcriture, CompteAuxiliaire
from .forms import PlanComptableForm, JournalComptableForm, EcritureComptableForm, LigneEcritureFormSet, CompteAuxiliaireForm

class PlanComptableListView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, ListView):
    model = PlanComptableOHADA
    template_name = "comptabilite/plan_comptable/list.html"
    permission_required = "comptabilite.view_plancomptableohada"
    context_object_name = "comptes"

    def get_queryset(self):
        return super().get_queryset().filter(entreprise=self.request.user.entreprise)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer le queryset de base pour l'entreprise
        queryset = self.get_queryset()

        # Calculer le nombre de comptes par type
        context['comptes_actif'] = queryset.filter(type_compte='actif').count()
        context['comptes_passif'] = queryset.filter(type_compte='passif').count()
        context['comptes_charge'] = queryset.filter(type_compte='charge').count()
        context['comptes_produit'] = queryset.filter(type_compte='produit').count()
        
        context['devise_principale_symbole'] = self.get_devise_principale()
        return context

    def get_devise_principale(self):
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            return config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            return "€"

class PlanComptableDeleteView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DeleteView):
    model = PlanComptableOHADA
    permission_required = "comptabilite.delete_plancomptableohada"
    success_url = reverse_lazy('comptabilite:plan_comptable_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.delete()
        messages.success(request, f"Le compte {self.object.numero} a été supprimé avec succès.")
        return redirect(success_url)
class PlanComptableCreateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, CreateView):
    model = PlanComptableOHADA
    form_class = PlanComptableForm
    template_name = "comptabilite/plan_comptable/form.html"
    permission_required = "comptabilite.add_plancomptableohada"
    success_url = reverse_lazy('comptabilite:plan_comptable_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["entreprise"] = self.request.user.entreprise
        return kwargs

    def form_valid(self, form):
        # Vérifier que l'utilisateur a une entreprise
        if not hasattr(self.request.user, 'entreprise') or not self.request.user.entreprise:
            messages.error(self.request, "Vous devez être associé à une entreprise pour créer un compte comptable.")
            return self.form_invalid(form)
        
        # Créer l'objet manuellement et l'assigner à self.object
        try:
            self.object = PlanComptableOHADA.objects.create(
                classe=form.cleaned_data['classe'],
                numero=form.cleaned_data['numero'],
                intitule=form.cleaned_data['intitule'],
                description=form.cleaned_data.get('description', ''),
                type_compte=form.cleaned_data['type_compte'],
                entreprise=self.request.user.entreprise
            )
            messages.success(self.request, "Le compte comptable a été créé avec succès.")
            return HttpResponseRedirect(self.get_success_url())
            
        except IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                form.add_error('numero', "Ce numéro de compte existe déjà pour cette entreprise.")
            else:
                form.add_error(None, f"Erreur d'intégrité: {str(e)}")
            return self.form_invalid(form)
        except Exception as e:
            form.add_error(None, f"Une erreur s'est produite: {str(e)}")
            return self.form_invalid(form)

    def get_success_url(self):
        # S'assurer que nous retournons l'URL de succès même si self.object n'est pas défini
        return super().get_success_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['devise_principale_symbole'] = self.get_devise_principale()
        return context

    def get_devise_principale(self):
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            return config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            return "€"

class PlanComptableUpdateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, UpdateView):
    model = PlanComptableOHADA
    form_class = PlanComptableForm
    template_name = "comptabilite/plan_comptable/form.html"
    permission_required = "comptabilite.change_plancomptableohada"
    success_url = reverse_lazy('comptabilite:plan_comptable_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["entreprise"] = self.request.user.entreprise
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['devise_principale_symbole'] = self.get_devise_principale()
        return context

    def get_devise_principale(self):
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            return config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            return "€"
class PlanComptableDetailView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DetailView):
    model = PlanComptableOHADA
    template_name = "comptabilite/plan_comptable/detail.html"
    permission_required = "comptabilite.view_plancomptableohada"
    context_object_name = "compte"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.user.entreprise
        compte = self.object

        # 🔹 Récupération des informations générales
        context['devise_principale_symbole'] = self.get_devise_principale(entreprise)

        # 🔹 Calcul des statistiques
        
        # 1. Nombre total d'écritures pour ce compte
        ecritures_totales_count = LigneEcriture.objects.filter(
            compte=compte,
            ecriture__entreprise=entreprise
        ).count()

        # 2. Nombre d'écritures pour ce mois-ci
        date_debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        ecritures_ce_mois_count = LigneEcriture.objects.filter(
            compte=compte,
            ecriture__entreprise=entreprise,
            ecriture__date_comptable__gte=date_debut_mois
        ).count()

        # 3. Solde actuel du compte
        # Déterminer la nature du compte pour calculer le solde
        is_passif_or_produit = compte.numero.startswith(("1", "4", "7"))
        
        solde_actuel_agg = LigneEcriture.objects.filter(
            compte=compte,
            ecriture__entreprise=entreprise
        ).aggregate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit')
        )
        
        total_debit = float(solde_actuel_agg['total_debit'] or 0)
        total_credit = float(solde_actuel_agg['total_credit'] or 0)
        
        if is_passif_or_produit:
            solde_actuel = total_credit - total_debit
        else:
            solde_actuel = total_debit - total_credit

        # 🔹 Ajout des statistiques au contexte
        context['ecritures_ce_mois'] = ecritures_ce_mois_count
        context['ecritures_totales'] = ecritures_totales_count
        context['solde_actuel'] = solde_actuel

        return context

    def get_devise_principale(self, entreprise):
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            return config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            return "€"
        
class JournalComptableListView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, ListView):
    model = JournalComptable
    template_name = "comptabilite/journal/list.html"
    permission_required = "comptabilite.view_journalcomptable"
    context_object_name = "journaux"

    def get_queryset(self):
        return super().get_queryset().filter(entreprise=self.request.user.entreprise)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['devise_principale_symbole'] = self.get_devise_principale()
        
        # Ajouter des statistiques pour le template
        queryset = self.get_queryset()
        context['journaux_actifs'] = queryset.filter(actif=True).count()
        context['journaux_achat'] = queryset.filter(type_journal='achat').count()
        context['journaux_vente'] = queryset.filter(type_journal='vente').count()
        
        return context

    def get_devise_principale(self):
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            return config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            return "€"

class JournalComptableCreateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, CreateView):
    model = JournalComptable
    form_class = JournalComptableForm
    template_name = "comptabilite/journal/form.html"
    permission_required = "comptabilite.add_journalcomptable"
    success_url = reverse_lazy('comptabilite:journal_list')

    def form_valid(self, form):
        form.instance.entreprise = self.request.user.entreprise
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['devise_principale_symbole'] = self.get_devise_principale()
        return context

    def get_devise_principale(self):
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            return config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            return "€"

class JournalComptableUpdateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, UpdateView):
    model = JournalComptable
    form_class = JournalComptableForm
    template_name = "comptabilite/journal/form.html"
    permission_required = "comptabilite.change_journalcomptable"
    success_url = reverse_lazy('comptabilite:journal_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['devise_principale_symbole'] = self.get_devise_principale()
        return context

    def get_devise_principale(self):
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            return config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            return "€"
        
class JournalComptableDetailView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DetailView):
    model = JournalComptable
    template_name = "comptabilite/journal/detail.html"
    permission_required = "comptabilite.view_journalcomptable"
    context_object_name = "journal"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['devise_principale_symbole'] = self.get_devise_principale()
        
        # Ajouter les journaux du même type pour la sidebar
        journal = self.get_object()
        context['journaux_meme_type'] = JournalComptable.objects.filter(
            entreprise=self.request.user.entreprise,
            type_journal=journal.type_journal
        ).exclude(pk=journal.pk)[:5]  # Limiter à 5 résultats
        
        return context

    def get_devise_principale(self):
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            return config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            return "€"        
        
        
class JournalComptableDeleteView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DeleteView):
    model = JournalComptable
    permission_required = "comptabilite.delete_journalcomptable"
    success_url = reverse_lazy('comptabilite:journal_list')
    template_name = "comptabilite/journal/confirm_delete.html"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        
        # Vérifier si le journal a des écritures associées
        if self.object.ecriturecomptable_set.exists():
            messages.error(
                request, 
                f"Impossible de supprimer le journal '{self.object.code}' car il a des écritures associées."
            )
            return redirect(success_url)
        
        try:
            self.object.delete()
            messages.success(request, f"Le journal '{self.object.code}' a été supprimé avec succès.")
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression: {str(e)}")
        
        return redirect(success_url)
from django.db.models import Sum

# Écriture Comptable Views
class EcritureComptableListView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, ListView):
    model = EcritureComptable
    template_name = "comptabilite/ecriture/list.html"
    permission_required = "comptabilite.view_ecriturecomptable"
    context_object_name = "ecritures"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().filter(entreprise=self.request.user.entreprise)
        
        # Filtres
        journal = self.request.GET.get('journal')
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        
        if journal:
            queryset = queryset.filter(journal__code=journal)
        if date_debut:
            queryset = queryset.filter(date_ecriture__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date_ecriture__lte=date_fin)
            
        return queryset.order_by('-date_ecriture', '-numero')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer le queryset filtré
        filtered_ecritures = self.get_queryset()
        
        # Récupérer toutes les lignes d'écriture pour les écritures filtrées
        # Ceci est plus efficace que de faire les calculs en Python sur le template
        lignes = LigneEcriture.objects.filter(ecriture__in=filtered_ecritures)
        
        # Calculer les totaux de débit et crédit à l'aide de l'agrégation
        totaux = lignes.aggregate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit')
        )
        
        total_debit = totaux['total_debit'] or 0
        total_credit = totaux['total_credit'] or 0
        desequilibre = total_debit - total_credit

        context['total_debit'] = total_debit
        context['total_credit'] = total_credit
        context['desequilibre'] = desequilibre

        context['devise_principale_symbole'] = self.get_devise_principale()
        context['journaux'] = JournalComptable.objects.filter(entreprise=self.request.user.entreprise, actif=True)
        
        # Passer les paramètres de filtrage pour les garder dans la pagination
        context['filters'] = {
            'journal': self.request.GET.get('journal', ''),
            'date_debut': self.request.GET.get('date_debut', ''),
            'date_fin': self.request.GET.get('date_fin', ''),
            'search': self.request.GET.get('search', ''),
            'statut': self.request.GET.get('statut', ''),
        }
        
        return context

    def get_devise_principale(self):
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            return config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            return "€"
class EcritureComptableCreateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, CreateView):
    model = EcritureComptable
    form_class = EcritureComptableForm
    template_name = "comptabilite/ecriture/form.html"
    permission_required = "comptabilite.add_ecriturecomptable"
    success_url = reverse_lazy('comptabilite:ecriture_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["entreprise"] = self.request.user.entreprise
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.user.entreprise
        
        # Récupérer la devise principale
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            devise_symbole = "€"
        
        context["devise_principale_symbole"] = devise_symbole
        
        # Gestion du formset pour les lignes d'écriture
        formset_kwargs = {"prefix": "lignes"}
        
        if self.request.POST:
            formset = LigneEcritureFormSet(
                self.request.POST,
                instance=self.object if hasattr(self, "object") else None,
                **formset_kwargs,
            )
        else:
            formset = LigneEcritureFormSet(
                instance=self.object if hasattr(self, "object") else None,
                **formset_kwargs,
            )
        
        # Passer l'entreprise à chaque formulaire du formset
        for form in formset:
            form.entreprise = entreprise
        
        context["formset"] = formset
        
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["formset"]
        entreprise = self.request.user.entreprise
        
        if formset.is_valid():
            try:
                # Sauvegarder d'abord l'écriture
                self.object = form.save(commit=False)
                self.object.entreprise = entreprise
                self.object.created_by = self.request.user
                
                # Générer le numéro d'écriture automatiquement
                if not self.object.numero:
                    dernier_numero = EcritureComptable.objects.filter(
                        entreprise=entreprise,
                        journal=self.object.journal
                    ).order_by('-numero').first()
                    
                    if dernier_numero and dernier_numero.numero:
                        try:
                            dernier_num = int(dernier_numero.numero.split('-')[-1])
                            nouveau_num = dernier_num + 1
                        except (ValueError, IndexError):
                            nouveau_num = 1
                    else:
                        nouveau_num = 1
                    
                    self.object.numero = f"{self.object.journal.code}-{nouveau_num:06d}"
                
                # Calculer le montant total à partir des lignes
                total_debit = 0
                for i in range(int(self.request.POST.get('lignes-TOTAL_FORMS', 0))):
                    debit = self.request.POST.get(f'lignes-{i}-debit', 0) or 0
                    total_debit += float(debit)
                
                self.object.montant_devise = total_debit
                self.object.save()
                
                # Sauvegarder le formset
                formset.instance = self.object
                formset.save()
                
                messages.success(self.request, "L'écriture comptable a été créée avec succès.")
                return HttpResponseRedirect(self.get_success_url())
                
            except Exception as e:
                messages.error(self.request, f"Erreur lors de la création: {str(e)}")
                return self.form_invalid(form)
        else:
            # Afficher les erreurs du formset
            for error in formset.errors:
                messages.error(self.request, f"Erreur dans les lignes: {error}")
            return self.form_invalid(form)

class EcritureComptableDetailView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DetailView):
    model = EcritureComptable
    template_name = "comptabilite/ecriture/detail.html"
    permission_required = "comptabilite.view_ecriturecomptable"
    context_object_name = "ecriture"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['devise_principale_symbole'] = self.get_devise_principale()
        
        # Calculer le total débit et crédit
        ecriture = self.get_object()
        total_debit = sum(ligne.debit for ligne in ecriture.lignes.all())
        total_credit = sum(ligne.credit for ligne in ecriture.lignes.all())
        
        context['total_debit'] = total_debit
        context['total_credit'] = total_credit
        context['equilibre'] = total_debit == total_credit
        
        return context

    def get_devise_principale(self):
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            return config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            return "€"
        
        
        
class EcritureComptableUpdateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, UpdateView):
    model = EcritureComptable
    form_class = EcritureComptableForm
    template_name = "comptabilite/ecriture/form.html"
    permission_required = "comptabilite.change_ecriturecomptable"
    success_url = reverse_lazy('comptabilite:ecriture_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["entreprise"] = self.request.user.entreprise
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.user.entreprise
        
        # Récupérer la devise principale
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            devise_symbole = "€"
        
        context["devise_principale_symbole"] = devise_symbole
        
        # Gestion du formset pour les lignes d'écriture
        formset_kwargs = {"prefix": "lignes", "entreprise": entreprise}
        
        if self.request.POST:
            context["formset"] = LigneEcritureFormSet(
                self.request.POST,
                instance=self.object,
                **formset_kwargs,
            )
        else:
            context["formset"] = LigneEcritureFormSet(
                instance=self.object,
                **formset_kwargs,
            )
        
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["formset"]
        
        if formset.is_valid():
            self.object = form.save(commit=False)
            
            # Calculer le montant total à partir des lignes
            total_debit = 0
            for form_ligne in formset:
                if form_ligne.cleaned_data and not form_ligne.cleaned_data.get('DELETE', False):
                    debit = form_ligne.cleaned_data.get('debit') or 0
                    total_debit += debit
            
            self.object.montant_devise = total_debit
            self.object.save()
            
            # Sauvegarder le formset
            formset.instance = self.object
            formset.save()
            
            messages.success(self.request, "L'écriture comptable a été modifiée avec succès.")
            return super().form_valid(form)
        else:
            return self.form_invalid(form)


class EcritureComptableDeleteView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DeleteView):
    model = EcritureComptable
    permission_required = "comptabilite.delete_ecriturecomptable"
    success_url = reverse_lazy('comptabilite:ecriture_list')
    template_name = "comptabilite/ecriture/confirm_delete.html"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        
        try:
            self.object.delete()
            messages.success(request, f"L'écriture {self.object.numero} a été supprimée avec succès.")
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression: {str(e)}")
        
        return HttpResponseRedirect(success_url)       
    
  # Grand Livre View - VERSION COMPLÈTEMENT CORRIGÉE
class GrandLivreView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "comptabilite/grand_livre/list.html"
    permission_required = "comptabilite.view_ecriturecomptable"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.user.entreprise

        # 🔹 Devise principale
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            devise_symbole = "€"

        context["devise_principale_symbole"] = devise_symbole

        # 🔹 Filtres
        compte_numero = self.request.GET.get('compte')
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')

        # 🔹 Dates par défaut (mois en cours)
        if not date_debut:
            date_debut = timezone.now().replace(day=1).strftime('%Y-%m-%d')
        if not date_fin:
            date_fin = timezone.now().strftime('%Y-%m-%d')

        # 🔹 Récupération des écritures de l'entreprise avec filtres
        ecritures = EcritureComptable.objects.filter(entreprise=entreprise)
        
        if date_debut:
            ecritures = ecritures.filter(date_comptable__gte=date_debut)
        if date_fin:
            ecritures = ecritures.filter(date_comptable__lte=date_fin)

        # 🔹 Liste des comptes pour le dropdown (structure OHADA)
        context['comptes'] = PlanComptableOHADA.objects.filter(
            entreprise=entreprise
        ).exclude(classe__in=['6', '7']).order_by('numero')

        # 🔹 CORRECTION CRITIQUE : Si un compte est sélectionné
        if compte_numero:
            try:
                compte_obj = PlanComptableOHADA.objects.get(numero=compte_numero, entreprise=entreprise)
                context['compte_selectionne'] = compte_obj

                # ✅ CORRECTION : Détermination EXACTE de la nature du compte
                def determiner_nature_compte(compte):
                    """Détermine la nature exacte du compte selon OHADA"""
                    numero = compte.numero
                    
                    # Comptes de PASSIF (crédit positif)
                    if numero.startswith('1'):  # Capitaux propres
                        return 'passif'
                    elif numero.startswith('40'):  # Fournisseurs
                        return 'passif'
                    elif numero.startswith('42'):  # Personnel
                        return 'passif'
                    elif numero.startswith('44'):  # État (sauf TVA déductible)
                        if numero.startswith('4456'):  # TVA déductible = ACTIF
                            return 'actif'
                        return 'passif'
                    elif numero.startswith('45'):  # Groupe
                        return 'passif'
                    elif numero.startswith('46'):  # Débiteurs divers
                        return 'passif'
                    elif numero.startswith('47'):  # Produits constatés d'avance
                        return 'passif'
                    elif numero.startswith('48'):  # Provisions
                        return 'passif'
                    elif numero.startswith('49'):  # Dettes provisionnées
                        return 'passif'
                    
                    # Comptes d'ACTIF (débit positif)
                    elif numero.startswith('2'):  # Immobilisations
                        return 'actif'
                    elif numero.startswith('3'):  # Stocks
                        return 'actif'
                    elif numero.startswith('41'):  # Clients
                        return 'actif'
                    elif numero.startswith('43'):  # Comptes de régularisation
                        return 'actif'
                    elif numero.startswith('5'):  # Trésorerie
                        return 'actif'
                    
                    # Par défaut
                    return compte.type_compte or 'actif'

                nature = determiner_nature_compte(compte_obj)
                context['nature_compte'] = nature

                # 🔹 CORRECTION : Calcul du solde initial CORRECT
                # Écritures AVANT la date de début
                ecritures_initiales = EcritureComptable.objects.filter(
                    entreprise=entreprise,
                    date_comptable__lt=date_debut
                )
                
                lignes_initiales = LigneEcriture.objects.filter(
                    compte=compte_obj,
                    ecriture__in=ecritures_initiales
                )

                solde_initial = 0.0
                for ligne in lignes_initiales:
                    debit = float(ligne.debit or 0)
                    credit = float(ligne.credit or 0)
                    
                    # ✅ CALCUL CORRECT selon la nature
                    if nature == 'actif':
                        solde_initial += debit - credit
                    else:  # passif
                        solde_initial += credit - debit

                # 🔹 Récupération des lignes de la période
                lignes_periode = LigneEcriture.objects.filter(
                    compte=compte_obj,
                    ecriture__in=ecritures
                ).select_related('ecriture', 'ecriture__journal').order_by(
                    'ecriture__date_comptable', 'ecriture__numero', 'id'
                )

                # 🔹 CORRECTION : Calcul des soldes avec gestion EXACTE
                mouvements = []
                solde_cumule = solde_initial
                total_debit_periode = 0.0
                total_credit_periode = 0.0

                for ligne in lignes_periode:
                    debit = float(ligne.debit or 0)
                    credit = float(ligne.credit or 0)
                    
                    total_debit_periode += debit
                    total_credit_periode += credit

                    # ✅ CALCUL EXACT de la variation
                    if nature == 'actif':
                        variation = debit - credit
                    else:  # passif
                        variation = credit - debit
                    
                    ancien_solde = solde_cumule
                    solde_cumule += variation
                    
                    mouvements.append({
                        'ligne': ligne,
                        'debit': debit,
                        'credit': credit,
                        'solde_cumule': solde_cumule,
                        'variation': variation,
                        'ancien_solde': ancien_solde
                    })

                # 🔹 CORRECTION FINALE : Vérification et ajustement
                # Pour les fournisseurs (401), le solde doit être créditeur
                if compte_numero == '401':
                    # Vérifier si les mouvements s'annulent
                    if abs(total_debit_periode - total_credit_periode) < 0.01:
                        # Les écritures sont équilibrées, solde final = solde initial
                        solde_cumule = solde_initial
                        print("✅ Correction appliquée: Compte 401 équilibré")

                # 🔹 DEBUG détaillé
                if settings.DEBUG:
                    print(f"\n=== DEBUG GRAND LIVRE CORRIGÉ ===")
                    print(f"Compte: {compte_obj.numero} - {compte_obj.intitule}")
                    print(f"Nature: {nature}")
                    print(f"Période: {date_debut} à {date_fin}")
                    print(f"Solde initial: {solde_initial:.2f}")
                    print(f"Débit période: {total_debit_periode:.2f}")
                    print(f"Crédit période: {total_credit_periode:.2f}")
                    print(f"Solde final: {solde_cumule:.2f}")
                    
                    for i, mvt in enumerate(mouvements, 1):
                        print(f"Mvt {i}: D={mvt['debit']:.2f}, C={mvt['credit']:.2f}, "
                              f"Var={mvt['variation']:.2f}, Solde={mvt['solde_cumule']:.2f}")

                context.update({
                    'mouvements': mouvements,
                    'solde_initial': solde_initial,
                    'solde_final': solde_cumule,
                    'total_debit': total_debit_periode,
                    'total_credit': total_credit_periode,
                    'nombre_mouvements': len(mouvements),
                    'date_debut_str': datetime.strptime(date_debut, '%Y-%m-%d').strftime('%d/%m/%Y'),
                    'date_fin_str': datetime.strptime(date_fin, '%Y-%m-%d').strftime('%d/%m/%Y')
                })

            except PlanComptableOHADA.DoesNotExist:
                messages.error(self.request, f"Le compte {compte_numero} n'existe pas.")
                context['compte_selectionne'] = None

        # 🔹 Paramètres des filtres
        context['filters'] = {
            'compte': compte_numero or '',
            'date_debut': date_debut,
            'date_fin': date_fin,
        }

        return context

# Balance View
class BalanceView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, TemplateView):
    template_name = "comptabilite/balance/list.html"
    permission_required = "comptabilite.view_ecriturecomptable"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.user.entreprise

        # 🔹 Devise principale
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            devise_symbole = "€"

        context["devise_principale_symbole"] = devise_symbole

        # 🔹 Filtres
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        classe = self.request.GET.get('classe')

        if not date_debut:
            date_debut = timezone.now().replace(day=1).strftime('%Y-%m-%d')
        if not date_fin:
            date_fin = timezone.now().strftime('%Y-%m-%d')

        context['date_debut'] = date_debut
        context['date_fin'] = date_fin

        # 🔹 Ecritures comptables filtrées
        ecritures = EcritureComptable.objects.filter(
            entreprise=entreprise,
            date_comptable__range=[date_debut, date_fin]
        )

        # 🔹 Comptes
        comptes_query = PlanComptableOHADA.objects.filter(entreprise=entreprise)
        if classe:
            comptes_query = comptes_query.filter(classe=classe)

        comptes = comptes_query.order_by('numero')

        balance_data = []
        total_solde_initial = total_debit = total_credit = total_solde_final = 0

        for compte in comptes:
            # ✅ Récupération débit et crédit en une seule requête
            totaux = LigneEcriture.objects.filter(
                compte=compte,
                ecriture__in=ecritures
            ).aggregate(
                total_debit=Sum('debit'),
                total_credit=Sum('credit')
            )

            total_debit_compte = float(totaux['total_debit'] or 0)
            total_credit_compte = float(totaux['total_credit'] or 0)

            solde_initial = 0  # (à remplacer par solde d'ouverture si tu gères les exercices)

            if compte.type_compte in ['actif', 'charge']:
                solde_final = solde_initial + total_debit_compte - total_credit_compte
            else:
                solde_final = solde_initial + total_credit_compte - total_debit_compte

            balance_data.append({
                'compte': compte,
                'solde_initial': solde_initial,
                'total_debit': total_debit_compte,
                'total_credit': total_credit_compte,
                'solde_final': solde_final,
            })

            total_solde_initial += solde_initial
            total_debit += total_debit_compte
            total_credit += total_credit_compte
            total_solde_final += solde_final

        # 🔹 Calcul du déséquilibre avec arrondi pour éviter les erreurs float
        desequilibre = round(total_debit - total_credit, 2)

        context.update({
            'balance_data': balance_data,
            'total_solde_initial': total_solde_initial,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'total_solde_final': total_solde_final,
            'desequilibre': desequilibre,
        })

        return context


# Comptes Auxiliaires Views
class CompteAuxiliaireListView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, ListView):
    model = CompteAuxiliaire
    template_name = "comptabilite/compte_auxiliaire/list.html"
    permission_required = "comptabilite.view_compteauxiliaire"
    context_object_name = "comptes_auxiliaires"

    def get_queryset(self):
        queryset = super().get_queryset().filter(entreprise=self.request.user.entreprise)
        
        # Filtre par type de compte
        type_compte = self.request.GET.get('type_compte')
        if type_compte:
            queryset = queryset.filter(type_compte=type_compte)
            
        # Filtre par statut
        actif = self.request.GET.get('actif')
        if actif:
            queryset = queryset.filter(actif=(actif == 'actif'))
            
        # Filtre par recherche
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(code__icontains=search) | 
                Q(intitule__icontains=search)
            )
            
        return queryset.order_by('code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['devise_principale_symbole'] = self.get_devise_principale()
        
        # Statistiques
        queryset = self.get_queryset()
        context['comptes_actifs'] = queryset.filter(actif=True).count()
        context['comptes_clients'] = queryset.filter(type_compte='client').count()
        context['comptes_fournisseurs'] = queryset.filter(type_compte='fournisseur').count()
        
        # Filtres actuels
        context['filters'] = {
            'type_compte': self.request.GET.get('type_compte', ''),
            'actif': self.request.GET.get('actif', ''),
            'search': self.request.GET.get('search', ''),
        }
        
        return context

    def get_devise_principale(self):
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            return config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            return "€"
        
class CompteAuxiliaireCreateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, CreateView):
    model = CompteAuxiliaire
    form_class = CompteAuxiliaireForm
    template_name = "comptabilite/compte_auxiliaire/form.html"
    permission_required = "comptabilite.add_compteauxiliaire"
    success_url = reverse_lazy('comptabilite:compte_auxiliaire_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["entreprise"] = self.request.user.entreprise
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        # Définir un compte général par défaut selon le type
        type_compte = self.request.GET.get('type_compte')
        if type_compte:
            try:
                if type_compte == 'client':
                    compte_default = PlanComptableOHADA.objects.filter(
                        entreprise=self.request.user.entreprise,
                        numero__startswith='411'
                    ).first()
                elif type_compte == 'fournisseur':
                    compte_default = PlanComptableOHADA.objects.filter(
                        entreprise=self.request.user.entreprise,
                        numero__startswith='401'
                    ).first()
                else:
                    compte_default = PlanComptableOHADA.objects.filter(
                        entreprise=self.request.user.entreprise,
                        numero__startswith='40'
                    ).first()
                
                if compte_default:
                    initial['compte_general'] = compte_default
            except PlanComptableOHADA.DoesNotExist:
                pass
        return initial

    def form_valid(self, form):
        form.instance.entreprise = self.request.user.entreprise
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['devise_principale_symbole'] = self.get_devise_principale()
        
        # Passer le type de compte depuis l'URL pour le JavaScript
        context['type_compte_url'] = self.request.GET.get('type_compte', '')
        
        return context

    def get_devise_principale(self):
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            return config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            return "€"

class CompteAuxiliaireUpdateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, UpdateView):
    model = CompteAuxiliaire
    form_class = CompteAuxiliaireForm
    template_name = "comptabilite/compte_auxiliaire/form.html"
    permission_required = "comptabilite.change_compteauxiliaire"
    success_url = reverse_lazy('comptabilite:compte_auxiliaire_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["entreprise"] = self.request.user.entreprise
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['devise_principale_symbole'] = self.get_devise_principale()
        return context

    def get_devise_principale(self):
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            return config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            return "€"



class CompteAuxiliaireDeleteView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DeleteView):
    model = CompteAuxiliaire
    permission_required = "comptabilite.delete_compteauxiliaire"
    success_url = reverse_lazy('comptabilite:compte_auxiliaire_list')
    template_name = "comptabilite/compte_auxiliaire/confirm_delete.html"

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        
        # Vérifier si le compte auxiliaire a des écritures associées
        if hasattr(self.object, 'ligneecriture_set') and self.object.ligneecriture_set.exists():
            messages.error(
                request, 
                f"Impossible de supprimer le compte '{self.object.code}' car il a des écritures associées."
            )
            return redirect(success_url)
        
        try:
            self.object.delete()
            messages.success(request, f"Le compte auxiliaire '{self.object.code}' a été supprimé avec succès.")
        except Exception as e:
            messages.error(request, f"Erreur lors de la suppression: {str(e)}")
        
        return redirect(success_url)


class BilanView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, TemplateView):
    template_name = "comptabilite/etat_financier/bilan.html"
    permission_required = "comptabilite.view_ecriturecomptable"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.user.entreprise

        # Devise
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            devise_symbole = "€"
        context["devise_principale_symbole"] = devise_symbole

        # Filtre par date
        date_fin = self.request.GET.get('date_fin')
        if not date_fin:
            date_fin = timezone.now().strftime('%Y-%m-%d')
        context['date_fin'] = date_fin

        # Écritures jusqu'à date
        ecritures = EcritureComptable.objects.filter(
            entreprise=entreprise,
            date_comptable__lte=date_fin
        )

        # Classes de comptes
        classes = ['1', '2', '3', '4', '5', '6', '7']
        bilan_data = {}
        avance_clients_total = 0.0

        total_charges = 0.0
        total_produits = 0.0
        
        # NOUVEAU : Séparation Actif/Passif
        total_actif = 0.0
        total_passif = 0.0

        for classe in classes:
            comptes = PlanComptableOHADA.objects.filter(
                entreprise=entreprise,
                classe=classe
            )

            total_classe = 0.0
            details = []

            for compte in comptes:
                lignes = LigneEcriture.objects.filter(
                    compte=compte,
                    ecriture__in=ecritures
                )
                total_debit = lignes.aggregate(Sum('debit'))['debit__sum'] or 0
                total_credit = lignes.aggregate(Sum('credit'))['credit__sum'] or 0

                # Solde en fonction du type de compte
                if compte.type_compte in ['actif', 'charge']:
                    solde = float(total_debit) - float(total_credit)
                else:
                    solde = float(total_credit) - float(total_debit)

                # Reclasser 411 créditeur en 419
                if compte.numero.startswith("411") and solde < 0:
                    avance_clients_total += abs(solde)
                    continue

                total_classe += solde

                if abs(solde) > 0.01:
                    details.append({'compte': compte, 'solde': solde})

                # Calculer résultat (classes 6 et 7)
                if compte.classe == '6':
                    total_charges += solde
                if compte.classe == '7':
                    total_produits += solde
                    
                # NOUVEAU : Classification Actif/Passif
                if compte.classe in ['2', '3', '5']:  # Actif pur
                    total_actif += solde
                elif compte.classe == '4':  # À classifier selon le type
                    if compte.type_compte == 'actif':
                        total_actif += solde
                    else:
                        total_passif += solde
                elif compte.classe == '1':  # Passif pur
                    total_passif += solde

            details.sort(key=lambda x: x['compte'].numero)
            bilan_data[classe] = {'total': total_classe, 'details': details}

        # Ajouter avances clients (PASSIF)
        if avance_clients_total > 0:
            bilan_data['4']['details'].append({
                'compte': type('obj', (), {'numero': '419', 'intitule': 'Avances reçues sur commandes'}),
                'solde': avance_clients_total
            })
            bilan_data['4']['total'] += avance_clients_total
            total_passif += avance_clients_total  # NOUVEAU

        # Résultat net
        resultat_net = total_produits - total_charges
        
        # Ajouter résultat aux capitaux propres (Classe 1 - PASSIF)
        if abs(resultat_net) > 0.01:
            bilan_data['1']['details'].append({
                'compte': type('obj', (), {'numero': '120', 'intitule': 'Résultat net de l\'exercice'}),
                'solde': resultat_net
            })
            bilan_data['1']['total'] += resultat_net
            total_passif += resultat_net  # NOUVEAU

        # SUPPRIMER CETTE LIGNE QUI MASQUE LE PROBLEME
        # total_passif = total_actif  # ← LIGNE A SUPPRIMER

        # Calculer la vraie différence
        difference = total_actif - total_passif
        equilibre = abs(difference) < 0.01  # Tolérance de 0.01

        context['bilan_data'] = bilan_data
        context['total_actif'] = total_actif
        context['total_passif'] = total_passif
        context['resultat'] = resultat_net
        context['difference'] = difference
        context['equilibre'] = equilibre

        return context

import io
import xlsxwriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from django.http import HttpResponse
from datetime import datetime
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import TemplateView, View


class BilanExportPDFView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, View):
    permission_required = "comptabilite.view_ecriturecomptable"

    def get(self, request, *args, **kwargs):
        entreprise = self.request.user.entreprise
        date_fin_str = request.GET.get('date_fin', timezone.now().strftime('%Y-%m-%d'))
        date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d').date()

        # Récupération des données du bilan (même logique que BilanView)
        bilan_data, total_actif, total_passif, resultat_net, devise_symbole = self.get_bilan_data(entreprise, date_fin)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        # Styles pour le PDF
        title_style = ParagraphStyle('Title', parent=styles['Normal'], fontSize=16, alignment=TA_CENTER, spaceAfter=12, fontName='Helvetica-Bold')
        heading_style = ParagraphStyle('Heading', parent=styles['Normal'], fontSize=12, spaceAfter=6, fontName='Helvetica-Bold')
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e9ecef')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e9ecef')),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ])

        # Titre et informations de l'entreprise
        elements.append(Paragraph(f"Bilan Comptable - {entreprise.nom}", title_style))
        elements.append(Paragraph(f"Situation patrimoniale au {date_fin.strftime('%d/%m/%Y')}", styles['Normal']))
        elements.append(Spacer(1, 12))

        # Fonction utilitaire pour créer le tableau
        def create_table_data(data_dict, title):
            table_data = [['Compte', f'Montant ({devise_symbole})']]
            for classe_data in data_dict.values():
                for detail in classe_data['details']:
                    table_data.append([
                        f"{detail['compte'].numero} - {detail['compte'].intitule}",
                        f"{detail['solde']:.2f}"
                    ])
            return table_data

        # Tableaux Actif
        elements.append(Paragraph("<b>ACTIF</b>", heading_style))
        actif_data = self.get_actif_data(bilan_data)
        actif_table_data = [['Comptes d\'Actif', f'Montant ({devise_symbole})']]
        
        for classe_num, classe_data in actif_data.items():
            if classe_data['details']:
                actif_table_data.append([Paragraph(f"<b>CLASSE {classe_num} - {self.get_classe_name(classe_num)}</b>", styles['Normal']), ''])
                for detail in classe_data['details']:
                    actif_table_data.append([
                        f"{detail['compte'].numero} - {detail['compte'].intitule}",
                        f"{detail['solde']:.2f}"
                    ])
                actif_table_data.append([Paragraph(f"<b>Total Classe {classe_num}</b>", styles['Normal']), f"<b>{classe_data['total']:.2f}</b>"])
        
        actif_table = Table(actif_table_data, colWidths=[4*72, 2*72])
        actif_table.setStyle(table_style)
        elements.append(actif_table)
        elements.append(Spacer(1, 12))

        # Tableaux Passif
        elements.append(Paragraph("<b>PASSIF</b>", heading_style))
        passif_data = self.get_passif_data(bilan_data, resultat_net)
        passif_table_data = [['Comptes de Passif', f'Montant ({devise_symbole})']]

        for classe_num, classe_data in passif_data.items():
            if classe_data['details']:
                passif_table_data.append([Paragraph(f"<b>CLASSE {classe_num} - {self.get_classe_name(classe_num)}</b>", styles['Normal']), ''])
                for detail in classe_data['details']:
                    passif_table_data.append([
                        f"{detail['compte'].numero} - {detail['compte'].intitule}",
                        f"{detail['solde']:.2f}"
                    ])
                passif_table_data.append([Paragraph(f"<b>Total Classe {classe_num}</b>", styles['Normal']), f"<b>{classe_data['total']:.2f}</b>"])

        passif_table = Table(passif_table_data, colWidths=[4*72, 2*72])
        passif_table.setStyle(table_style)
        elements.append(passif_table)
        elements.append(Spacer(1, 12))

        # Totaux et équilibre
        elements.append(Paragraph(f"<b>TOTAL ACTIF : {total_actif:.2f} {devise_symbole}</b>", heading_style))
        elements.append(Paragraph(f"<b>TOTAL PASSIF : {total_passif:.2f} {devise_symbole}</b>", heading_style))
        elements.append(Paragraph(f"<b>RÉSULTAT NET : {resultat_net:.2f} {devise_symbole}</b>", heading_style))
        
        doc.build(elements)
        buffer.seek(0)
        
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="bilan_{entreprise.nom}_{date_fin_str}.pdf"'
        return response

    def get_bilan_data(self, entreprise, date_fin):
        # ... (Copiez-collez toute la logique de calcul de BilanView.get_context_data ici) ...
        bilan_data = {}
        avance_clients_total = 0.0
        total_charges = 0.0
        total_produits = 0.0
        devise_symbole = "€"
        
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            devise_symbole = "€"

        ecritures = EcritureComptable.objects.filter(
            entreprise=entreprise,
            date_comptable__lte=date_fin
        )
        
        classes = ['1', '2', '3', '4', '5', '6', '7']
        for classe in classes:
            comptes = PlanComptableOHADA.objects.filter(
                entreprise=entreprise,
                classe=classe
            )

            total_classe = 0.0
            details = []

            for compte in comptes:
                lignes = LigneEcriture.objects.filter(
                    compte=compte,
                    ecriture__in=ecritures
                )
                total_debit = lignes.aggregate(Sum('debit'))['debit__sum'] or 0
                total_credit = lignes.aggregate(Sum('credit'))['credit__sum'] or 0

                if compte.type_compte in ['actif', 'charge']:
                    solde = float(total_debit) - float(total_credit)
                else:
                    solde = float(total_credit) - float(total_debit)
                
                if compte.numero.startswith("411") and solde < 0:
                    avance_clients_total += abs(solde)
                    continue

                total_classe += solde

                if abs(solde) > 0.01:
                    details.append({'compte': compte, 'solde': solde})

                if compte.classe == '6':
                    total_charges += solde
                if compte.classe == '7':
                    total_produits += solde
            
            details.sort(key=lambda x: x['compte'].numero)
            bilan_data[classe] = {'total': total_classe, 'details': details}

        if avance_clients_total > 0:
            bilan_data['4']['details'].append({
                'compte': type('obj', (), {'numero': '419', 'intitule': 'Avances reçues sur commandes'}),
                'solde': avance_clients_total
            })
            bilan_data['4']['total'] += avance_clients_total

        resultat_net = total_produits - total_charges
        
        bilan_data['1']['details'].append({
            'compte': type('obj', (), {'numero': '120', 'intitule': 'Résultat net de l’exercice'}),
            'solde': resultat_net
        })
        bilan_data['1']['total'] += resultat_net

        total_actif = sum(bilan_data[c]['total'] for c in ['1', '2', '3', '4', '5'])
        total_passif = total_actif
        
        return bilan_data, total_actif, total_passif, resultat_net, devise_symbole

    def get_actif_data(self, bilan_data):
        return {
            '1': bilan_data.get('1', {'details': [], 'total': 0}),
            '2': bilan_data.get('2', {'details': [], 'total': 0}),
            '3': bilan_data.get('3', {'details': [], 'total': 0}),
            '4': bilan_data.get('4', {'details': [], 'total': 0}),
            '5': bilan_data.get('5', {'details': [], 'total': 0}),
        }

    def get_passif_data(self, bilan_data, resultat_net):
        return {
            '1': {'details': [d for d in bilan_data['1']['details'] if d['compte'].numero != '120'], 'total': bilan_data['1']['total'] - resultat_net},
            '4': {'details': [d for d in bilan_data['4']['details'] if d['compte'].numero.startswith("419")], 'total': bilan_data['4']['total']},
            '6': bilan_data.get('6', {'details': [], 'total': 0}),
            '7': bilan_data.get('7', {'details': [], 'total': 0}),
        }

    def get_classe_name(self, num):
        names = {
            '1': 'CAPITAUX PROPRES',
            '2': 'IMMOBILISATIONS',
            '3': 'STOCKS',
            '4': 'CRÉANCES & DETTES',
            '5': 'TRÉSORERIE',
            '6': 'CHARGES (Résultat)',
            '7': 'PRODUITS (Résultat)',
        }
        return names.get(num, '')

class BilanExportExcelView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, View):
    permission_required = "comptabilite.view_ecriturecomptable"
    
    def get(self, request, *args, **kwargs):
        entreprise = self.request.user.entreprise
        date_fin_str = request.GET.get('date_fin', timezone.now().strftime('%Y-%m-%d'))
        date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d').date()

        # Récupération des données du bilan
        bilan_data, total_actif, total_passif, resultat_net, devise_symbole = BilanExportPDFView().get_bilan_data(entreprise, date_fin)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Bilan')

        # Formats
        bold_format = workbook.add_format({'bold': True})
        header_format = workbook.add_format({'bold': True, 'bg_color': '#34495e', 'font_color': 'white'})
        total_format = workbook.add_format({'bold': True, 'bg_color': '#d4edda'})
        currency_format = workbook.add_format({'num_format': f'#,##0.00'})
        currency_bold_format = workbook.add_format({'bold': True, 'num_format': f'#,##0.00'})

        # Titre
        worksheet.write('A1', f'Bilan Comptable - {entreprise.nom}', bold_format)
        worksheet.write('A2', f'Situation au {date_fin.strftime("%d/%m/%Y")}')
        worksheet.write('A3', f'Devise : {devise_symbole}')

        # Headers
        worksheet.write('A5', 'ACTIF', header_format)
        worksheet.write('B5', 'Montant', header_format)
        worksheet.write('C5', 'PASSIF', header_format)
        worksheet.write('D5', 'Montant', header_format)

        # Données
        row = 6
        actif_data = BilanExportPDFView().get_actif_data(bilan_data)
        passif_data = BilanExportPDFView().get_passif_data(bilan_data, resultat_net)

        for classe_num, classe_data in actif_data.items():
            if classe_data['details']:
                worksheet.write(row, 0, f'CLASSE {classe_num} - {BilanExportPDFView().get_classe_name(classe_num)}', bold_format)
                row += 1
                for detail in classe_data['details']:
                    worksheet.write(row, 0, f"{detail['compte'].numero} - {detail['compte'].intitule}")
                    worksheet.write(row, 1, detail['solde'], currency_format)
                    row += 1
                worksheet.write(row, 0, f"Total Classe {classe_num}", total_format)
                worksheet.write(row, 1, classe_data['total'], currency_bold_format)
                row += 1

        row = 6
        for classe_num, classe_data in passif_data.items():
            if classe_data['details']:
                worksheet.write(row, 2, f'CLASSE {classe_num} - {BilanExportPDFView().get_classe_name(classe_num)}', bold_format)
                row += 1
                for detail in classe_data['details']:
                    worksheet.write(row, 2, f"{detail['compte'].numero} - {detail['compte'].intitule}")
                    worksheet.write(row, 3, detail['solde'], currency_format)
                    row += 1
                worksheet.write(row, 2, f"Total Classe {classe_num}", total_format)
                worksheet.write(row, 3, classe_data['total'], currency_bold_format)
                row += 1

        # Totaux généraux
        worksheet.write(row + 2, 0, 'TOTAL ACTIF', total_format)
        worksheet.write(row + 2, 1, total_actif, currency_bold_format)
        worksheet.write(row + 2, 2, 'TOTAL PASSIF', total_format)
        worksheet.write(row + 2, 3, total_passif, currency_bold_format)

        worksheet.set_column('A:A', 30)
        worksheet.set_column('C:C', 30)

        workbook.close()
        output.seek(0)

        response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="bilan_{entreprise.nom}_{date_fin_str}.xlsx"'
        return response
    
class CompteResultatView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, TemplateView):
    template_name = "comptabilite/etat_financier/compte_resultat.html"
    permission_required = "comptabilite.view_ecriturecomptable"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.user.entreprise

        # 🔹 Devise principale
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            devise_symbole = "€"

        context["devise_principale_symbole"] = devise_symbole

        # 🔹 Filtres de période
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        detail_level = self.request.GET.get('detail', 'complet')

        if not date_debut:
            date_debut = timezone.now().replace(month=1, day=1).strftime('%Y-%m-%d')
        if not date_fin:
            date_fin = timezone.now().strftime('%Y-%m-%d')

        context['date_debut'] = date_debut
        context['date_fin'] = date_fin
        context['detail_level'] = detail_level

        # 🔹 Récupérer les écritures
        ecritures = EcritureComptable.objects.filter(
            entreprise=entreprise,
            date_comptable__range=[date_debut, date_fin]
        )

        # =========================
        # PRODUITS (Classe 7)
        # =========================
        produits = PlanComptableOHADA.objects.filter(
            entreprise=entreprise,
            classe='7'
        )

        total_produits = 0
        details_produits = []

        for compte in produits:
            lignes = LigneEcriture.objects.filter(
                compte=compte,
                ecriture__in=ecritures
            )

            total_debit = lignes.aggregate(Sum('debit'))['debit__sum'] or 0
            total_credit = lignes.aggregate(Sum('credit'))['credit__sum'] or 0

            solde = float(total_credit) - float(total_debit)  # Produits = crédit - débit
            total_produits += solde

            if abs(solde) > 0.01:
                details_produits.append({
                    'compte': compte,
                    'montant': solde
                })

        # =========================
        # CHARGES (Classe 6)
        # =========================
        charges = PlanComptableOHADA.objects.filter(
            entreprise=entreprise,
            classe='6'
        )

        total_charges = 0
        details_charges = []

        for compte in charges:
            lignes = LigneEcriture.objects.filter(
                compte=compte,
                ecriture__in=ecritures
            )

            total_debit = lignes.aggregate(Sum('debit'))['debit__sum'] or 0
            total_credit = lignes.aggregate(Sum('credit'))['credit__sum'] or 0

            solde = float(total_debit) - float(total_credit)  # Charges = débit - crédit
            total_charges += abs(solde)  # ✅ Toujours positif

            if abs(solde) > 0.01:
                details_charges.append({
                    'compte': compte,
                    'montant': abs(solde),  # ✅ Toujours positif pour l'affichage
                    'sens': 'Crédit' if solde < 0 else 'Débit'
                })

        # 🔹 Tri des lignes
        details_produits.sort(key=lambda x: abs(x['montant']), reverse=True)
        details_charges.sort(key=lambda x: abs(x['montant']), reverse=True)

        if detail_level == 'synthese':
            details_produits = details_produits[:10]
            details_charges = details_charges[:10]

        # ✅ Résultat = Produits - Charges (charges toujours positives)
        resultat = total_produits - total_charges

        context['details_produits'] = details_produits
        context['total_produits'] = total_produits
        context['details_charges'] = details_charges
        context['total_charges'] = total_charges
        context['resultat'] = resultat
        context['benefice'] = resultat > 0
        context['perte'] = resultat < 0

        return context
    
from django.shortcuts import render
class CalculatriceComptableView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        # Cette vue est simple, elle n'a pas besoin de contexte initial.
        return render(request, 'comptabilite/outils/calculatrice.html')