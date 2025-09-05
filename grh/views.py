from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q, Sum
from parametres.mixins import EntrepriseAccessMixin
from parametres.models import ConfigurationSAAS
from .models import Departement, Poste, Employe, Contrat, BulletinPaie, Conge, Presence, LigneBulletinPaie
from .forms import DepartementForm, PosteForm, EmployeForm, ContratForm, BulletinPaieForm, CongeForm,LigneBulletinPaieForm
from django.views.generic import TemplateView
from django.views import View
from django.views.generic.edit import FormView

class GRHAccueilView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin,  TemplateView):
    template_name = "grh/accueil.html"
    permission_required = "grh.view_employe"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.user.entreprise
        
        # Statistiques pour le tableau de bord
        context['total_employes'] = Employe.objects.filter(entreprise=entreprise).count()
        context['employes_actifs'] = Employe.objects.filter(entreprise=entreprise, statut='ACTIF').count()
        context['total_departements'] = Departement.objects.filter(entreprise=entreprise, actif=True).count()
        context['conges_en_cours'] = Conge.objects.filter(entreprise=entreprise, statut='DEMANDE').count()
        
        return context
# Mixin de base pour le module GRH
class GRHBaseMixin:
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
        return context

# Vues pour les départements
class DepartementListView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, ListView):
    model = Departement
    template_name = "grh/departement/list.html"
    permission_required = "grh.view_departement"
    context_object_name = "departements"
    
    def get_queryset(self):
        return Departement.objects.filter(entreprise=self.request.user.entreprise)
    
    
class DepartementCreateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, CreateView):
    model = Departement
    form_class = DepartementForm
    template_name = "grh/departement/form.html"
    permission_required = "grh.add_departement"
    success_url = reverse_lazy('grh:departement_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["entreprise"] = self.request.user.entreprise
        return kwargs
    
    def form_valid(self, form):
        form.instance.entreprise = self.request.user.entreprise
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ajouter le nombre d'employés disponibles pour information
        context['employes_count'] = Employe.objects.filter(
            entreprise=self.request.user.entreprise, 
            statut='ACTIF'
        ).count()
        return context

class DepartementUpdateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, UpdateView):
    model = Departement
    form_class = DepartementForm
    template_name = "grh/departement/form.html"
    permission_required = "grh.change_departement"
    success_url = reverse_lazy('grh:departement_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["entreprise"] = self.request.user.entreprise
        return kwargs

class DepartementDeleteView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, DeleteView):
    model = Departement
    template_name = "grh/departement/confirm_delete.html"
    permission_required = "grh.delete_departement"
    success_url = reverse_lazy('grh:departement_list')

# Vues pour les postes
class PosteListView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, ListView):
    model = Poste
    template_name = "grh/poste/list.html"
    permission_required = "grh.view_poste"
    context_object_name = "postes"
    
    def get_queryset(self):
        queryset = Poste.objects.filter(entreprise=self.request.user.entreprise)
        
        # Filtrage par recherche
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(code__icontains=search_query) |
                Q(intitule__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Filtrage par département
        departement_id = self.request.GET.get('departement')
        if departement_id:
            queryset = queryset.filter(departement_id=departement_id)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['departements'] = Departement.objects.filter(entreprise=self.request.user.entreprise, actif=True)
        return context

class PosteCreateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, CreateView):
    model = Poste
    form_class = PosteForm
    template_name = "grh/poste/form.html"
    permission_required = "grh.add_poste"
    success_url = reverse_lazy('grh:poste_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["entreprise"] = self.request.user.entreprise
        return kwargs
    
    def form_valid(self, form):
        form.instance.entreprise = self.request.user.entreprise
        return super().form_valid(form)

class PosteUpdateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, UpdateView):
    model = Poste
    form_class = PosteForm
    template_name = "grh/poste/form.html"
    permission_required = "grh.change_poste"
    success_url = reverse_lazy('grh:poste_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["entreprise"] = self.request.user.entreprise
        return kwargs

class PosteDeleteView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, DeleteView):
    model = Poste
    template_name = "grh/poste/confirm_delete.html"
    permission_required = "grh.delete_poste"
    success_url = reverse_lazy('grh:poste_list')

# Vues pour les employés
class EmployeListView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, ListView):
    model = Employe
    template_name = "grh/employe/list.html"
    permission_required = "grh.view_employe"
    context_object_name = "employes"
    
    def get_queryset(self):
        return Employe.objects.filter(entreprise=self.request.user.entreprise)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['statuts'] = Employe.STATUT_CHOICES
        return context

class EmployeCreateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, CreateView):
    model = Employe
    form_class = EmployeForm
    template_name = "grh/employe/form.html"
    permission_required = "grh.add_employe"
    success_url = reverse_lazy('grh:employe_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["entreprise"] = self.request.user.entreprise
        return kwargs
    
    def form_valid(self, form):
        form.instance.entreprise = self.request.user.entreprise
        return super().form_valid(form)

class EmployeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, UpdateView):
    model = Employe
    form_class = EmployeForm
    template_name = "grh/employe/form.html"
    permission_required = "grh.change_employe"
    success_url = reverse_lazy('grh:employe_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["entreprise"] = self.request.user.entreprise
        return kwargs
    
class EmployeDetailView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, DetailView):
    model = Employe
    template_name = "grh/employe/detail.html"
    permission_required = "grh.view_employe"
    context_object_name = "employe"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ajouter le contrat actuel
        context['contrat_actuel'] = self.object.contrat_set.filter(statut='EN_COURS').first()
        return context

class EmployeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, DeleteView):
    model = Employe
    template_name = "grh/employe/confirm_delete.html"
    permission_required = "grh.delete_employe"
    success_url = reverse_lazy('grh:employe_list')


from django.http import HttpResponse
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
import os
from decimal import Decimal

class GenererCarteEmployeView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, View):
    permission_required = "grh.change_employe"
    
    def get(self, request, pk):
        employe = get_object_or_404(Employe, pk=pk, entreprise=request.user.entreprise)
        
        if employe.generer_carte_employe():
            employe.save()
            messages.success(request, "Carte d'employé générée avec succès!")
        else:
            messages.error(request, "Erreur lors de la génération de la carte")
        
        return redirect('grh:employe_detail', pk=employe.pk)

class TelechargerCarteEmployeView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, View):
    permission_required = "grh.view_employe"
    
    def get(self, request, pk):
        employe = get_object_or_404(Employe, pk=pk, entreprise=request.user.entreprise)
        
        if employe.carte_employe:
            file_path = employe.carte_employe.path
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='image/png')
                    response['Content-Disposition'] = f'attachment; filename="carte_employe_{employe.matricule}.png"'
                    return response
        
        messages.error(request, "Carte d'employé non disponible")
        return redirect('grh:employe_detail', pk=employe.pk)

class ApercuCarteEmployeView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, View):
    permission_required = "grh.view_employe"
    
    def get(self, request, pk):
        employe = get_object_or_404(Employe, pk=pk, entreprise=request.user.entreprise)
        
        if employe.carte_employe:
            return redirect(employe.carte_employe.url)
        
        messages.error(request, "Carte d'employé non disponible")
        return redirect('grh:employe_detail', pk=employe.pk)



# Vues pour les contrats
class ContratListView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, ListView):
    model = Contrat
    template_name = "grh/contrat/list.html"
    permission_required = "grh.view_contrat"
    context_object_name = "contrats"
    
    def get_queryset(self):
        return Contrat.objects.filter(entreprise=self.request.user.entreprise)
class CongeCreateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, CreateView):
    model = Conge
    form_class = CongeForm
    template_name = "grh/conge/form.html"
    permission_required = "grh.add_conge"
    success_url = reverse_lazy('grh:conge_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["entreprise"] = self.request.user.entreprise
        return kwargs
    
    def form_valid(self, form):
        form.instance.entreprise = self.request.user.entreprise
        # Si c'est une nouvelle demande, forcer le statut à DEMANDE
        if not form.instance.pk:
            form.instance.statut = 'DEMANDE'
            form.instance.date_demande = timezone.now()
        
        messages.success(self.request, "Demande de congé créée avec succès !")
        return super().form_valid(form)
class CongeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, UpdateView):
    model = Conge
    form_class = CongeForm
    template_name = "grh/conge/form.html"
    permission_required = "grh.change_conge"
    success_url = reverse_lazy('grh:conge_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["entreprise"] = self.request.user.entreprise
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, "Demande de congé modifiée avec succès !")
        return super().form_valid(form)

class ContratDetailView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, DetailView):
    model = Contrat
    template_name = "grh/contrat/detail.html"
    permission_required = "grh.view_contrat"
    context_object_name = "contrat"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ajouter la date actuelle pour les comparaisons
        from django.utils import timezone
        context['now'] = timezone.now()
        return context

# Vues pour les bulletins de paie
class BulletinPaieListView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, ListView):
    model = BulletinPaie
    template_name = "grh/paie/list.html"
    permission_required = "grh.view_bulletinpaie"
    context_object_name = "bulletins"
    
    def get_queryset(self):
        queryset = BulletinPaie.objects.filter(entreprise=self.request.user.entreprise)
        
        # Filtrage par période
        periode = self.request.GET.get('periode')
        if periode:
            queryset = queryset.filter(periode=periode)
        
        # Filtrage par employé
        employe_id = self.request.GET.get('employe')
        if employe_id:
            queryset = queryset.filter(employe_id=employe_id)
        
        return queryset.order_by('-periode', '-date_edition')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employes'] = Employe.objects.filter(entreprise=self.request.user.entreprise, statut='ACTIF')
        
        # Calcul des statistiques
        bulletins = context['bulletins']
        context['total_brut'] = bulletins.aggregate(Sum('salaire_brut'))['salaire_brut__sum'] or 0
        context['total_cotisations'] = bulletins.aggregate(Sum('total_cotisations'))['total_cotisations__sum'] or 0
        context['total_net'] = bulletins.aggregate(Sum('net_a_payer'))['net_a_payer__sum'] or 0
        
        return context
    
from .services import CalculPaieService
from datetime import datetime, timedelta
from .forms import BulletinPaieForm, LigneBulletinPaieForm, LigneBulletinPaieFormSet

class BulletinPaieCreateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, CreateView):
    model = BulletinPaie
    form_class = BulletinPaieForm
    template_name = "grh/paie/form.html"
    permission_required = "grh.add_bulletinpaie"
    success_url = reverse_lazy('grh:bulletin_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["entreprise"] = self.request.user.entreprise
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Initialiser le formset vide pour le contexte
        if self.request.POST:
            context['formset'] = LigneBulletinPaieFormSet(self.request.POST)
        else:
            context['formset'] = LigneBulletinPaieFormSet(queryset=LigneBulletinPaie.objects.none())
        return context
    
    def get_initial(self):
        initial = super().get_initial()
        employe_id = self.request.GET.get('employe')
        periode = self.request.GET.get('periode', datetime.now().strftime('%Y-%m'))
        
        if employe_id:
            try:
                employe = Employe.objects.get(id=employe_id, entreprise=self.request.user.entreprise)
                # Calcul automatique du salaire
                salaire_brut, jours_travailles, heures_supp, contrat = CalculPaieService.calculer_salaire_brut(employe, periode)
                
                initial.update({
                    'employe': employe,
                    'contrat': contrat,
                    'periode': periode,
                    'salaire_brut': salaire_brut,
                    'jours_travailles': jours_travailles,
                    'heures_travaillees': heures_supp + (jours_travailles * 8),
                    'total_cotisations': CalculPaieService.calculer_cotisations(salaire_brut),
                    'salaire_net': salaire_brut - CalculPaieService.calculer_cotisations(salaire_brut),
                    'net_a_payer': salaire_brut - CalculPaieService.calculer_cotisations(salaire_brut),
                })
            except (Employe.DoesNotExist, TypeError):
                pass
        
        return initial
    
    def form_valid(self, form):
        form.instance.entreprise = self.request.user.entreprise
        self.object = form.save()
        
        # Gérer le formset des lignes de bulletin
        formset = LigneBulletinPaieFormSet(self.request.POST, instance=self.object)
        if formset.is_valid():
            formset.save()
        
        # Générer l'écriture comptable
        self.generer_ecriture_comptable(self.object)
        
        return super().form_valid(form)
    
    def generer_ecriture_comptable(self, bulletin):
        """Génère l'écriture comptable automatique"""
        try:
            from comptabilite.models import EcritureComptable, LigneEcriture, PlanComptableOHADA, JournalComptable
            
            # Récupérer le journal "Paie"
            journal, created = JournalComptable.objects.get_or_create(
                code='PAIE',
                entreprise=self.request.user.entreprise,
                defaults={
                    'intitule': 'Journal de Paie',
                    'type_journal': 'divers'
                }
            )
            
            # Créer l'écriture comptable
            ecriture = EcritureComptable.objects.create(
                journal=journal,
                numero=f"PAIE-{bulletin.periode}-{bulletin.employe.matricule}",
                date_ecriture=datetime.now().date(),
                date_comptable=datetime.now().date(),
                libelle=f"Paie {bulletin.employe.nom_complet} - {bulletin.periode}",
                montant_devise=bulletin.salaire_brut,
                entreprise=self.request.user.entreprise,
                created_by=self.request.user
            )
            
            # Comptes selon plan OHADA (à adapter à votre plan comptable)
            compte_salaire = PlanComptableOHADA.objects.get(numero='6411', entreprise=self.request.user.entreprise)
            compte_cnss = PlanComptableOHADA.objects.get(numero='4311', entreprise=self.request.user.entreprise)
            compte_impot = PlanComptableOHADA.objects.get(numero='4451', entreprise=self.request.user.entreprise)
            compte_banque = PlanComptableOHADA.objects.get(numero='5121', entreprise=self.request.user.entreprise)
            
            # Ligne de débit (charges de personnel)
            LigneEcriture.objects.create(
                ecriture=ecriture,
                compte=compte_salaire,
                libelle=f"Salaire {bulletin.employe.nom_complet}",
                debit=bulletin.salaire_brut,
                credit=0,
                entreprise=self.request.user.entreprise
            )
            
            # Ligne de crédit (dettes)
            LigneEcriture.objects.create(
                ecriture=ecriture,
                compte=compte_cnss,
                libelle="CNSS à payer",
                debit=0,
                credit=bulletin.salaire_brut * Decimal('0.05'),
                entreprise=self.request.user.entreprise
            )
            
            LigneEcriture.objects.create(
                ecriture=ecriture,
                compte=compte_impot,
                libelle="Impôt à payer",
                debit=0,
                credit=bulletin.salaire_brut * Decimal('0.03'),
                entreprise=self.request.user.entreprise
            )
            
            LigneEcriture.objects.create(
                ecriture=ecriture,
                compte=compte_banque,
                libelle="Net à payer",
                debit=0,
                credit=bulletin.net_a_payer,
                entreprise=self.request.user.entreprise
            )
            
        except Exception as e:
            print(f"Erreur génération écriture comptable: {e}")
            
class GenererBulletinAutoView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, View):
    """Vue pour générer automatiquement les bulletins"""
    permission_required = "grh.add_bulletinpaie"
    
    def post(self, request):
        periode = request.POST.get('periode', datetime.now().strftime('%Y-%m'))
        employe_id = request.POST.get('employe')
        
        try:
            if employe_id:
                # Générer pour un employé spécifique
                employe = get_object_or_404(Employe, id=employe_id, entreprise=request.user.entreprise)
                bulletin = CalculPaieService.generer_bulletin_automatique(employe, periode)
                
                if bulletin:
                    messages.success(request, f"Bulletin généré pour {employe.nom_complet}")
                    return redirect('grh:bulletin_detail', pk=bulletin.pk)
                else:
                    messages.error(request, f"Impossible de générer le bulletin pour {employe.nom_complet}")
            else:
                # Générer pour tous les employés actifs
                bulletins_crees = CalculPaieService.generer_bulletins_masse(periode, request.user.entreprise)
                
                if bulletins_crees:
                    messages.success(request, f"{len(bulletins_crees)} bulletins générés avec succès")
                else:
                    messages.warning(request, "Aucun bulletin généré (vérifiez les contrats et présences)")
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la génération: {str(e)}")
        
        return redirect('grh:bulletin_list')

class BulletinPaieDetailView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, DetailView):
    model = BulletinPaie
    template_name = "grh/paie/detail.html"
    permission_required = "grh.view_bulletinpaie"
    context_object_name = "bulletin"

# Vues pour les congés
class CongeListView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, ListView):
    model = Conge
    template_name = "grh/conge/list.html"
    permission_required = "grh.view_conge"
    context_object_name = "conges"
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Conge.objects.filter(entreprise=self.request.user.entreprise)
        
        # Filtres
        statut = self.request.GET.get('statut')
        type_conge = self.request.GET.get('type_conge')
        employe_id = self.request.GET.get('employe')
        mois = self.request.GET.get('mois')
        
        if statut:
            queryset = queryset.filter(statut=statut)
        if type_conge:
            queryset = queryset.filter(type_conge=type_conge)
        if employe_id:
            queryset = queryset.filter(employe_id=employe_id)
        if mois:
            # Filtre par mois (format YYYY-MM)
            year, month = map(int, mois.split('-'))
            queryset = queryset.filter(
                date_debut__year=year,
                date_debut__month=month
            )
        
        return queryset.order_by('-date_demande')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Choices pour les filtres
        context['statut_choices'] = Conge.STATUT_CHOICES
        context['type_choices'] = Conge.TYPE_CONGE_CHOICES
        
        # Liste des employés pour le filtre
        context['employes'] = Employe.objects.filter(
            entreprise=self.request.user.entreprise,
            statut='ACTIF'
        )
        
        # Statistiques
        queryset = Conge.objects.filter(entreprise=self.request.user.entreprise)
        context['stats'] = {
            'total': queryset.count(),
            'valides': queryset.filter(statut='VALIDE').count(),
            'demandes': queryset.filter(statut='DEMANDE').count(),
            'rejetes': queryset.filter(statut='REJETE').count(),
        }
        
        return context

class CongeCreateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, CreateView):
    model = Conge
    form_class = CongeForm
    template_name = "grh/conge/form.html"
    permission_required = "grh.add_conge"
    success_url = reverse_lazy('grh:conge_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["entreprise"] = self.request.user.entreprise
        return kwargs
    
    def form_valid(self, form):
        form.instance.entreprise = self.request.user.entreprise
        return super().form_valid(form)
from django.utils import timezone
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views import View

class CongeValidationView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, View):
    """Vue pour valider ou rejeter un congé"""
    permission_required = "grh.change_conge"
    
    def post(self, request, pk, action):
        conge = get_object_or_404(Conge, pk=pk, entreprise=request.user.entreprise)
        
        if action in ['VALIDE', 'REJETE']:
            conge.statut = action
            conge.date_validation = timezone.now()
            
            # Essayer de récupérer l'employé connecté (si le user a un profil employé)
            try:
                # Vérifier si l'utilisateur a un profil employé
                if hasattr(request.user, 'employe'):
                    conge.valide_par = request.user.employe
                else:
                    # Si pas de profil employé, chercher un employé admin ou responsable
                    employe_admin = Employe.objects.filter(
                        entreprise=request.user.entreprise,
                        user=request.user
                    ).first()
                    if employe_admin:
                        conge.valide_par = employe_admin
            except Exception as e:
                # En cas d'erreur, on continue sans définir valide_par
                print(f"Erreur attribution validateur: {e}")
                pass
                
            conge.save()
            
            message = f"Congé {conge.get_statut_display().lower()} avec succès !"
            messages.success(request, message)
        else:
            messages.error(request, "Action invalide")
        
        return redirect('grh:conge_list')
   
   
class CongeDetailView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, DetailView):
    model = Conge
    template_name = "grh/conge/detail.html"
    permission_required = "grh.view_conge"
    context_object_name = "conge"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ajouter des informations supplémentaires si nécessaire
        return context   
   
   
   
   
   
    
from .forms import PresenceForm, ImportPresenceForm
import csv
from datetime import datetime
from django.http import JsonResponse

class PresenceListView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, ListView):
    model = Presence
    template_name = "grh/presence/list.html"
    permission_required = "grh.view_presence"
    context_object_name = "presences"
    
    def get_queryset(self):
        queryset = Presence.objects.filter(entreprise=self.request.user.entreprise)
        
        # Filtrage par employé
        employe_id = self.request.GET.get('employe')
        if employe_id:
            queryset = queryset.filter(employe_id=employe_id)
        
        # Filtrage par date
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        if date_debut and date_fin:
            queryset = queryset.filter(date__gte=date_debut, date__lte=date_fin)
        
        return queryset.order_by('-date', 'employe__nom')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employes'] = Employe.objects.filter(entreprise=self.request.user.entreprise, statut='ACTIF')
        return context

class PresenceCreateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, CreateView):
    model = Presence
    form_class = PresenceForm
    template_name = "grh/presence/form.html"
    permission_required = "grh.add_presence"
    success_url = reverse_lazy('grh:presence_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["entreprise"] = self.request.user.entreprise
        return kwargs
    
    def form_valid(self, form):
        form.instance.entreprise = self.request.user.entreprise
        
        # Calcul automatique des heures travaillées
        if form.instance.heure_arrivee and form.instance.heure_depart and form.instance.statut == 'PRESENT':
            from datetime import datetime
            arrivee = datetime.combine(form.instance.date, form.instance.heure_arrivee)
            depart = datetime.combine(form.instance.date, form.instance.heure_depart)
            duree = depart - arrivee
            form.instance.heures_travaillees = round(duree.total_seconds() / 3600, 2)
        
        return super().form_valid(form)

class PresenceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, UpdateView):
    model = Presence
    form_class = PresenceForm
    template_name = "grh/presence/form.html"
    permission_required = "grh.change_presence"
    success_url = reverse_lazy('grh:presence_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["entreprise"] = self.request.user.entreprise
        return kwargs
    
class PresenceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, DeleteView):
    model = Presence
    template_name = "grh/presence/confirm_delete.html"
    permission_required = "grh.delete_presence"
    success_url = reverse_lazy('grh:presence_list')
    
    def get_queryset(self):
        return Presence.objects.filter(entreprise=self.request.user.entreprise)
    
    def delete(self, request, *args, **kwargs):
        # Récupérer l'objet avant suppression pour le message
        self.object = self.get_object()
        employe_nom = self.object.employe.nom_complet
        date_presence = self.object.date
        
        # Effectuer la suppression
        response = super().delete(request, *args, **kwargs)
        
        # Ajouter le message de succès
        messages.success(
            self.request, 
            f"Présence de {employe_nom} du {date_presence.strftime('%d/%m/%Y')} supprimée avec succès !"
        )
        
        return response

class ImportPresenceView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, FormView):
    template_name = "grh/presence/import.html"
    form_class = ImportPresenceForm
    permission_required = "grh.add_presence"
    success_url = reverse_lazy('grh:presence_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["entreprise"] = self.request.user.entreprise
        return kwargs
    
    def form_valid(self, form):
        fichier = form.cleaned_data['fichier_csv']
        mois = form.cleaned_data['mois']
        
        try:
            # Lire le fichier CSV
            decoded_file = fichier.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            
            presences_importees = 0
            erreurs = []
            
            for ligne, row in enumerate(reader, start=2):  # ligne 1 = entêtes
                try:
                    # Trouver l'employé par matricule ou nom
                    employe = Employe.objects.filter(
                        entreprise=self.request.user.entreprise,
                        matricule=row.get('matricule', '')
                    ).first()
                    
                    if not employe:
                        employe = Employe.objects.filter(
                            entreprise=self.request.user.entreprise,
                            nom=row.get('nom', ''),
                            prenom=row.get('prenom', '')
                        ).first()
                    
                    if employe:
                        # Créer la présence
                        Presence.objects.create(
                            entreprise=self.request.user.entreprise,
                            employe=employe,
                            date=datetime.strptime(row['date'], '%Y-%m-%d').date(),
                            heure_arrivee=datetime.strptime(row['heure_arrivee'], '%H:%M').time(),
                            heure_depart=datetime.strptime(row['heure_depart'], '%H:%M').time(),
                            statut=row.get('statut', 'PRESENT'),
                            notes=row.get('notes', '')
                        )
                        presences_importees += 1
                    else:
                        erreurs.append(f"Ligne {ligne}: Employé non trouvé")
                        
                except Exception as e:
                    erreurs.append(f"Ligne {ligne}: {str(e)}")
            
            if presences_importees > 0:
                messages.success(self.request, f"{presences_importees} présences importées avec succès")
            if erreurs:
                messages.warning(self.request, f"{len(erreurs)} erreurs lors de l'importation")
                
        except Exception as e:
            messages.error(self.request, f"Erreur lors de l'importation: {str(e)}")
        
        return super().form_valid(form)

class CalendrierPresenceView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, GRHBaseMixin, TemplateView):
    template_name = "grh/presence/calendrier.html"
    permission_required = "grh.view_presence"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employes'] = Employe.objects.filter(entreprise=self.request.user.entreprise, statut='ACTIF')
        return context

class GetPresencesDataView(LoginRequiredMixin, EntrepriseAccessMixin, View):
    """API pour récupérer les données de présence au format JSON"""
    
    def get(self, request):
        mois = request.GET.get('mois', datetime.now().strftime('%Y-%m'))
        employe_id = request.GET.get('employe')
        
        # Convertir le mois en dates
        annee, mois_num = map(int, mois.split('-'))
        date_debut = datetime(annee, mois_num, 1)
        if mois_num == 12:
            date_fin = datetime(annee + 1, 1, 1) - timedelta(days=1)
        else:
            date_fin = datetime(annee, mois_num + 1, 1) - timedelta(days=1)
        
        # Récupérer les présences
        presences = Presence.objects.filter(
            entreprise=request.user.entreprise,
            date__gte=date_debut,
            date__lte=date_fin
        )
        
        if employe_id:
            presences = presences.filter(employe_id=employe_id)
        
        # Formater les données pour le calendrier
        data = []
        for presence in presences:
            data.append({
                'title': f"{presence.employe.nom_complet} - {presence.get_statut_display()}",
                'start': presence.date.isoformat(),
                'backgroundColor': self.get_color_for_status(presence.statut),
                'borderColor': self.get_color_for_status(presence.statut),
                'extendedProps': {
                    'employe': presence.employe.nom_complet,
                    'heures': str(presence.heures_travaillees),
                    'statut': presence.get_statut_display()
                }
            })
        
        return JsonResponse(data, safe=False)
    
    def get_color_for_status(self, statut):
        colors = {
            'PRESENT': '#28a745',
            'ABSENT': '#dc3545',
            'CONGE': '#17a2b8',
            'MALADIE': '#ffc107',
            'AUTRE': '#6c757d'
        }
        return colors.get(statut, '#6c757d')
    
    
    
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
@method_decorator(csrf_exempt, name='dispatch')
class CalculerPaieAPIView(LoginRequiredMixin, EntrepriseAccessMixin, View):
    """API pour calculer automatiquement la paie"""
    
    def get(self, request):
        employe_id = request.GET.get('employe')
        periode = request.GET.get('periode')
        
        print(f"API appelée - Employé: {employe_id}, Période: {periode}")
        
        try:
            employe = Employe.objects.get(id=employe_id, entreprise=request.user.entreprise)
            print(f"Employé trouvé: {employe.nom_complet}")
            
            # Validation de la période
            if not periode or len(periode) != 7:
                return JsonResponse({
                    'success': False,
                    'message': 'Format de période invalide. Utilisez YYYY-MM'
                })
            
            # Vérifier d'abord s'il y a un contrat
            from datetime import date
            annee, mois = map(int, periode.split('-'))
            date_debut = date(annee, mois, 1)
            if mois == 12:
                date_fin = date(annee + 1, 1, 1) - timedelta(days=1)
            else:
                date_fin = date(annee, mois + 1, 1) - timedelta(days=1)
            
            # Chercher un contrat actif
            contrat = Contrat.objects.filter(
                employe=employe,
                statut='EN_COURS',
                date_debut__lte=date_fin,
                date_fin__gte=date_debut
            ).order_by('-date_debut').first()
            
            if not contrat:
                print(f"Aucun contrat ACTIF trouvé pour {employe.nom_complet}")
                return JsonResponse({
                    'success': False,
                    'message': f"Aucun contrat actif trouvé pour {employe.nom_complet} sur la période {periode}"
                })
            
            print(f"Contrat sélectionné: {contrat.reference} (Début: {contrat.date_debut}, Fin: {contrat.date_fin})")
            
            # Utiliser le service de calcul de paie
            from .services import CalculPaieService
            salaire_brut, jours_travailles, heures_supp, contrat_calc = CalculPaieService.calculer_salaire_brut(employe, periode)
            
            if salaire_brut == 0:
                return JsonResponse({
                    'success': False,
                    'message': 'Impossible de calculer le salaire. Vérifiez les données du contrat.'
                })
            
            total_cotisations = CalculPaieService.calculer_cotisations(salaire_brut)
            salaire_net = salaire_brut - total_cotisations
            
            # Préparer les lignes détaillées
            lignes = [
                {'type_ligne': 'GAINS', 'libelle': 'Salaire de base', 'montant': float(salaire_brut), 'ordre': 1},
                {'type_ligne': 'RETENUES', 'libelle': 'Cotisations sociales (10%)', 'montant': float(total_cotisations), 'ordre': 2},
            ]
            
            return JsonResponse({
                'success': True,
                'salaire_brut': float(salaire_brut),
                'total_cotisations': float(total_cotisations),
                'salaire_net': float(salaire_net),
                'net_a_payer': float(salaire_net),
                'jours_travailles': jours_travailles,
                'heures_travaillees': float(heures_supp),
                'contrat_id': contrat.id,
                'lignes': lignes,
                'message': f"Calcul basé sur le contrat {contrat.reference} ({contrat.date_debut} au {contrat.date_fin or 'indéterminé'})"
            })
                
        except Employe.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Employé non trouvé'})
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Format de période invalide. Utilisez YYYY-MM'})
        except Exception as e:
            print(f"Erreur générale: {str(e)}")
            return JsonResponse({'success': False, 'message': f'Erreur lors du calcul: {str(e)}'})
        
        
    from django.http import HttpResponse
from django.views.generic import View
from django.utils.text import slugify

class DownloadBulletinPDFView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, View):
    """Vue pour télécharger le bulletin de paie en PDF"""
    permission_required = "grh.view_bulletinpaie"
    
    def get(self, request, pk):
        bulletin = get_object_or_404(BulletinPaie, pk=pk, entreprise=request.user.entreprise)
        
        if bulletin.fichier_bulletin:
            # Si le fichier existe, le servir
            response = HttpResponse(bulletin.fichier_bulletin.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{slugify(bulletin.employe.nom_complet)}_{bulletin.periode}.pdf"'
            return response
        else:
            # Générer le PDF à la volée
            from .utils import BulletinPaiePDFGenerator
            pdf_buffer = BulletinPaiePDFGenerator.generate_bulletin_pdf(bulletin)
            
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{slugify(bulletin.employe.nom_complet)}_{bulletin.periode}.pdf"'
            return response
class GenerateBulletinPDFView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, View):
    """Vue pour régénérer le PDF"""
    permission_required = "grh.change_bulletinpaie"
    
    def post(self, request, pk):
        bulletin = get_object_or_404(BulletinPaie, pk=pk, entreprise=request.user.entreprise)
        
        try:
            from .utils import BulletinPaiePDFGenerator
            fichier = BulletinPaiePDFGenerator.save_bulletin_pdf(bulletin)
            
            messages.success(request, f"Bulletin de paie régénéré avec succès !")
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la génération du PDF: {str(e)}")
            # Fallback: utiliser une méthode simplifiée
            try:
                from .utils import BulletinPaiePDFGenerator
                # Régénérer sans les informations d'entreprise
                pdf_buffer = BulletinPaiePDFGenerator.generate_bulletin_pdf(bulletin)
                # ... sauvegarde
                messages.warning(request, "Bulletin généré avec des informations limitées")
            except:
                messages.error(request, "Impossible de générer le bulletin PDF")
        
        return redirect('grh:bulletin_detail', pk=bulletin.pk)