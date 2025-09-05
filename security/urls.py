from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import *

app_name = 'security'

urlpatterns = [
    # Authentification
    path('connexion/', ConnexionView.as_view(), name='connexion'),
    path('deconnexion/', deconnexion, name='deconnexion'),
    
    # Tableaux de bord par rôle
   path('admin/dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('manager/', TableauDeBordManager.as_view(), name='manager_dashboard'),
    path('caissier/', TableauDeBordCaissier.as_view(), name='caissier_dashboard'),
    path('vendeur/', TableauDeBordVendeur.as_view(), name='vendeur_dashboard'),
    path('stock/', TableauDeBordStock.as_view(), name='stock_dashboard'),
    path("acces-refuse/", acces_refuse, name="acces_refuse"),
    # Gestion des utilisateurs
    path('utilisateurs/', ListeUtilisateurs.as_view(), name='liste_utilisateurs'),
    path('utilisateurs/creer/', CreerUtilisateur.as_view(), name='creer_utilisateur'),
    path('utilisateurs/<int:pk>/editer/', EditerUtilisateur.as_view(), name='editer_utilisateur'),
    path('utilisateurs/<int:pk>/supprimer/', SupprimerUtilisateur.as_view(), name='supprimer_utilisateur'),
    path('utilisateurs/<int:user_id>/gestion/',GestionUtilisateur.as_view(), name='gestion_utilisateur'),
    path('profil/', MonProfil.as_view(), name='mon_profil'),
    path('profil/editer/', EditProfile.as_view(), name='edit_profile'),
    path('profil/photo/',UpdateProfilePhoto.as_view(), name='update_profile_photo'),

    
    # Journal d'activité
    path('journal/', JournalActiviteView.as_view(), name='journal_activite'),
    path('changement-mdp/', ChangementMdpView.as_view(), name='changement_mdp'),
     path('dashboard/', dashboard_redirect, name='dashboard_redirect'),
     
   # Group management
    path('groups/', GroupListView.as_view(), name='liste_groupes'),
    path('groups/new/', GroupCreateView.as_view(), name='creer_groupe'),
    path('groups/<int:pk>/edit/', GroupUpdateView.as_view(), name='group_update'),
    path('groups/<int:pk>/delete/', GroupDeleteView.as_view(), name='group_delete'),
    path('permissions/', ListePermissionsView.as_view(), name='liste_permissions'),
    path('permissions/affecter/', affecter_permissions, name='affecter_permissions'),
    path('api/groupes/<int:group_id>/permissions/', get_group_permissions, name='api_group_permissions'),
    path('profile/',user_profile, name='user_profile'),
    path('profile/signature/',manage_signature, name='manage_signature'),
    
]