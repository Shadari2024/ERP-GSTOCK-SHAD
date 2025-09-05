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
# Plan Comptable Views
class PlanComptableListView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, ListView):
    model = PlanComptableOHADA
    template_name = "comptabilite/plan_comptable/list.html"
    permission_required = "comptabilite.view_plancomptableohada"
    context_object_name = "comptes"

    def get_queryset(self):
        return super().get_queryset().filter(entreprise=self.request.user.entreprise)

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
        context['devise_principale_symbole'] = self.get_devise_principale()
        return context

    def get_devise_principale(self):
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
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
        context['devise_principale_symbole'] = self.get_devise_principale()
        context['journaux'] = JournalComptable.objects.filter(entreprise=self.request.user.entreprise, actif=True)
        
        # Passer les paramètres de filtrage pour les garder dans la pagination
        context['filters'] = {
            'journal': self.request.GET.get('journal', ''),
            'date_debut': self.request.GET.get('date_debut', ''),
            'date_fin': self.request.GET.get('date_fin', ''),
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
        
        
        
        
        

# Grand Livre View
class GrandLivreView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, TemplateView):
    template_name = "comptabilite/grand_livre/list.html"
    permission_required = "comptabilite.view_ecriturecomptable"

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
        
        # Filtres
        compte = self.request.GET.get('compte')
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        
        # Récupérer les écritures filtrées
        ecritures = EcritureComptable.objects.filter(entreprise=entreprise)
        
        if date_debut:
            ecritures = ecritures.filter(date_ecriture__gte=date_debut)
        if date_fin:
            ecritures = ecritures.filter(date_ecriture__lte=date_fin)
        
        # Si un compte est spécifié, filtrer les lignes de ce compte
        if compte:
            try:
                compte_obj = PlanComptableOHADA.objects.get(numero=compte, entreprise=entreprise)
                context['compte_selectionne'] = compte_obj
                
                # Récupérer toutes les lignes d'écriture pour ce compte
                lignes = LigneEcriture.objects.filter(
                    compte=compte_obj,
                    ecriture__in=ecritures
                ).select_related('ecriture', 'ecriture__journal').order_by('ecriture__date_ecriture', 'ecriture__numero')
                
                # Calculer le solde
                solde = 0
                total_debit = 0
                total_credit = 0
                
                for ligne in lignes:
                    solde += ligne.debit - ligne.credit
                    total_debit += ligne.debit
                    total_credit += ligne.credit
                    ligne.solde_cumule = solde
                
                context['lignes'] = lignes
                context['solde_final'] = solde
                context['total_debit'] = total_debit
                context['total_credit'] = total_credit
                
            except PlanComptableOHADA.DoesNotExist:
                messages.error(self.request, f"Le compte {compte} n'existe pas.")
        
        # Liste des comptes pour le filtre
        context['comptes'] = PlanComptableOHADA.objects.filter(entreprise=entreprise).order_by('numero')
        
        # Passer les paramètres de filtrage
        context['filters'] = {
            'compte': compte if compte else '',
            'date_debut': date_debut if date_debut else '',
            'date_fin': date_fin if date_fin else '',
        }
        
        return context

# Balance View
class BalanceView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, TemplateView):
    template_name = "comptabilite/balance/list.html"
    permission_required = "comptabilite.view_ecriturecomptable"

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
        
        # Filtres
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        classe = self.request.GET.get('classe')
        
        # Définir les dates par défaut (mois en cours)
        if not date_debut:
            date_debut = timezone.now().replace(day=1).strftime('%Y-%m-%d')
        if not date_fin:
            date_fin = timezone.now().strftime('%Y-%m-%d')
        
        context['date_debut'] = date_debut
        context['date_fin'] = date_fin
        
        # Récupérer les écritures dans la période
        ecritures = EcritureComptable.objects.filter(
            entreprise=entreprise,
            date_ecriture__range=[date_debut, date_fin]
        )
        
        # Récupérer tous les comptes (filtrer par classe si spécifié)
        comptes_query = PlanComptableOHADA.objects.filter(entreprise=entreprise)
        if classe:
            comptes_query = comptes_query.filter(classe=classe)
        
        comptes = comptes_query.order_by('numero')
        
        # Calculer les totaux pour chaque compte
        balance_data = []
        total_solde_initial = 0
        total_debit = 0
        total_credit = 0
        total_solde_final = 0
        
        for compte in comptes:
            lignes = LigneEcriture.objects.filter(
                compte=compte,
                ecriture__in=ecritures
            )
            
            total_debit_compte = lignes.aggregate(Sum('debit'))['debit__sum'] or 0
            total_credit_compte = lignes.aggregate(Sum('credit'))['credit__sum'] or 0
            
            # Solde initial (à implémenter avec la gestion d'ouverture/exercice)
            solde_initial = 0
            
            # Solde final selon le type de compte
            if compte.type_compte in ['actif', 'charge']:
                solde_final = solde_initial + total_debit_compte - total_credit_compte
            else:  # passif, produit
                solde_final = solde_initial + total_credit_compte - total_debit_compte
            
            balance_data.append({
                'compte': compte,
                'solde_initial': solde_initial,
                'total_debit': total_debit_compte,
                'total_credit': total_credit_compte,
                'solde_final': solde_final,
            })
            
            # Totaux généraux
            total_solde_initial += solde_initial
            total_debit += total_debit_compte
            total_credit += total_credit_compte
            total_solde_final += solde_final
        
        context['balance_data'] = balance_data
        context['total_solde_initial'] = total_solde_initial
        context['total_debit'] = total_debit
        context['total_credit'] = total_credit
        context['total_solde_final'] = total_solde_final
        context['desequilibre'] = abs(total_debit - total_credit)
        
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





# États Financiers Views
class BilanView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, TemplateView):
    template_name = "comptabilite/etat_financier/bilan.html"
    permission_required = "comptabilite.view_ecriturecomptable"

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
        
        # Filtre par date
        date_fin = self.request.GET.get('date_fin')
        if not date_fin:
            date_fin = timezone.now().strftime('%Y-%m-%d')
        
        context['date_fin'] = date_fin
        
        # Récupérer les écritures jusqu'à la date spécifiée
        ecritures = EcritureComptable.objects.filter(
            entreprise=entreprise,
            date_ecriture__lte=date_fin
        )
        
        # Calculer les totaux par classe de comptes
        classes = ['1', '2', '3', '4', '5', '6', '7']
        bilan_data = {}
        
        for classe in classes:
            comptes = PlanComptableOHADA.objects.filter(
                entreprise=entreprise,
                classe=classe
            )
            
            total_classe = 0
            details = []
            
            for compte in comptes:
                lignes = LigneEcriture.objects.filter(
                    compte=compte,
                    ecriture__in=ecritures
                )
                
                total_debit = lignes.aggregate(Sum('debit'))['debit__sum'] or 0
                total_credit = lignes.aggregate(Sum('credit'))['credit__sum'] or 0
                
                # Déterminer le solde selon le type de compte
                if compte.type_compte in ['actif', 'charge']:
                    solde = total_debit - total_credit
                else:  # passif, produit
                    solde = total_credit - total_debit
                
                total_classe += solde
                
                if abs(solde) > 0.01:  # Seulement les comptes avec solde significatif
                    details.append({
                        'compte': compte,
                        'solde': solde
                    })
            
            # Trier par numéro de compte
            details.sort(key=lambda x: x['compte'].numero)
            
            bilan_data[classe] = {
                'total': total_classe,
                'details': details
            }
        
        context['bilan_data'] = bilan_data
        
        # Total Actif (classes 1 à 5)
        total_actif = sum(bilan_data[classe]['total'] for classe in ['1', '2', '3', '4', '5'])
        
        # Total Passif (classes 6 et 7)
        total_passif = sum(bilan_data[classe]['total'] for classe in ['6', '7'])
        
        # Ajuster pour l'équilibre
        difference = total_actif - total_passif
        resultat = difference
        
        context['total_actif'] = total_actif
        context['total_passif'] = total_passif + resultat  # Ajuster le passif avec le résultat
        context['resultat'] = resultat
        context['difference'] = abs(difference)
        context['equilibre'] = abs(difference) < 0.01  # Tolérance de 0.01 pour les arrondis
        
        return context

class CompteResultatView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, TemplateView):
    template_name = "comptabilite/etat_financier/compte_resultat.html"
    permission_required = "comptabilite.view_ecriturecomptable"

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
        
        # Filtres
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        detail_level = self.request.GET.get('detail', 'complet')
        
        # Définir les dates par défaut (année en cours)
        if not date_debut:
            date_debut = timezone.now().replace(month=1, day=1).strftime('%Y-%m-%d')
        if not date_fin:
            date_fin = timezone.now().strftime('%Y-%m-%d')
        
        context['date_debut'] = date_debut
        context['date_fin'] = date_fin
        context['detail_level'] = detail_level
        
        # Récupérer les écritures dans la période
        ecritures = EcritureComptable.objects.filter(
            entreprise=entreprise,
            date_ecriture__range=[date_debut, date_fin]
        )
        
        # Calculer les produits (classe 7)
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
            
            # Pour les comptes de produits, le solde est crédit - débit
            solde = total_credit - total_debit
            total_produits += solde
            
            if abs(solde) > 0.01:  # Seulement les comptes avec montant significatif
                details_produits.append({
                    'compte': compte,
                    'montant': solde
                })
        
        # Calculer les charges (classe 6)
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
            
            # Pour les comptes de charges, le solde est débit - crédit
            solde = total_debit - total_credit
            total_charges += solde
            
            if abs(solde) > 0.01:  # Seulement les comptes avec montant significatif
                details_charges.append({
                    'compte': compte,
                    'montant': solde
                })
        
        # Trier par montant décroissant
        details_produits.sort(key=lambda x: abs(x['montant']), reverse=True)
        details_charges.sort(key=lambda x: abs(x['montant']), reverse=True)
        
        # Réduire le détail si demandé
        if detail_level == 'synthese':
            details_produits = details_produits[:10]  # Top 10 produits
            details_charges = details_charges[:10]    # Top 10 charges
        
        # Résultat (bénéfice ou perte)
        resultat = total_produits - total_charges
        
        context['details_produits'] = details_produits
        context['total_produits'] = total_produits
        context['details_charges'] = details_charges
        context['total_charges'] = total_charges
        context['resultat'] = resultat
        context['benefice'] = resultat > 0
        context['perte'] = resultat < 0
        
        return context