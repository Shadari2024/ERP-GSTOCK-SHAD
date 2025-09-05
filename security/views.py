# security/views.py

from django.utils.translation import gettext_lazy as _ # <--- Add this line!

from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.utils import timezone

# Assurez-vous d'importer vos formulaires et modèles
from .forms import UtilisateurForm
from .models import UtilisateurPersonnalise, ProfilUtilisateur
from .decorators import permission_requise # Exemple, ajustez le chemin

# ... (rest of your views.py content)

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views import View
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.utils import timezone
from security.models import UtilisateurPersonnalise as User
from .models import UtilisateurPersonnalise, ProfilUtilisateur, JournalActivite
from .forms import *
from .decorators import role_requis, permission_requise
from .utils import enregistrer_activite, get_client_ip
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib.auth.models import Group
from django.views.generic import ListView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.views import View
from django.urls import reverse
# security/views.py
from django.contrib.auth.models import Group, Permission
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count
from .forms import GroupAdminForm
# security/views.py
from django.contrib.auth.models import Group, Permission
from django.db.models import Count
from django.views.generic import TemplateView


class ConnexionView(View):
    template_name = 'security/login.html'
    form_class = ConnexionForm
    
    def get(self, request):
        # Vérifie si l'utilisateur est déjà connecté
        if request.user.is_authenticated:
            # Récupère le paramètre 'next' s'il existe
            next_url = request.GET.get('next') or None
            if next_url:
                return redirect(next_url)
            return redirect(self._get_redirect_url(request.user))
        return render(request, self.template_name, {'form': self.form_class()})
    
    def post(self, request):
        form = self.form_class(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            
            if user is not None and user.est_actif:
                login(request, user)
                enregistrer_activite(user, 'CONNEXION', f"Connexion réussie", get_client_ip(request))
                
                # Gestion de la redirection après connexion
                next_url = request.POST.get('next') or request.GET.get('next') or None
                if next_url:
                    return redirect(next_url)
                return redirect(self._get_redirect_url(user))
            else:
                messages.error(request, "Identifiants incorrects ou compte désactivé")
                enregistrer_activite(None, 'CONNEXION', f"Tentative de connexion échouée pour {username}", get_client_ip(request))
        
        return render(request, self.template_name, {
            'form': form,
            'next': request.GET.get('next', '')  # Passe le paramètre next au template
        })
    
    def _get_redirect_url(self, user):
        """Méthode interne pour déterminer la redirection"""
        # Utilise reverse() pour obtenir les URLs absolues
        if user.role == 'ADMIN':
            return reverse('security:admin_dashboard')
        elif user.role == 'security:MANAGER':
            return reverse('manager_dashboard')
        elif user.role == 'CAISSIER':
            return reverse('ventes:caissier_dashboard')
        elif user.role == 'STOCK':
            return reverse('security:stock_dashboard')
        return reverse('security:vendeur_dashboard')

def deconnexion(request):
    if request.user.is_authenticated:
        enregistrer_activite(request.user, 'DECONNEXION', "Déconnexion", get_client_ip(request))
    logout(request)
    return redirect('security:connexion')






from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View

def dashboard_redirect(request):
    """
    Redirige l'utilisateur vers le tableau de bord approprié selon son rôle.
    """
    if not request.user.is_authenticated:
        return redirect('security:connexion')
    
    if request.user.is_superuser or request.user.is_staff:
        return redirect('security:admin_dashboard')
    elif request.user.groups.filter(name='Manager').exists():
        return redirect('security:manager_dashboard')
    elif request.user.groups.filter(name='Caissier').exists():
        return redirect('security:caissier_dashboard')
    elif request.user.groups.filter(name='Vendeur').exists():
        return redirect('security:vendeur_dashboard')
    elif request.user.groups.filter(name='Stock').exists():
        return redirect('security:stock_dashboard')
    else:
        # Redirection par défaut
        return redirect('security:admin_dashboard')

# Version basée sur classe si vous préférez
class DashboardRedirectView(View):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get(self, request):
        if request.user.is_superuser or request.user.is_staff:
            return redirect('security:admin_dashboard')
        elif request.user.groups.filter(name='Manager').exists():
            return redirect('security:manager_dashboard')
        elif request.user.groups.filter(name='Caissier').exists():
            return redirect('security:caissier_dashboard')
        elif request.user.groups.filter(name='Vendeur').exists():
            return redirect('security:vendeur_dashboard')
        elif request.user.groups.filter(name='Stock').exists():
            return redirect('security:stock_dashboard')
        else:
            return redirect('security:admin_dashboard')








class AdminDashboardView(TemplateView):
    template_name = 'security/dashboard/admin.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Statistiques utilisateurs
        context['stats'] = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'total_groups': Group.objects.count(),
            'total_perms': Permission.objects.count()
        }
        
        # Derniers utilisateurs
        context['recent_users'] = User.objects.order_by('-date_joined')[:5]
        
        # Activités récentes
        context['recent_activities'] = JournalActivite.objects.order_by('-date_heure')[:10]
        
        # Statistiques groupes
        context['group_stats'] = Group.objects.annotate(
            user_count=Count('user')
        ).values('name', 'user_count')[:5]
        
        # Statistiques permissions
        context['perm_stats'] = Permission.objects.values(
            'content_type__app_label'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        return context
    
    def get_recent_activities(self):
        return JournalActivite.objects.all().order_by('-date_heure')[:10]

@method_decorator([login_required, role_requis(['MANAGER'])], name='dispatch')
class TableauDeBordManager(View):
    template_name = 'security/dashboard/manager.html'
    
    def get(self, request):
        return redirect('statistiques_produits')

@method_decorator([login_required, role_requis(['CAISSIER'])], name='dispatch')
class TableauDeBordCaissier(View):
    template_name = 'security/dashboard/caissier.html'
    
    def get(self, request):
        return render(request, self.template_name)
    
from django.shortcuts import render
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from ventes.models import Devis, Commande, Facture, SessionPOS, VentePOS, LigneVentePOS
from django.db.models import Count, Sum, Q, F, ExpressionWrapper, DecimalField
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from parametres.models import *
@method_decorator([login_required, role_requis(['VENDEUR', 'CAISSIER'])], name='dispatch')
class TableauDeBordVendeur(View):
    template_name = 'security/dashboard/vendeur.html'
    
    def get(self, request):
        user = request.user
        entreprise = user.entreprise
        
        # AJOUT DE LA LOGIQUE POUR RÉCUPÉRER LA DEVISE PRINCIPALE
        devise_principale_symbole = self.get_devise_principale(entreprise)
        
        # Statistiques des devis
        devis_stats = self.get_devis_stats(entreprise)
        
        # Statistiques des commandes
        commandes_stats = self.get_commandes_stats(entreprise)
        
        # Statistiques des factures
        factures_stats = self.get_factures_stats(entreprise)
        
        # Statistiques des ventes POS (si applicable)
        ventes_pos_stats = self.get_ventes_pos_stats(entreprise, user)
        
        # Derniers documents
        derniers_documents = self.get_derniers_documents(entreprise)
        
        # Alertes et notifications
        alertes = self.get_alertes(entreprise)
        
        context = {
            'devis_stats': devis_stats,
            'commandes_stats': commandes_stats,
            'factures_stats': factures_stats,
            'ventes_pos_stats': ventes_pos_stats,
            'derniers_documents': derniers_documents,
            'alertes': alertes,
            'devise_principale': devise_principale_symbole,  # AJOUT DANS LE CONTEXTE
        }
        
        return render(request, self.template_name, context)

    def get_devise_principale(self, entreprise):
        """Récupère le symbole de la devise principale de l'entreprise."""
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            return config_saas.devise_principale.symbole if config_saas.devise_principale else ''
        except ConfigurationSAAS.DoesNotExist:
            return '' # Ou une devise par défaut comme '€' ou '$'
    
    def get_devis_stats(self, entreprise):
        """Récupère les statistiques des devis"""
        aujourdhui = timezone.now().date()
        debut_mois = aujourdhui.replace(day=1)
        debut_semaine = aujourdhui - timedelta(days=aujourdhui.weekday())
        
        devis = Devis.objects.filter(entreprise=entreprise)
        
        return {
            'total': devis.count(),
            'brouillon': devis.filter(statut='brouillon').count(),
            'envoyes': devis.filter(statut='envoye').count(),
            'acceptes': devis.filter(statut='accepte').count(),
            'ce_mois': devis.filter(date__gte=debut_mois).count(),
            'cette_semaine': devis.filter(date__gte=debut_semaine).count(),
            'aujourdhui': devis.filter(date=aujourdhui).count(),
        }
    
    def get_commandes_stats(self, entreprise):
        """Récupère les statistiques des commandes"""
        aujourdhui = timezone.now().date()
        debut_mois = aujourdhui.replace(day=1)
        
        commandes = Commande.objects.filter(entreprise=entreprise)
        
        # Calcul du chiffre d'affaires avec les champs existants
        ca_mois = commandes.filter(
            date__gte=debut_mois, 
            statut__in=['Confirmee', 'expedie', 'livre']
        ).aggregate(total=Sum('total_ttc'))['total'] or Decimal('0.00')
        
        return {
            'total': commandes.count(),
            'brouillon': commandes.filter(statut='brouillon').count(),
            'confirmees': commandes.filter(statut='Confirmee').count(),
            'expediees': commandes.filter(statut='expedie').count(),
            'livrees': commandes.filter(statut='livre').count(),
            'ce_mois': commandes.filter(date__gte=debut_mois).count(),
            'chiffre_affaire_mois': ca_mois,
        }
    
    def get_factures_stats(self, entreprise):
        """Récupère les statistiques des factures"""
        aujourdhui = timezone.now().date()
        debut_mois = aujourdhui.replace(day=1)
        
        factures = Facture.objects.filter(entreprise=entreprise)
        
        return {
            'total': factures.count(),
            'brouillon': factures.filter(statut='brouillon').count(),
            'validees': factures.filter(statut='validee').count(),
            'payees': factures.filter(statut='paye').count(),
            'impayees': factures.filter(
                Q(statut='validee') | Q(statut='paye_partiel')
            ).count(),
            'montant_impaye': factures.filter(
                Q(statut='validee') | Q(statut='paye_partiel')
            ).aggregate(total=Sum('montant_restant'))['total'] or Decimal('0.00'),
            'chiffre_affaire_mois': factures.filter(
                date_facture__gte=debut_mois,
                statut__in=['validee', 'paye_partiel', 'paye']
            ).aggregate(total=Sum('total_ttc'))['total'] or Decimal('0.00'),
        }
    
    def get_ventes_pos_stats(self, entreprise, user):
        """Récupère les statistiques des ventes POS"""
        aujourdhui = timezone.now().date()
        
        # Vérifier si l'utilisateur a accès au POS
        sessions_actives = SessionPOS.objects.filter(
            point_de_vente__entreprise=entreprise,
            statut='ouverte',
            utilisateur=user
        )
        
        if not sessions_actives.exists():
            return None
        
        session_active = sessions_actives.first()
        ventes = VentePOS.objects.filter(session=session_active)
        ventes_aujourdhui = ventes.filter(date__date=aujourdhui)
        
        # Calcul manuel du chiffre d'affaires pour les ventes d'aujourd'hui
        ca_jour = Decimal('0.00')
        for vente in ventes_aujourdhui:
            ca_jour += vente.total_ttc  # Utilisation de la propriété
        
        # Calcul manuel du total des ventes de la session
        total_ventes_session = Decimal('0.00')
        for vente in ventes:
            total_ventes_session += vente.total_ttc  # Utilisation de la propriété
        
        return {
            'session_active': session_active,
            'ventes_aujourdhui': ventes_aujourdhui.count(),
            'chiffre_affaire_jour': ca_jour,
            'fonds_ouverture': session_active.fonds_ouverture,
            'total_ventes_session': total_ventes_session,
        }
    
    def get_derniers_documents(self, entreprise):
        """Récupère les derniers documents créés"""
        return {
            'devis': Devis.objects.filter(entreprise=entreprise)
                        .select_related('client')
                        .order_by('-created_at')[:5],
            'commandes': Commande.objects.filter(entreprise=entreprise)
                          .select_related('client')
                          .order_by('-created_at')[:5],
            'factures': Facture.objects.filter(entreprise=entreprise)
                         .select_related('client')
                         .order_by('-date_facture')[:5],
        }
    
    def get_alertes(self, entreprise):
        """Récupère les alertes importantes"""
        alertes = []
        
        # Devis en attente de suivi (envoyés il y a plus de 7 jours)
        devis_en_attente = Devis.objects.filter(
            entreprise=entreprise,
            statut='envoye',
            date__lte=timezone.now().date() - timedelta(days=7)
        ).count()
        
        if devis_en_attente > 0:
            alertes.append({
                'type': 'warning',
                'message': f'{devis_en_attente} devis envoyés nécessitent un suivi',
                'lien': '/ventes/devis/'  # Remplacez par votre URL réelle
            })
        
        # Commandes en retard de livraison
        commandes_retard = Commande.objects.filter(
            entreprise=entreprise,
            statut='Confirmee',
            created_at__lte=timezone.now() - timedelta(days=3)
        ).count()
        
        if commandes_retard > 0:
            alertes.append({
                'type': 'danger',
                'message': f'{commandes_retard} commandes en retard de traitement',
                'lien': '/ventes/commandes/'  # Remplacez par votre URL réelle
            })
        
        # Factures impayées
        factures_impayees = Facture.objects.filter(
            entreprise=entreprise,
            statut__in=['validee', 'paye_partiel'],
            date_echeance__lt=timezone.now().date()
        ).count()
        
        if factures_impayees > 0:
            alertes.append({
                'type': 'danger',
                'message': f'{factures_impayees} factures en retard de paiement',
                'lien': '/ventes/factures/'  # Remplacez par votre URL réelle
            })
        
        return alertes

@method_decorator([login_required, permission_requise('gerer_utilisateurs')], name='dispatch')
class ListeUtilisateurs(View):
    template_name = 'security/user/list.html'
    form_class = FiltreUtilisateurForm
    
    def get(self, request):
        form = self.form_class(request.GET or None)
        utilisateurs = UtilisateurPersonnalise.objects.all()
        
        if form.is_valid():
            # Filtrage par statut
            if form.cleaned_data['statut']:
                utilisateurs = utilisateurs.filter(is_active=form.cleaned_data['statut'] == 'actif')
            
            # Filtrage par rôle
            if form.cleaned_data['role']:
                utilisateurs = utilisateurs.filter(role=form.cleaned_data['role'])
            
            # Filtrage par date
            if form.cleaned_data['date_debut']:
                utilisateurs = utilisateurs.filter(date_joined__gte=form.cleaned_data['date_debut'])
            if form.cleaned_data['date_fin']:
                utilisateurs = utilisateurs.filter(date_joined__lte=form.cleaned_data['date_fin'])
            
            # Recherche textuelle
            if form.cleaned_data['recherche']:
                search_term = form.cleaned_data['recherche']
                utilisateurs = utilisateurs.filter(
                    Q(username__icontains=search_term) |
                    Q(first_name__icontains=search_term) |
                    Q(last_name__icontains=search_term) |
                    Q(email__icontains=search_term)
                )
        
        # Tri
        tri = request.GET.get('tri', '-date_joined')
        utilisateurs = utilisateurs.order_by(tri)
        
        context = {
            'utilisateurs': utilisateurs,
            'form': form,
            'role_choices': UtilisateurPersonnalise.ROLES,
            'tri_actuel': tri,
        }
        return render(request, self.template_name, context)

        
@method_decorator([login_required], name='dispatch')
class EditProfile(View):
    template_name = 'security/user/edit_profile.html'
    form_class = UtilisateurForm
    profil_form_class = ProfilForm

    def get(self, request):
        user = request.user
        return render(request, self.template_name, {
            'form': self.form_class(instance=user),
            'profil_form': self.profil_form_class(instance=user.profil)
        })


from django.views import View
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

@method_decorator(login_required, name='dispatch')
class UpdateProfilePhoto(View):
    def post(self, request):
        user = request.user
        if 'photo' in request.FILES:
            user.profil.photo = request.FILES['photo']
            user.profil.save()
            messages.success(request, "Photo de profil mise à jour avec succès")
        else:
            messages.error(request, "Aucune photo sélectionnée")
        return redirect('security:mon_profil')
    
    
    def post(self, request):
        user = request.user
        form = self.form_class(request.POST, instance=user)
        profil_form = self.profil_form_class(request.POST, request.FILES, instance=user.profil)

        if form.is_valid() and profil_form.is_valid():
            form.save()
            profil_form.save()
            messages.success(request, "Profil mis à jour avec succès")
            return redirect('security:mon_profil')

        return render(request, self.template_name, {
            'form': form,
            'profil_form': profil_form
        })       
@method_decorator([login_required, permission_requise('gerer_utilisateurs')], name='dispatch')
class EditerUtilisateur(View):
    template_name = 'security/user/edit.html'
    form_class = UtilisateurForm
    profil_form_class = ProfilForm
    
    def get(self, request, pk):
        utilisateur = get_object_or_404(UtilisateurPersonnalise, pk=pk)
        form = self.form_class(instance=utilisateur)
        profil_form = self.profil_form_class(instance=utilisateur.profil)
        
        return render(request, self.template_name, {
            'form': form,
            'profil_form': profil_form,
            'utilisateur': utilisateur
        })
    
    def post(self, request, pk):
        utilisateur = get_object_or_404(UtilisateurPersonnalise, pk=pk)
        form = self.form_class(request.POST, instance=utilisateur)
        profil_form = self.profil_form_class(
            request.POST, 
            request.FILES, 
            instance=utilisateur.profil
        )
        
        if form.is_valid() and profil_form.is_valid():
            user = form.save()
            profil_form.save()
            
            enregistrer_activite(
                request.user, 
                'MODIFICATION', 
                f"Modification de l'utilisateur {user.username}", 
                get_client_ip(request)
            )
            messages.success(request, "Utilisateur mis à jour avec succès")
            return redirect('security:liste_utilisateurs')
        
        return render(request, self.template_name, {
            'form': form,
            'profil_form': profil_form,
            'utilisateur': utilisateur
        })
        
        
@method_decorator([login_required, permission_requise('gerer_utilisateurs')], name='dispatch')
class SupprimerUtilisateur(View):
    def post(self, request, pk):
        utilisateur = get_object_or_404(UtilisateurPersonnalise, pk=pk)
        username = utilisateur.username
        
        # Empêcher l'auto-suppression
        if request.user.pk == utilisateur.pk:
            messages.error(request, "Vous ne pouvez pas supprimer votre propre compte")
            return redirect('security:liste_utilisateurs')
        
        utilisateur.delete()
        
        enregistrer_activite(
            request.user,
            'SUPPRESSION',
            f"Suppression de l'utilisateur {username}",
            get_client_ip(request)
        )
        messages.success(request, f"Utilisateur {username} supprimé avec succès")
        return redirect('security:liste_utilisateurs')
    
class ChangementMdpView(PasswordChangeView):
    template_name = 'security/changement_mdp.html'
    success_url = reverse_lazy('security:mon_profil')

from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .forms import UtilisateurForm, ProfilForm
from .models import ProfilUtilisateur

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.utils import timezone
from .forms import UtilisateurForm, ProfilForm
from .models import ProfilUtilisateur


@method_decorator([login_required], name='dispatch')
class MonProfil(View):
    template_name = 'security/user/profile.html'

    def get(self, request):
        user = request.user
        profil, _ = ProfilUtilisateur.objects.get_or_create(utilisateur=user)
        
        return render(request, self.template_name, {
            'form': UtilisateurForm(instance=user),
            'profil_form': ProfilForm(instance=profil),
            'password_form': PasswordChangeForm(user),
            'profil': profil,
            'user': user
        })

    def post(self, request):
        user = request.user
        profil, _ = ProfilUtilisateur.objects.get_or_create(utilisateur=user)
        action = request.POST.get('action')

        if action == 'update_info':
            form = UtilisateurForm(request.POST, instance=user)
            profil_form = ProfilForm(request.POST, request.FILES, instance=profil)

            if form.is_valid() and profil_form.is_valid():
                form.save()
                profil = profil_form.save(commit=False)

                if request.POST.get('signature_data'):
                    profil.signature_svg = request.POST['signature_data']
                    profil.signature_date = timezone.now()

                profil.save()
                messages.success(request, "Profil mis à jour avec succès")
            else:
                messages.error(request, "Erreur lors de la mise à jour")

        elif action == 'change_password':
            password_form = PasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Mot de passe mis à jour avec succès")
            else:
                messages.error(request, "Erreur lors du changement de mot de passe")

        elif action == 'update_photo':
            if 'photo' in request.FILES:
                profil.photo = request.FILES['photo']
                profil.save()
                messages.success(request, "Photo de profil mise à jour avec succès")
            else:
                messages.error(request, "Aucune photo sélectionnée")

        return redirect('security:mon_profil')


    
    
@method_decorator([login_required, role_requis(['STOCK'])], name='dispatch')
class TableauDeBordStock(View):
    template_name = 'security/dashboard/stock.html'
    
    def get(self, request):
        return render(request, self.template_name)
    
    
    

@login_required
def dashboard_redirect(request):
    """Redirige vers le dashboard approprié selon le rôle"""
    if not request.user.is_authenticated:
        return redirect('security:connexion')
    
    # Vérifiez d'abord si une redirection 'next' est spécifiée
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    
    # Redirection selon le rôle - utilisez les noms d'URL de votre application
    if request.user.role == 'ADMIN':
        return redirect('security:admin_dashboard')  # Utilisez le bon nom d'URL
    elif request.user.role == 'MANAGER':
        return redirect('security:manager_dashboard')
    elif request.user.role == 'CAISSIER':
        return redirect('security:caissier_dashboard')
    elif request.user.role == 'STOCK':
        return redirect('security:stock_dashboard')
    return redirect('security:vendeur_dashboard')  # Redirection par défaut
    
    
@method_decorator([login_required, permission_requise('voir_statistiques')], name='dispatch')
class JournalActiviteView(View):
    template_name = 'security/journal_activite.html'
    paginate_by = 20
    permission_required = 'voir_statistiques'
    
    def get(self, request):
        # Récupérer les paramètres
        params = {
            'utilisateur': request.GET.get('utilisateur'),
            'action': request.GET.get('action'),
            'date_debut': request.GET.get('date_debut'),
            'date_fin': request.GET.get('date_fin'),
            'recherche': request.GET.get('recherche', '').strip(),
        }

        # Requête de base
        activites = JournalActivite.objects.select_related('utilisateur').order_by('-date_heure')

        # Filtres
        if params['utilisateur']:
            activites = activites.filter(utilisateur_id=params['utilisateur'])
        if params['action']:
            activites = activites.filter(action=params['action'])
        if params['date_debut']:
            activites = activites.filter(date_heure__gte=params['date_debut'])
        if params['date_fin']:
            activites = activites.filter(date_heure__lte=params['date_fin'])

        # Recherche avancée
        if params['recherche']:
            search_term = params['recherche']
            activites = activites.filter(
                Q(details__icontains=search_term) |
                Q(utilisateur__username__icontains=search_term) |
                Q(utilisateur__email__icontains=search_term) |
                Q(action__icontains=search_term) |
                Q(ip_address__icontains=search_term)
            )

        # Liste des utilisateurs actifs pour le filtre
        utilisateurs_distincts = UtilisateurPersonnalise.objects.filter(
            id__in=JournalActivite.objects.values('utilisateur').distinct()
        ).order_by('username')

        # Utilisateur sélectionné pour l'affichage
        utilisateur_filtre = None
        if params['utilisateur']:
            try:
                utilisateur_filtre = UtilisateurPersonnalise.objects.get(id=params['utilisateur'])
            except UtilisateurPersonnalise.DoesNotExist:
                utilisateur_filtre = None

        # Pagination
        paginator = Paginator(activites, self.paginate_by)
        page = request.GET.get('page', 1)
        try:
            activites_page = paginator.page(page)
        except PageNotAnInteger:
            activites_page = paginator.page(1)
        except EmptyPage:
            activites_page = paginator.page(paginator.num_pages)

        context = {
            'activites': activites_page,
            'utilisateurs': utilisateurs_distincts,
            'action_types': JournalActivite.ACTION_TYPES,
            'filters': params,
            'is_filtered': any(params.values()),
            'search_params': self._build_search_params(params),
            'filtre_utilisateur_obj': utilisateur_filtre,
        }
        return render(request, self.template_name, context)

    def _build_search_params(self, params):
        """Construit la chaîne de paramètres de recherche pour la pagination."""
        return '&'.join(
            f"{key}={value}"
            for key, value in params.items()
            if value
        )
        
        
        
        
from django.shortcuts import render

def acces_refuse_view(request):
    return render(request, 'security/acces_refuse.html', {})        
        
        
class GroupListView(PermissionRequiredMixin, ListView):
    permission_required = 'auth.view_group'
    model = Group
    template_name = 'security/group/list.html'
    context_object_name = 'groups'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Group.objects.annotate(user_count=Count('user')).order_by('name')
        
        # Récupération des paramètres de recherche
        name = self.request.GET.get('name')
        permission = self.request.GET.get('permission')
        min_users = self.request.GET.get('min_users')
        
        # Filtrage par nom
        if name:
            queryset = queryset.filter(name__icontains=name)
        
        # Filtrage par permission
        if permission:
            queryset = queryset.filter(permissions__id=permission)
        
        # Filtrage par nombre minimum d'utilisateurs
        if min_users:
            queryset = queryset.filter(user_count__gte=min_users)
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ajout des permissions pour le filtre
        context['all_permissions'] = Permission.objects.all().order_by('name')
        
        # Ajout de la permission sélectionnée si elle existe
        permission_id = self.request.GET.get('permission')
        if permission_id:
            try:
                context['selected_permission'] = Permission.objects.get(id=permission_id)
            except Permission.DoesNotExist:
                pass
        
        # Indicateur de filtrage actif
        context['is_filtered'] = any([
            self.request.GET.get('name'),
            self.request.GET.get('permission'),
            self.request.GET.get('min_users')
        ])
        
        # Conservation des paramètres de recherche pour la pagination
        context['search_params'] = self._get_search_params()
        
        return context
    
    def _get_search_params(self):
        """Retourne les paramètres de recherche sous forme de chaîne de requête"""
        params = []
        for param in ['name', 'permission', 'min_users']:
            value = self.request.GET.get(param)
            if value:
                params.append(f"{param}={value}")
        return '&'.join(params) if params else ''

class GroupCreateView(PermissionRequiredMixin, CreateView):
    permission_required = 'auth.add_group'
    model = Group
    form_class = GroupAdminForm
    template_name = 'security/group/form.html'
    success_url = reverse_lazy('security:liste_groupes')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Group created successfully")
        return response

class GroupUpdateView(PermissionRequiredMixin, UpdateView):
    permission_required = 'auth.change_group'
    model = Group
    form_class = GroupAdminForm
    template_name = 'security/group/form.html'
    success_url = reverse_lazy('security:liste_groupes')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Group updated successfully")
        return response

class GroupDeleteView(PermissionRequiredMixin, DeleteView):
    permission_required = 'auth.delete_group'
    model = Group
    template_name = 'security/group/confirm_delete.html'
    success_url = reverse_lazy('security:liste_groupes')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Group deleted successfully")
        return super().delete(request, *args, **kwargs)
    
    
    
    

class ListePermissionsView(PermissionRequiredMixin, ListView):
    permission_required = 'auth.view_permission'
    model = Permission
    template_name = 'security/permission/liste.html'
    context_object_name = 'permissions'
    paginate_by = 25

    def get_queryset(self):
        queryset = Permission.objects.select_related('content_type').order_by('content_type__app_label', 'codename')
        
        # Récupération des paramètres de recherche
        search_term = self.request.GET.get('q')
        app_label = self.request.GET.get('app_label')
        model_name = self.request.GET.get('model_name')
        
        # Filtrage par terme de recherche
        if search_term:
            queryset = queryset.filter(
                Q(codename__icontains=search_term) |
                Q(name__icontains=search_term) |
                Q(content_type__app_label__icontains=search_term) |
                Q(content_type__model__icontains=search_term)
            )
        
        # Filtrage par application
        if app_label:
            queryset = queryset.filter(content_type__app_label__iexact=app_label)
        
        # Filtrage par modèle
        if model_name:
            queryset = queryset.filter(content_type__model__iexact=model_name)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Suggestions d'applications pour le filtre
        context['app_suggestions'] = Permission.objects.values_list(
            'content_type__app_label', flat=True
        ).distinct().order_by('content_type__app_label')
        
        # Suggestions de modèles pour le filtre
        context['model_suggestions'] = Permission.objects.values_list(
            'content_type__model', flat=True
        ).distinct().order_by('content_type__model')
        
        # Mots-clés populaires pour la recherche
        context['popular_keywords'] = self._get_popular_keywords()
        
        # Paramètres de recherche actuels
        context['current_search'] = {
            'q': self.request.GET.get('q', ''),
            'app_label': self.request.GET.get('app_label', ''),
            'model_name': self.request.GET.get('model_name', ''),
        }
        
        return context

    def _get_popular_keywords(self):
        """Retourne une liste de mots-clés populaires pour les suggestions"""
        from collections import Counter
        names = Permission.objects.values_list('name', flat=True)
        words = []
        
        for name in names:
            words.extend(name.split())
        
        return [word for word, count in Counter(words).most_common(10) if len(word) > 3]
    

from django.contrib.auth.decorators import permission_required


@permission_required('auth.change_permission')
def affecter_permissions(request):
    # Traitement du formulaire
    if request.method == 'POST':
        groupe_id = request.POST.get('groupe')
        permission_ids = request.POST.getlist('permissions')
        
        try:
            groupe = Group.objects.get(id=groupe_id)
            permissions = Permission.objects.filter(id__in=permission_ids)
            groupe.permissions.set(permissions)
            messages.success(request, f"Permissions mises à jour pour le groupe {groupe.name}")
            return redirect('security:affecter_permissions')
        except Group.DoesNotExist:
            messages.error(request, "Groupe introuvable")
    
    # Récupération des paramètres de recherche
    search_term = request.GET.get('q', '')
    app_filter = request.GET.get('app', '')
    groupe_filter = request.GET.get('groupe_filter', '')
    
    # Récupération des données pour le formulaire
    groupes = Group.objects.all().order_by('name')
    permissions = Permission.objects.select_related('content_type').order_by('content_type__app_label', 'codename')
    
    # Filtrage des permissions
    if search_term:
        permissions = permissions.filter(
            Q(codename__icontains=search_term) |
            Q(name__icontains=search_term) |
            Q(content_type__app_label__icontains=search_term) |
            Q(content_type__model__icontains=search_term))
    
    if app_filter:
        permissions = permissions.filter(content_type__app_label=app_filter)
    
    # Préparation des données pour le template
    permissions_par_app = {}
    selected_groupe = None
    permissions_groupe = []
    
    if groupe_filter:
        try:
            selected_groupe = Group.objects.get(id=groupe_filter)
            permissions_groupe = selected_groupe.permissions.values_list('id', flat=True)
        except Group.DoesNotExist:
            pass
    
    # Organisation des permissions par application
    app_labels = permissions.values_list('content_type__app_label', flat=True).distinct()
    
    for app_label in app_labels:
        app_perms = permissions.filter(content_type__app_label=app_label)
        permissions_par_app[app_label] = {
            'permissions': app_perms,
            'app_label': app_label,
            'model_names': app_perms.values_list('content_type__model', flat=True).distinct()
        }
    
    context = {
        'groupes': groupes,
        'permissions_par_app': permissions_par_app,
        'app_suggestions': Permission.objects.values_list(
            'content_type__app_label', flat=True).distinct().order_by('content_type__app_label'),
        'current_search': {
            'q': search_term,
            'app': app_filter,
            'groupe_filter': groupe_filter,
        },
        'selected_groupe_id': request.POST.get('groupe', '') or groupe_filter,
        'selected_groupe': selected_groupe,  # Ajout de l'objet groupe sélectionné
        'permissions_groupe': permissions_groupe,
    }
    
    return render(request, 'security/permission/affecter.html', context)
    
from django.http import JsonResponse

def get_group_permissions(request, group_id):
    try:
        group = Group.objects.get(id=group_id)
        permissions = list(group.permissions.values_list('id', flat=True))
        return JsonResponse({'permissions': permissions})
    except Group.DoesNotExist:
        return JsonResponse({'error': 'Groupe introuvable'}, status=404)
    
    
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .decorators import permission_requise
from .forms import UtilisateurForm, ProfilForm
from .models import UtilisateurPersonnalise, ProfilUtilisateur

class CreerUtilisateur(LoginRequiredMixin, View):
    @method_decorator([login_required, permission_requise('gerer_utilisateurs')], name='dispatch')
    def get(self, request):
        return render(request, 'security/user/create.html', {
            'form': UtilisateurForm(),
            'profil_form': ProfilForm()
        })

    def post(self, request):
        form = UtilisateurForm(request.POST)
        profil_form = ProfilForm(request.POST, request.FILES)

        if form.is_valid() and profil_form.is_valid():
            # user = form.save() <-- Ne pas sauvegarder directement ici si vous voulez modifier l'instance avant
            
            # Récupérer l'instance de l'utilisateur sans la sauvegarder immédiatement
            user = form.save(commit=False)

            # L'entreprise est maintenant gérée par le formulaire UtilisateurForm.
            # La valeur sera déjà sur user.entreprise grâce à form.save(commit=False).
            # Il n'y a donc rien de spécial à faire ici si le champ est sur le formulaire UtilisateurForm.
            # user.entreprise = form.cleaned_data.get('entreprise') # Cette ligne n'est plus nécessaire

            # Sauvegarder l'utilisateur après que l'entreprise soit définie (si non définie par le form.save)
            user.save() # Sauvegarde l'utilisateur avec l'entreprise sélectionnée

            # Sauvegarde du profil
            profil = profil_form.save(commit=False)
            profil.utilisateur = user
            profil.poste = user.get_role_display()

            # Récupération de la signature SVG si présente
            if request.POST.get('signature_data'):
                profil.signature_svg = request.POST['signature_data']
                profil.signature_date = timezone.now()

            profil.save() # Sauvegarde le profil

            messages.success(request, _("L'utilisateur a été créé avec succès."))
            return redirect('security:liste_utilisateurs')

        # Gestion des erreurs (inchangée)
        for f, errors in list(form.errors.items()) + list(profil_form.errors.items()):
            for error in errors:
                messages.error(request, _(f"Erreur dans le champ '{f}': {error}"))

        return render(request, 'security/user/create.html', {
            'form': form,
            'profil_form': profil_form
        })
        
class EditerUtilisateur(LoginRequiredMixin, View):
    @method_decorator([login_required, permission_requise('gerer_utilisateurs')], name='dispatch')
    def get(self, request, pk):
        utilisateur = get_object_or_404(UtilisateurPersonnalise, pk=pk)
        profil, _ = ProfilUtilisateur.objects.get_or_create(
            utilisateur=utilisateur,
            defaults={'poste': utilisateur.get_role_display()}
        )

        return render(request, 'security/user/edit.html', {
            'form': UtilisateurForm(instance=utilisateur), # Le formulaire se remplit automatiquement avec l'entreprise existante
            'profil_form': ProfilForm(instance=profil),
            'utilisateur': utilisateur,
            'profil': profil
        })

    def post(self, request, pk):
        utilisateur = get_object_or_404(UtilisateurPersonnalise, pk=pk)
        profil = get_object_or_404(ProfilUtilisateur, utilisateur=utilisateur)

        form = UtilisateurForm(request.POST, instance=utilisateur)
        profil_form = ProfilForm(request.POST, request.FILES, instance=profil)

        if form.is_valid() and profil_form.is_valid():
            # user = form.save() <-- Pas de commit=False ici car nous n'avons pas de modification complexe avant save
            # L'entreprise est mise à jour automatiquement par form.save() si elle a été changée dans le formulaire.
            user = form.save() 

            # Récupération de la nouvelle signature SVG si fournie
            if request.POST.get('signature_data'):
                profil.signature_svg = request.POST['signature_data']
                profil.signature_date = timezone.now()

            # Mettre à jour le poste si le rôle a changé
            if 'role' in form.changed_data:
                profil.poste = user.get_role_display()

            profil.save() # Sauvegarde le profil

            messages.success(request, _("L'utilisateur a été mis à jour avec succès."))
            return redirect('security:liste_utilisateurs')

        # Gestion des erreurs (inchangée)
        for f, errors in list(form.errors.items()) + list(profil_form.errors.items()):
            for error in errors:
                messages.error(request, _(f"Erreur dans le champ '{f}': {error}"))

        return render(request, 'security/user/edit.html', {
            'form': form,
            'profil_form': profil_form,
            'utilisateur': utilisateur,
            'profil': profil
        })
from django.contrib.auth.models import Group
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, permission_required

@method_decorator([login_required, permission_required('auth.change_user')], name='dispatch')
class GestionUtilisateur(View):
    template_name = 'security/user/manage.html'

    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        groupes = Group.objects.all()
        return render(request, self.template_name, {
            'user': user,
            'groupes': groupes,
            'user_groupes': user.groups.all()
        })

    def post(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        action = request.POST.get('action')

        if action == 'changer_groupes':
            # Gestion des groupes
            groupes_ids = request.POST.getlist('groupes')
            user.groups.clear()
            for groupe_id in groupes_ids:
                groupe = Group.objects.get(pk=groupe_id)
                user.groups.add(groupe)
            messages.success(request, "Groupes mis à jour avec succès")

        elif action == 'toggle_activation':
            # Activation/désactivation
            user.is_active = not user.is_active
            user.save()
            status = "activé" if user.is_active else "désactivé"
            messages.success(request, f"Utilisateur {status} avec succès")

        return redirect('security:gestion_utilisateur', user_id=user_id)
    
    
    
    
    
def acces_refuse(request):
    """Vue pour la page d'accès refusé"""
    return render(request, 'security/acces_refuse.html')
    
    
from .forms import SignatureForm

# views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import SignatureForm

@login_required
def manage_signature(request):
    try:
        profile = request.user.profil
    except ProfilUtilisateur.DoesNotExist:
        profile = ProfilUtilisateur.objects.create(utilisateur=request.user)
    
    if request.method == 'POST':
        form = SignatureForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Signature mise à jour avec succès!")
            return redirect('security:user_profile')
    else:
        form = SignatureForm(instance=profile)
    
    return render(request, 'accounts/manage_signature.html', {
        'form': form,
        'signature_url': profile.signature.url if profile.signature else None,
    })
    
    
@login_required
def user_profile(request):
    try:
        profile = request.user.profil
    except ProfilUtilisateur.DoesNotExist:
        profile = ProfilUtilisateur.objects.create(utilisateur=request.user)
    
    return render(request, 'accounts/user_profile.html', {
        'profile': profile,
        'user': request.user,
    })

    
    