from django.urls import path
from . import views

app_name = "comptabilite"

urlpatterns = [
    # Plan Comptable
    path('plan-comptable/', views.PlanComptableListView.as_view(), name='plan_comptable_list'),
    path('plan-comptable/ajouter/', views.PlanComptableCreateView.as_view(), name='plan_comptable_create'),
    path('plan-comptable/<int:pk>/modifier/', views.PlanComptableUpdateView.as_view(), name='plan_comptable_update'),
    path('plan-comptable/<int:pk>/', views.PlanComptableDetailView.as_view(), name='plan_comptable_detail'),
    path('plan-comptable/<int:pk>/supprimer/', views.PlanComptableDeleteView.as_view(), name='plan_comptable_delete'),
  # Journaux Comptables
path('journaux/', views.JournalComptableListView.as_view(), name='journal_list'),
path('journaux/ajouter/', views.JournalComptableCreateView.as_view(), name='journal_create'),
path('journaux/<int:pk>/modifier/', views.JournalComptableUpdateView.as_view(), name='journal_update'),
path('journaux/<int:pk>/supprimer/', views.JournalComptableDeleteView.as_view(), name='journal_delete'),
path('journaux/<int:pk>/', views.JournalComptableDetailView.as_view(), name='journal_detail'),
    # Écritures Comptables
    path('ecritures/', views.EcritureComptableListView.as_view(), name='ecriture_list'),
    path('ecritures/ajouter/', views.EcritureComptableCreateView.as_view(), name='ecriture_create'),
    path('ecritures/<int:pk>/', views.EcritureComptableDetailView.as_view(), name='ecriture_detail'),
        path('ecritures/<int:pk>/modifier/', views.EcritureComptableUpdateView.as_view(), name='ecriture_update'),
    path('ecritures/<int:pk>/supprimer/', views.EcritureComptableDeleteView.as_view(), name='ecriture_delete'),
   
    
    # Grand Livre
    path('grand-livre/', views.GrandLivreView.as_view(), name='grand_livre'),
    
    # Balance
    path('balance/', views.BalanceView.as_view(), name='balance'),
    
    # Comptes Auxiliaires
    path('comptes-auxiliaires/', views.CompteAuxiliaireListView.as_view(), name='compte_auxiliaire_list'),
    path('comptes-auxiliaires/ajouter/', views.CompteAuxiliaireCreateView.as_view(), name='compte_auxiliaire_create'),
    path('comptes-auxiliaires/<int:pk>/modifier/', views.CompteAuxiliaireUpdateView.as_view(), name='compte_auxiliaire_update'),
    path('comptes-auxiliaires/<int:pk>/supprimer/', views.CompteAuxiliaireDeleteView.as_view(), name='compte_auxiliaire_delete'),
    
    # États Financiers
    path('bilan/', views.BilanView.as_view(), name='bilan'),
    path('bilan/export-pdf/', views.BilanExportPDFView.as_view(), name='bilan-export-pdf'),
    path('bilan/export-excel/',views. BilanExportExcelView.as_view(), name='bilan-export-excel'),
    path('compte-resultat/', views.CompteResultatView.as_view(), name='compte_resultat'),
     path('Outils/', views.CalculatriceComptableView.as_view(), name='caluclatrice_comptable'),
]