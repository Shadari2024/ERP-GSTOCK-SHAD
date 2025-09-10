from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    # Page d'accueil
    path('', views.AccueilCRMView.as_view(), name='acceuil'),
    
    # Clients
    path('clients/', views.ClientListView.as_view(), name='client_list'),
    path('clients/nouveau/', views.ClientCreateView.as_view(), name='client_create'),
    path('clients/<int:pk>/', views.ClientDetailView.as_view(), name='client_detail'),
    path('clients/<int:pk>/modifier/', views.ClientUpdateView.as_view(), name='client_update'),
    # Statuts d'opportunité
path('statuts-opportunite/', views.StatutOpportuniteListView.as_view(), name='statut_opportunite_list'),
path('statuts-opportunite/nouveau/', views.StatutOpportuniteCreateView.as_view(), name='statut_opportunite_create'),
path('statuts-opportunite/<int:pk>/modifier/', views.StatutOpportuniteUpdateView.as_view(), name='statut_opportunite_update'),
path('statuts-opportunite/<int:pk>/supprimer/', views.StatutOpportuniteDeleteView.as_view(), name='statut_opportunite_delete'),
    # Opportunités
    path('opportunites/', views.OpportuniteListView.as_view(), name='opportunite_list'),
    path('opportunites/nouvelle/', views.OpportuniteCreateView.as_view(), name='opportunite_create'),
    path('opportunites/<int:pk>/', views.OpportuniteDetailView.as_view(), name='opportunite_detail'),
    path('opportunites/<int:pk>/modifier/', views.OpportuniteUpdateView.as_view(), name='opportunite_update'),
    
    
    
    
    
    
   # Types d'activité
path('types-activite/', views.TypeActiviteListView.as_view(), name='type_activite_list'),
path('types-activite/nouveau/', views.TypeActiviteCreateView.as_view(), name='type_activite_create'),
path('types-activite/<int:pk>/modifier/', views.TypeActiviteUpdateView.as_view(), name='type_activite_update'),
path('types-activite/<int:pk>/supprimer/', views.TypeActiviteDeleteView.as_view(), name='type_activite_delete'), 
    
    # Activités
    path('activites/', views.ActiviteListView.as_view(), name='activite_list'),
    path('activites/nouvelle/', views.ActiviteCreateView.as_view(), name='activite_create'),
    path('activites/<int:pk>/modifier/', views.ActiviteUpdateView.as_view(), name='activite_update'),
    path('activites/<int:pk>/', views.ActiviteDetailView.as_view(), name='activite_detail'),
    path('activites/calendrier/', views.ActiviteCalendarView.as_view(), name='activite_calendar'),
    
    # Tableaux de bord et rapports
    path('tableau-de-bord/', views.TableauDeBordView.as_view(), name='tableau_de_bord'),
    path('performances/', views.PerformancesView.as_view(), name='performances'),
    
    # API endpoints
    path('api/opportunites-par-statut/', views.GetOpportunitesParStatutView.as_view(), name='api_opportunites_par_statut'),
    path('api/activites-mensuelles/', views.GetActivitesMensuellesView.as_view(), name='api_activites_mensuelles'),
]