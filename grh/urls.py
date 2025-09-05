from django.urls import path
from . import views

app_name = "grh"

urlpatterns = [
    path('', views.GRHAccueilView.as_view(), name='grh'),
    # URLs pour les départements
    path('departements/', views.DepartementListView.as_view(), name='departement_list'),
    path('departements/ajouter/', views.DepartementCreateView.as_view(), name='departement_create'),
    path('departements/<int:pk>/modifier/', views.DepartementUpdateView.as_view(), name='departement_update'),
    path('departements/<int:pk>/supprimer/', views.DepartementDeleteView.as_view(), name='departement_delete'),
    
    # URLs pour les postes
    path('postes/', views.PosteListView.as_view(), name='poste_list'),
    path('postes/ajouter/', views.PosteCreateView.as_view(), name='poste_create'),
    path('postes/<int:pk>/modifier/', views.PosteUpdateView.as_view(), name='poste_update'),
    path('postes/<int:pk>/supprimer/', views.PosteDeleteView.as_view(), name='poste_delete'),
    
    # URLs pour les employés
    path('employes/', views.EmployeListView.as_view(), name='employe_list'),
    path('employes/ajouter/', views.EmployeCreateView.as_view(), name='employe_create'),
    path('employes/<int:pk>/', views.EmployeDetailView.as_view(), name='employe_detail'),
    path('employes/<int:pk>/modifier/', views.EmployeUpdateView.as_view(), name='employe_update'),
    path('employes/<int:pk>/supprimer/', views.EmployeDeleteView.as_view(), name='employe_delete'),
    path('employes/<int:pk>/generer-carte/', views.GenererCarteEmployeView.as_view(), name='generer_carte_employe'),
    path('employes/<int:pk>/telecharger-carte/', views.TelechargerCarteEmployeView.as_view(), name='telecharger_carte_employe'),
    path('employes/<int:pk>/apercu-carte/', views.ApercuCarteEmployeView.as_view(), name='apercu_carte_employe'),
    
    # URLs pour les contrats
    path('contrats/', views.ContratListView.as_view(), name='contrat_list'),
    path('contrats/ajouter/', views.CongeCreateView.as_view(), name='contrat_create'),
    path('contrats/<int:pk>/', views.ContratDetailView.as_view(), name='contrat_detail'),
    path('contrats/<int:pk>/modifier/', views.CongeUpdateView.as_view(), name='contrat_update'),
     
    path('paie/', views.BulletinPaieListView.as_view(), name='bulletin_list'),
    path('paie/ajouter/', views.BulletinPaieCreateView.as_view(), name='bulletin_create'),
    path('paie/<int:pk>/', views.BulletinPaieDetailView.as_view(), name='bulletin_detail'),
    path('paie/generer-auto/', views.GenererBulletinAutoView.as_view(), name='generer_bulletin_auto'),
    path('api/calculer-paie/', views.CalculerPaieAPIView.as_view(), name='api_calculer_paie'),
    path('paie/<int:pk>/telecharger/', views.DownloadBulletinPDFView.as_view(), name='bulletin_download'),
    path('paie/<int:pk>/regenerer-pdf/', views.GenerateBulletinPDFView.as_view(), name='bulletin_regenerate_pdf'),
    
    # URLs pour les congés
    path('conges/', views.CongeListView.as_view(), name='conge_list'),
    path('conges/ajouter/', views.CongeCreateView.as_view(), name='conge_create'),
    path('conges/<int:pk>/modifier/', views.CongeCreateView.as_view(), name='conge_update'),
     path('conges/<int:pk>/valider/<str:action>/', views.CongeValidationView.as_view(), name='conge_valider'),
     path('conges/<int:pk>/', views.CongeDetailView.as_view(), name='conge_detail'),
    # URLs pour les bulletins de paie
    # URLs pour la gestion des présences
path('presences/', views.PresenceListView.as_view(), name='presence_list'),
path('presences/ajouter/', views.PresenceCreateView.as_view(), name='presence_create'),  # Enlevé le point avant views
path('presences/<int:pk>/modifier/', views.PresenceUpdateView.as_view(), name='presence_update'),  # Enlevé le point
path('presences/<int:pk>/supprimer/', views.PresenceDeleteView.as_view(), name='presence_delete'),  # Enlevé le point
path('presences/importer/', views.ImportPresenceView.as_view(), name='presence_import'),  # Enlevé le point
path('presences/calendrier/', views.CalendrierPresenceView.as_view(), name='presence_calendrier'),  # Enlevé le point

# API endpoints - CORRECTION ICI
path('api/presences/data/', views.GetPresencesDataView.as_view(), name='api_presences_data'),  # Enlevé le point et supprimé la ligne dupliquée
path('api/calculer-paie/', views.CalculerPaieAPIView.as_view(), name='api_calculer_paie'),  # Enlevé le point
    
    
    
    
]