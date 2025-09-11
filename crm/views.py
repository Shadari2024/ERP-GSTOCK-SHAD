from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView, TemplateView, View
from django.urls import reverse_lazy,reverse
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from STOCK.models import *
from .models import (
    ClientCRM, Opportunite, Activite, NoteClient, 
    SourceLead, StatutOpportunite, TypeActivite,
    PipelineVente, ObjectifCommercial
)
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.management import call_command
from django.http import HttpResponseRedirect
from django.urls import reverse
import logging

from django.views.generic import DetailView
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from ventes.models import Devis, Commande, Facture, BonLivraison
from STOCK.models import Client  # Import du modèle réel
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView
from django.db.models import Sum

from STOCK.models import Client
from ventes.models import Facture, Commande, Devis, BonLivraison
from crm.mixins import EntrepriseAccessMixin

from .forms import (
    ClientCRMForm, OpportuniteForm, ActiviteForm, 
    NoteClientForm, ObjectifCommercialForm,StatutOpportuniteForm,TypeActiviteForm
)
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from parametres.models import ConfigurationSAAS

from django.utils.translation import gettext_lazy as _  # <-- AJOUTEZ CET IMPOR
# ... le reste de votre code ...
from django.views.generic import TemplateView
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from parametres.mixins import EntrepriseAccessMixin
from .models import ClientCRM, Opportunite, Activite, StatutOpportunite

class AccueilCRMView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, TemplateView):
    template_name = "crm/acceuil.html"
    permission_required = "crm.add_clientcrm"
    
    def dispatch(self, request, *args, **kwargs):
        # Définir l'entreprise sur la requête avant que le mixin ne vérifie
        if hasattr(request.user, 'entreprise') and request.user.entreprise:
            request.entreprise = request.user.entreprise
        else:
            # Si l'utilisateur n'a pas d'entreprise, laisser le mixin gérer la redirection
            pass
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            entreprise = self.request.entreprise
            
            # Récupérer les statuts terminés
            statuts_termines_ids = self.get_statuts_termines_ids(entreprise)
            
            # Récupérer les statistiques
            stats = self.get_crm_statistics(entreprise, statuts_termines_ids)
            context.update(stats)
            
            # Configuration de la devise
            context['devise_principale_symbole'] = self.get_devise_symbol(entreprise)
            
        except Exception as e:
            # Gestion des erreurs silencieuse pour ne pas casser la page
            context['error'] = f"Erreur lors du chargement des données: {str(e)}"
            context['total_clients'] = 0
            context['opportunites_actives'] = 0
            context['activites_du_jour'] = 0
            context['taches_en_retard'] = 0
            context['opportunites_recentes'] = []
            context['activites_a_venir'] = []
            context['devise_principale_symbole'] = "€"
        
        return context
    
    def get_statuts_termines_ids(self, entreprise):
        """Retourne les IDs des statuts terminés"""
        return list(StatutOpportunite.objects.filter(
            entreprise=entreprise
        ).filter(
            Q(est_gagnant=True) | Q(est_perdant=True)
        ).values_list('id', flat=True))
    
    def get_crm_statistics(self, entreprise, statuts_termines_ids):
        """Récupère toutes les statistiques CRM"""
        return {
            'total_clients': ClientCRM.objects.filter(entreprise=entreprise).count(),
            'opportunites_actives': Opportunite.objects.filter(
                entreprise=entreprise
            ).exclude(statut_id__in=statuts_termines_ids).count(),
            'activites_du_jour': Activite.objects.filter(
                entreprise=entreprise,
                date_debut__date=timezone.now().date()
            ).count(),
            'taches_en_retard': Activite.objects.filter(
                entreprise=entreprise,
                date_echeance__lt=timezone.now(),
                statut__in=['planifie', 'en_cours']
            ).count(),
            'opportunites_recentes': Opportunite.objects.filter(
                entreprise=entreprise
            ).select_related('client', 'statut').order_by('-date_creation')[:5],
            'activites_a_venir': Activite.objects.filter(
                entreprise=entreprise,
                date_debut__gte=timezone.now()
            ).select_related('type_activite').order_by('date_debut')[:5],
        }
    
    def get_devise_symbol(self, entreprise):
        """Retourne le symbole de la devise principale"""
        try:
            from parametres.models import ConfigurationSAAS
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            return config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except:
            return "€"

from django.views.generic import ListView
from django.db.models import Q
from STOCK.models import Client as StockClient

class ClientListView(EntrepriseAccessMixin, ListView):
    model = StockClient
    template_name = "crm/client/list.html"  # Chemin correct
    permission_required = "STOCK.view_client"
    context_object_name = "clients"
    paginate_by = 20
    
    def get_queryset(self):
        queryset = StockClient.objects.filter(entreprise=self.request.user.entreprise)
        
        # Filtres
        search = self.request.GET.get('search')
        type_client = self.request.GET.get('type_client')
        statut = self.request.GET.get('statut')
        
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(email__icontains=search) |
                Q(telephone__icontains=search) |
                Q(ville__icontains=search) |
                Q(code_client__icontains=search)
            )
        
        if type_client:
            queryset = queryset.filter(type_client=type_client)
        
        if statut:
            queryset = queryset.filter(statut=statut)
        
        return queryset.select_related('devise_preferee').order_by('nom')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques pour le tableau de bord
        queryset = self.get_queryset()
        context['total_clients'] = StockClient.objects.filter(entreprise=self.request.user.entreprise).count()
        context['clients_actifs'] = queryset.filter(statut='ACT').count()
        context['clients_inactifs'] = queryset.filter(statut='INA').count()
        
        return context

class ClientCreateView(EntrepriseAccessMixin, CreateView):
    model = Client  # Utilisez le modèle Client réel, pas le proxy
    form_class = ClientCRMForm
    template_name = "crm/client/form.html"
    permission_required = "crm.add_clientcrm"
    success_url = reverse_lazy('crm:client_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['entreprise'] = self.request.user.entreprise
        return kwargs
    
    def form_valid(self, form):
        # Assigner l'entreprise et l'utilisateur
        form.instance.entreprise = self.request.user.entreprise
        form.instance.cree_par = self.request.user
        
        # Générer le code client si nécessaire
        if not form.instance.code_client:
            form.instance.code_client = self.generate_client_code(
                form.instance.type_client, 
                self.request.user.entreprise
            )
        
        messages.success(self.request, "Client créé avec succès.")
        return super().form_valid(form)
    
    def generate_client_code(self, type_client, entreprise):
        """Génère un code client unique"""
        from django.db import transaction
        from django.db.models import Max
        
        with transaction.atomic():
            prefix = type_client[:2].upper()
            
            # Cherche le dernier code client pour cette entreprise et ce préfixe
            max_code_obj = Client.objects.filter(
                entreprise=entreprise,
                code_client__startswith=f'{prefix}-'
            ).aggregate(max_val=Max('code_client'))
            
            max_code = max_code_obj['max_val']
            
            next_num = 1
            if max_code:
                try:
                    num_part = max_code.split('-')[-1]
                    next_num = int(num_part) + 1
                except (ValueError, IndexError):
                    next_num = 1
            
            return f"{prefix}-{next_num:04d}"


from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from STOCK.models import Client  # Import du modèle réel

class ClientUpdateView(EntrepriseAccessMixin, UpdateView):
    model = Client  # Utilisez le modèle réel Client
    form_class = ClientCRMForm
    template_name = "crm/client/form.html"
    permission_required = "STOCK.change_client"  # Permission du modèle réel
    success_url = reverse_lazy('crm:client_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['entreprise'] = self.request.user.entreprise
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, "Client modifié avec succès.")
        return super().form_valid(form)

class ClientDetailView(EntrepriseAccessMixin, DetailView):
    model = Client
    template_name = "crm/client/detail.html"
    permission_required = "STOCK.view_client"
    context_object_name = "client"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        client = self.get_object()
        entreprise = self.request.user.entreprise
        
        # Récupérer la devise principale depuis ConfigurationSAAS
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            context['devise_symbole'] = config_saas.devise_principale.symbole if config_saas.devise_principale else '$'
            context['devise_code'] = config_saas.devise_principale.code if config_saas.devise_principale else 'USD'
        except ConfigurationSAAS.DoesNotExist:
            context['devise_symbole'] = '$'
            context['devise_code'] = 'USD'

        try:
            # Récupérer les données des autres modules
            context['factures'] = Facture.objects.filter(
                client=client,
                entreprise=entreprise
            ).select_related('devis', 'commande').order_by('-date_facture')[:10]
            
            context['commandes'] = Commande.objects.filter(
                client=client,
                entreprise=entreprise
            ).select_related('devis').order_by('-date')[:10]
            
            context['devis'] = Devis.objects.filter(
                client=client,
                entreprise=entreprise
            ).order_by('-date')[:10]
            
            context['livraisons'] = BonLivraison.objects.filter(
                commande__client=client,
                entreprise=entreprise
            ).select_related('commande').order_by('-date')[:10]
            
            # Statistiques
            context['total_factures'] = Facture.objects.filter(
                client=client,
                entreprise=entreprise
            ).count()
            
            context['total_commandes'] = Commande.objects.filter(
                client=client,
                entreprise=entreprise
            ).count()
            
            context['total_devis'] = Devis.objects.filter(
                client=client,
                entreprise=entreprise
            ).count()
            
            context['total_livraisons'] = BonLivraison.objects.filter(
                commande__client=client,
                entreprise=entreprise
            ).count()
            
            # Chiffre d'affaires total
            total_ca = Facture.objects.filter(
                client=client,
                entreprise=entreprise,
                statut='paye'
            ).aggregate(total=Sum('total_ttc'))['total'] or 0
            context['chiffre_affaires'] = total_ca
            
            # Ajouter les opportunités du client
            context['opportunites'] = Opportunite.objects.filter(
                client=client,
                entreprise=entreprise
            ).select_related('statut', 'assigne_a').order_by('-date_creation')[:10]
            
            context['total_opportunites'] = context['opportunites'].count()
            
            # Valeur totale des opportunités
            valeur_opportunites = Opportunite.objects.filter(
                client=client,
                entreprise=entreprise
            ).aggregate(total=Sum('montant_estime'))['total'] or 0
            context['valeur_opportunites'] = valeur_opportunites
            
        except Exception as e:
            # Gestion d'erreur
            context['error'] = f"Erreur lors du chargement des données: {str(e)}"
            context['factures'] = []
            context['commandes'] = []
            context['devis'] = []
            context['livraisons'] = []
            context['opportunites'] = []
            context['total_factures'] = 0
            context['total_commandes'] = 0
            context['total_devis'] = 0
            context['total_livraisons'] = 0
            context['total_opportunites'] = 0
            context['chiffre_affaires'] = 0
            context['valeur_opportunites'] = 0
        
        return context
class StatutOpportuniteListView(EntrepriseAccessMixin, ListView):
    model = StatutOpportunite
    template_name = "crm/statut_opportunite/list.html"
    permission_required = "crm.view_statutopportunite"
    context_object_name = "statuts"
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.order_by('ordre')

class StatutOpportuniteCreateView(EntrepriseAccessMixin, CreateView):
    model = StatutOpportunite
    form_class = StatutOpportuniteForm
    template_name = "crm/statut_opportunite/form.html"
    permission_required = "crm.add_statutopportunite"
    success_url = reverse_lazy('crm:statut_opportunite_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['entreprise'] = self.request.user.entreprise
        return kwargs
    
    def form_valid(self, form):
        form.instance.entreprise = self.request.user.entreprise
        messages.success(self.request, _("Statut d'opportunité créé avec succès."))
        return super().form_valid(form)

class StatutOpportuniteUpdateView(EntrepriseAccessMixin, UpdateView):
    model = StatutOpportunite
    form_class = StatutOpportuniteForm
    template_name = "crm/statut_opportunite/form.html"
    permission_required = "crm.change_statutopportunite"
    success_url = reverse_lazy('crm:statut_opportunite_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['entreprise'] = self.request.user.entreprise
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, _("Statut d'opportunité modifié avec succès."))
        return super().form_valid(form)

class StatutOpportuniteDeleteView(EntrepriseAccessMixin, DeleteView):
    model = StatutOpportunite
    template_name = "crm/statut_opportunite/confirm_delete.html"
    permission_required = "crm.delete_statutopportunite"
    success_url = reverse_lazy('crm:statut_opportunite_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _("Statut d'opportunité supprimé avec succès."))
        return super().delete(request, *args, **kwargs) 
    
    
     
    
class OpportuniteKanbanView(EntrepriseAccessMixin, TemplateView):
    template_name = "crm/opportunite/kanban.html"
    permission_required = "crm.view_opportunite"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.user.entreprise
        
        # Récupérer la devise principale
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            context['devise_symbole'] = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            context['devise_symbole'] = "€"
        
        # Opportunités par statut pour le Kanban
        opportunites_par_statut = (
            Opportunite.objects.filter(entreprise=entreprise)
            .values('statut__nom', 'statut__couleur')
            .annotate(
                count=Count('id'),
                total=Sum('montant_estime')
            )
            .order_by('statut__ordre')
        )
        context['opportunites_par_statut'] = opportunites_par_statut
        
        # Toutes les opportunités pour peupler les colonnes
        opportunites = Opportunite.objects.filter(entreprise=entreprise).select_related(
            'client', 'statut', 'assigne_a'
        )
        context['opportunites'] = opportunites
        
        # Statistiques
        context['total_opportunites'] = opportunites.count()
        context['valeur_totale'] = opportunites.aggregate(
            total=Sum('montant_estime')
        )['total'] or 0
        
        # Calcul du taux de conversion
        # Correction de l'erreur
        # On filtre les opportunités gagnées ou perdues directement
        gagnees = opportunites.filter(statut__est_gagnant=True).count()
        perdues = opportunites.filter(statut__est_perdant=True).count()
        total_terminees = gagnees + perdues

        context['taux_conversion'] = (gagnees / total_terminees * 100) if total_terminees > 0 else 0
        context['opportunites_gagnees'] = gagnees
        
        # Filtres
        context['utilisateurs'] = User.objects.filter(entreprise=entreprise)
        
        return context

User = get_user_model()

class OpportuniteListView(EntrepriseAccessMixin, ListView):
    model = Opportunite
    template_name = "crm/opportunite/list.html"
    permission_required = "crm.view_opportunite"
    context_object_name = "opportunites"
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'client', 'statut', 'assigne_a', 'cree_par'
        )
        
        # Filtres
        search = self.request.GET.get('search')
        statut = self.request.GET.get('statut')
        assigne_a = self.request.GET.get('assigne_a')
        priorite = self.request.GET.get('priorite')
        
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(client__nom__icontains=search) |
                Q(description__icontains=search)
            )
        
        if statut:
            queryset = queryset.filter(statut_id=statut)
        
        if assigne_a:
            queryset = queryset.filter(assigne_a_id=assigne_a)
        
        if priorite:
            queryset = queryset.filter(priorite=priorite)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.user.entreprise
        
        # Filtres pour le template
        context['statuts'] = StatutOpportunite.objects.filter(entreprise=entreprise)
        context['utilisateurs'] = User.objects.filter(entreprise=entreprise)
        
        # Statistiques
        context['total_opportunites'] = self.get_queryset().count()
        context['valeur_totale'] = self.get_queryset().aggregate(
            total=Sum('montant_estime')
        )['total'] or 0
        
        # Récupérer la devise principale depuis ConfigurationSAAS
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            context['devise_symbole'] = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
            context['devise_code'] = config_saas.devise_principale.code if config_saas.devise_principale else "EUR"
        except ConfigurationSAAS.DoesNotExist:
            context['devise_symbole'] = "€"
            context['devise_code'] = "EUR"
        
        return context
    
class OpportuniteCreateView(EntrepriseAccessMixin, CreateView):
    model = Opportunite
    form_class = OpportuniteForm
    template_name = "crm/opportunite/form.html"
    permission_required = "crm.add_opportunite"
    success_url = reverse_lazy('crm:opportunite_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['entreprise'] = self.request.user.entreprise
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer la devise principale pour l'affichage dans le template
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            context['devise_symbole'] = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            context['devise_symbole'] = "€"
        
        return context
    
    def form_valid(self, form):
        form.instance.entreprise = self.request.user.entreprise
        form.instance.cree_par = self.request.user
        messages.success(self.request, _("Opportunité créée avec succès."))
        return super().form_valid(form)



class ConvertirOpportuniteEnDevisView(EntrepriseAccessMixin, View):
    """Vue pour convertir une opportunité en devis"""
    permission_required = "crm.change_opportunite"
    
    def post(self, request, pk):
        opportunite = get_object_or_404(Opportunite, pk=pk, entreprise=request.user.entreprise)
        
        try:
            devis = opportunite.convertir_en_devis(request)
            messages.success(
                request, 
                _(f"Opportunité convertie en devis avec succès. Devis #{devis.numero} créé.")
            )
            return redirect('ventes:devis_detail', pk=devis.pk)
            
        except Exception as e:
            messages.error(
                request, 
                _(f"Erreur lors de la conversion: {str(e)}")
            )
            return redirect('crm:opportunite_detail', pk=opportunite.pk)





class OpportuniteUpdateView(EntrepriseAccessMixin, UpdateView):
    model = Opportunite
    form_class = OpportuniteForm
    template_name = "crm/opportunite/form.html"
    permission_required = "crm.change_opportunite"
    success_url = reverse_lazy('crm:opportunite_list')
    
    def form_valid(self, form):
        messages.success(self.request, _("Opportunité modifiée avec succès."))
        return super().form_valid(form)
    
class OpportuniteDetailView(EntrepriseAccessMixin, DetailView):
    model = Opportunite
    template_name = "crm/opportunite/detail.html"
    permission_required = "crm.view_opportunite"
    context_object_name = "opportunite"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        opportunite = self.get_object()
        
        # Activités liées
        context['activites'] = opportunite.activites.all().select_related(
            'type_activite', 'assigne_a'
        )[:10]
        
        # Récupérer la devise principale depuis ConfigurationSAAS
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            context['devise_symbole'] = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            context['devise_symbole'] = "€"
        
        return context


class TypeActiviteListView(EntrepriseAccessMixin, ListView):
    model = TypeActivite
    template_name = "crm/type_activite/list.html"
    permission_required = "crm.view_typeactivite"
    context_object_name = "types_activite"
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.order_by('nom')

class TypeActiviteCreateView(EntrepriseAccessMixin, CreateView):
    model = TypeActivite
    form_class = TypeActiviteForm
    template_name = "crm/type_activite/form.html"
    permission_required = "crm.add_typeactivite"
    success_url = reverse_lazy('crm:type_activite_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['entreprise'] = self.request.user.entreprise
        return kwargs
    
    def form_valid(self, form):
        form.instance.entreprise = self.request.user.entreprise
        messages.success(self.request, _("Type d'activité créé avec succès."))
        return super().form_valid(form)

class TypeActiviteUpdateView(EntrepriseAccessMixin, UpdateView):
    model = TypeActivite
    form_class = TypeActiviteForm
    template_name = "crm/type_activite/form.html"
    permission_required = "crm.change_typeactivite"
    success_url = reverse_lazy('crm:type_activite_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['entreprise'] = self.request.user.entreprise
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, _("Type d'activité modifié avec succès."))
        return super().form_valid(form)

class TypeActiviteDeleteView(EntrepriseAccessMixin, DeleteView):
    model = TypeActivite
    template_name = "crm/type_activite/confirm_delete.html"
    permission_required = "crm.delete_typeactivite"
    success_url = reverse_lazy('crm:type_activite_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _("Type d'activité supprimé avec succès."))
        return super().delete(request, *args, **kwargs)







class ActiviteListView(EntrepriseAccessMixin, ListView):
    model = Activite
    template_name = "crm/activite/list.html"
    permission_required = "crm.view_activite"
    context_object_name = "activites"
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'type_activite', 'assigne_a', 'cree_par'
        ).prefetch_related('clients', 'opportunites')
        
        # Filtres
        search = self.request.GET.get('search')
        type_activite = self.request.GET.get('type_activite')
        statut = self.request.GET.get('statut')
        priorite = self.request.GET.get('priorite')
        assigne_a = self.request.GET.get('assigne_a')
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        
        if search:
            queryset = queryset.filter(
                Q(sujet__icontains=search) |
                Q(description__icontains=search) |
                Q(clients__nom__icontains=search) |
                Q(opportunites__nom__icontains=search)
            ).distinct()
        
        if type_activite:
            queryset = queryset.filter(type_activite_id=type_activite)
        
        if statut:
            queryset = queryset.filter(statut=statut)
        
        if priorite:
            queryset = queryset.filter(priorite=priorite)
        
        if assigne_a:
            queryset = queryset.filter(assigne_a_id=assigne_a)
        
        if date_debut:
            queryset = queryset.filter(date_debut__date__gte=date_debut)
        
        if date_fin:
            queryset = queryset.filter(date_debut__date__lte=date_fin)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filtres pour le template
        context['types_activite'] = TypeActivite.objects.filter(entreprise=self.request.user.entreprise)
        context['utilisateurs'] = User.objects.filter(entreprise=self.request.user.entreprise)
        
        # Statistiques
        context['activites_en_retard'] = self.get_queryset().filter(
            date_echeance__lt=timezone.now(),
            statut__in=['planifie', 'en_cours']
        ).count()
        
        context['activites_aujourdhui'] = self.get_queryset().filter(
            date_debut__date=timezone.now().date()
        ).count()
        
        return context

class ActiviteCreateView(EntrepriseAccessMixin, CreateView):
    model = Activite
    form_class = ActiviteForm
    template_name = "crm/activite/form.html"
    permission_required = "crm.add_activite"
    success_url = reverse_lazy('crm:activite_list')
    
    def form_valid(self, form):
        form.instance.entreprise = self.request.user.entreprise
        form.instance.cree_par = self.request.user
        messages.success(self.request, _("Activité créée avec succès."))
        return super().form_valid(form)

class ActiviteUpdateView(EntrepriseAccessMixin, UpdateView):
    model = Activite
    form_class = ActiviteForm
    template_name = "crm/activite/form.html"
    permission_required = "crm.change_activite"
    success_url = reverse_lazy('crm:activite_list')
    
    def form_valid(self, form):
        messages.success(self.request, _("Activité modifiée avec succès."))
        return super().form_valid(form)


class ActiviteDetailView(EntrepriseAccessMixin, DetailView):
    model = Activite
    template_name = "crm/activite/detail.html"
    permission_required = "crm.view_activite"
    context_object_name = "activite"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        activite = self.get_object()
        
        # Récupérer la devise principale depuis ConfigurationSAAS
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            context['devise_symbole'] = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            context['devise_symbole'] = "€"
        
        return context

class ActiviteCalendarView(EntrepriseAccessMixin, TemplateView):
    template_name = "crm/activite/calendar.html"
    permission_required = "crm.view_activite"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer les activités pour le calendrier
        activites = Activite.objects.filter(
            entreprise=self.request.user.entreprise
        ).select_related('type_activite', 'assigne_a')
        
        context['activites_json'] = [
            {
                'id': act.id,
                'title': act.sujet,
                'start': act.date_debut.isoformat(),
                'end': act.date_echeance.isoformat(),
                'color': act.type_activite.couleur if act.type_activite else '#007bff',
                'url': reverse('crm:activite_detail', kwargs={'pk': act.id}),  # Utilisez le bon nom d'URL
            }
            for act in activites
        ]
        
        return context
    
class TableauDeBordView(EntrepriseAccessMixin, TemplateView):
    template_name = "crm/rapport/tableau_de_bord.html"
    permission_required = "crm.view_tableau_de_bord"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.user.entreprise
        
        # Récupérer la devise principale depuis ConfigurationSAAS
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            context['devise_symbole'] = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            context['devise_symbole'] = "€"
        
        # Statistiques clients
        context['total_clients'] = ClientCRM.objects.filter(entreprise=entreprise).count()
        context['clients_actifs'] = ClientCRM.objects.filter(entreprise=entreprise, statut='ACT').count()
        context['nouveaux_clients_mois'] = ClientCRM.objects.filter(
            entreprise=entreprise,
            cree_le__month=timezone.now().month,
            cree_le__year=timezone.now().year
        ).count()
        
        # Statistiques opportunités
        opportunites = Opportunite.objects.filter(entreprise=entreprise)
        context['total_opportunites'] = opportunites.count()
        context['valeur_pipeline'] = opportunites.aggregate(
            total=Sum('montant_estime')
        )['total'] or 0
        
        # Calculer la valeur attendue avec annotation
        from django.db.models import F, ExpressionWrapper, FloatField
        opportunites_avec_valeur = opportunites.annotate(
            valeur_calculee=ExpressionWrapper(
                F('montant_estime') * F('probabilite') / 100.0,
                output_field=FloatField()
            )
        )
        context['valeur_attendue'] = opportunites_avec_valeur.aggregate(
            total=Sum('valeur_calculee')
        )['total'] or 0
        
        # Opportunités par statut
        context['opportunites_par_statut'] = (
            opportunites.values('statut__nom', 'statut__couleur')
            .annotate(count=Count('id'), total=Sum('montant_estime'))
            .order_by('-total')
        )
        
        # Activités à venir
        context['activites_a_venir'] = Activite.objects.filter(
            entreprise=entreprise,
            date_debut__gte=timezone.now(),
            statut__in=['planifie', 'en_cours']
        ).select_related('type_activite', 'assigne_a')[:10]
        
        # Opportunités en retard
        statuts_non_termines = StatutOpportunite.objects.filter(
            entreprise=entreprise,
            est_gagnant=False,
            est_perdant=False
        )
        
        context['opportunites_en_retard'] = opportunites.filter(
            date_fermeture_prevue__lt=timezone.now().date(),
            statut__in=statuts_non_termines
        ).select_related('client', 'statut')[:5]
        
        # Meilleurs clients (par chiffre d'affaires)
        clients = ClientCRM.objects.filter(entreprise=entreprise)[:5]
        context['meilleurs_clients'] = [
            {
                'client': client,
                'chiffre_affaires': client.valeur_commerciale
            }
            for client in clients
        ]
        
        return context
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from django.contrib.auth import get_user_model
from parametres.models import ConfigurationSAAS
from .models import Opportunite, StatutOpportunite

User = get_user_model()
class PerformancesView(EntrepriseAccessMixin, TemplateView):
    template_name = "crm/rapport/performances.html"
    permission_required = "crm.view_performances"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.user.entreprise
        
        # Récupérer la devise principale depuis ConfigurationSAAS
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            context['devise_symbole'] = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
            context['devise_code'] = config_saas.devise_principale.code if config_saas.devise_principale else "EUR"
        except ConfigurationSAAS.DoesNotExist:
            context['devise_symbole'] = "€"
            context['devise_code'] = "EUR"
        
        # Récupérer les statuts terminés (gagnants et perdants)
        statuts_termines = StatutOpportunite.objects.filter(
            Q(est_gagnant=True) | Q(est_perdant=True),
            entreprise=entreprise
        )
        
        # Taux de conversion
        opportunites_terminees = Opportunite.objects.filter(
            statut__in=statuts_termines,
            entreprise=entreprise
        )
        
        total_terminees = opportunites_terminees.count()
        gagnees = opportunites_terminees.filter(statut__est_gagnant=True).count()
        
        context['taux_conversion'] = (gagnees / total_terminees * 100) if total_terminees > 0 else 0
        
        # Valeur moyenne des opportunités gagnées
        opportunites_gagnees = Opportunite.objects.filter(
            statut__est_gagnant=True,
            entreprise=entreprise
        )
        
        context['valeur_moyenne'] = opportunites_gagnees.aggregate(
            moyenne=Avg('montant_estime')
        )['moyenne'] or 0
        
        # Valeur totale des opportunités gagnées
        context['valeur_totale_gagnees'] = opportunites_gagnees.aggregate(
            total=Sum('montant_estime')
        )['total'] or 0
        
        
        # Taux de conversion
        opportunites_terminees = Opportunite.objects.filter(
            entreprise=entreprise,
            statut__in=statuts_termines
        )
        
        total_terminees = opportunites_terminees.count()
        gagnees = opportunites_terminees.filter(statut__est_gagnant=True).count()
        
        context['taux_conversion'] = (gagnees / total_terminees * 100) if total_terminees > 0 else 0
        
        # Valeur moyenne des opportunités gagnées
        opportunites_gagnees = Opportunite.objects.filter(
            entreprise=entreprise,
            statut__est_gagnant=True
        )
        
        context['valeur_moyenne'] = opportunites_gagnees.aggregate(
            moyenne=Avg('montant_estime')
        )['moyenne'] or 0
        
        # Valeur totale des opportunités gagnées
        context['valeur_totale_gagnees'] = opportunites_gagnees.aggregate(
            total=Sum('montant_estime')
        )['total'] or 0
        
        # Nombre total d'opportunités
        context['total_opportunites'] = Opportunite.objects.filter(
            entreprise=entreprise
        ).count()
        
        # Opportunités en cours (non terminées)
        statuts_non_termines = StatutOpportunite.objects.filter(
            entreprise=entreprise,
            est_gagnant=False,
            est_perdant=False
        )
        
        context['opportunites_en_cours'] = Opportunite.objects.filter(
            entreprise=entreprise,
            statut__in=statuts_non_termines
        ).count()
        
        # Délai moyen de vente (pour les opportunités gagnées)
        opportunites_gagnees_avec_dates = opportunites_gagnees.exclude(
            date_fermeture_reelle__isnull=True
        ).exclude(
            date_creation__isnull=True
        )
        
        if opportunites_gagnees_avec_dates.exists():
            # Calculer le délai moyen en jours
            delais = []
            for opp in opportunites_gagnees_avec_dates:
                if opp.date_creation and opp.date_fermeture_reelle:
                    delai = (opp.date_fermeture_reelle - opp.date_creation.date()).days
                    delais.append(delai)
            
            if delais:
                context['delai_moyen_vente'] = sum(delais) / len(delais)
            else:
                context['delai_moyen_vente'] = 0
        else:
            context['delai_moyen_vente'] = 0
        
        # Performances par commercial
        performances_data = (
            Opportunite.objects.filter(
                entreprise=entreprise,
                statut__est_gagnant=True
            )
            .values('assigne_a')
            .annotate(
                count=Count('id'),
                total=Sum('montant_estime'),
                moyenne=Avg('montant_estime')
            )
            .order_by('-total')
        )
        
        # Enrichir les données avec les informations utilisateur
        context['performances_commerciaux'] = []
        for data in performances_data:
            if data['assigne_a']:
                try:
                    user = User.objects.get(id=data['assigne_a'])
                    context['performances_commerciaux'].append({
                        'utilisateur': user,
                        'count': data['count'],
                        'total': data['total'] or 0,
                        'moyenne': data['moyenne'] or 0
                    })
                except User.DoesNotExist:
                    continue
        
        # Statistiques par statut
        context['statistiques_par_statut'] = (
            Opportunite.objects.filter(entreprise=entreprise)
            .values('statut__nom', 'statut__couleur')
            .annotate(
                count=Count('id'),
                total=Sum('montant_estime'),
                moyenne=Avg('montant_estime')
            )
            .order_by('-total')
        )
        
        # Opportunités par mois (derniers 6 mois)
        maintenant = timezone.now()
        context['opportunites_par_mois'] = []
        
        for i in range(5, -1, -1):
            mois = maintenant.month - i
            annee = maintenant.year
            if mois <= 0:
                mois += 12
                annee -= 1
            
            count = Opportunite.objects.filter(
                entreprise=entreprise,
                date_creation__month=mois,
                date_creation__year=annee
            ).count()
            
            context['opportunites_par_mois'].append({
                'mois': f"{mois:02d}/{annee}",
                'count': count
            })
        
        return context
class GetOpportunitesParStatutView(EntrepriseAccessMixin, TemplateView):
    
    def get(self, request, *args, **kwargs):
        try:
            entreprise = request.user.entreprise
            
            # Récupérer les données de base
            data = list(
                Opportunite.objects.filter(entreprise=entreprise)
                .values('statut__nom', 'statut__couleur')
                .annotate(count=Count('id'), total=Sum('montant_estime'))
                .order_by('-total')
            )
            
            return JsonResponse(data, safe=False)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

class GetActivitesMensuellesView(EntrepriseAccessMixin, TemplateView):
    
    def get(self, request, *args, **kwargs):
        try:
            entreprise = request.user.entreprise
            now = timezone.now()
            data = []
            
            for i in range(5, -1, -1):
                month = now.month - i
                year = now.year
                if month <= 0:
                    month += 12
                    year -= 1
                
                count = Activite.objects.filter(
                    entreprise=entreprise,
                    date_debut__month=month,
                    date_debut__year=year
                ).count()
                
                data.append({
                    'month': f"{month:02d}/{year}",
                    'count': count
                })
            
            return JsonResponse(data, safe=False)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        
        
# crm/views.py

from django.contrib.auth.decorators import login_required

logger = logging.getLogger(__name__)

@login_required
def envoyer_message_clients(request):
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        sujet = request.POST.get('sujet', 'Message important de notre équipe')

        if not message:
            messages.error(request, "❌ Veuillez écrire un message avant d'envoyer.")
            return render(request, 'crm/envoyer_message_clients.html', {
                'sujet': sujet,
                'message': message,
            })

        # Récupérer l'entreprise de l'utilisateur connecté
        if not hasattr(request.user, 'entreprise'):
            messages.error(request, "❌ Votre utilisateur n'est lié à aucune entreprise.")
            return render(request, 'crm/envoyer_message_clients.html')

        entreprise = request.user.entreprise

        # Récupérer tous les clients actifs de cette entreprise avec email
        clients = Client.objects.filter(
            entreprise=entreprise,
            statut='ACT',
            email__isnull=False
        ).exclude(email='')

        count = 0
        for client in clients:
            try:
                send_mail(
                    sujet,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [client.email],
                    fail_silently=False,
                )
                count += 1
            except Exception as e:
                logger.error(f"Erreur envoi à {client.email}: {e}")
                continue  # On continue même si un email échoue

        messages.success(request, f"✅ Message envoyé à {count} clients sur {clients.count()}.")
        logger.info(f"{request.user} a envoyé un message à {count} clients de {entreprise.nom}")

        return HttpResponseRedirect(reverse('crm:envoyer_message_clients'))

    return render(request, 'crm/envoyer_message_clients.html', {
        'title': 'Envoyer un message à tous les clients',
    })