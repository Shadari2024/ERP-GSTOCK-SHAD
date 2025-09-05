# parametres/urls.py
from django.urls import path
from .views import *

app_name = 'parametres'

urlpatterns = [

    path('entreprises/', EntrepriseListView.as_view(), name='entreprise_list'),
    path('entreprise/ajouter/', EntrepriseCreateView.as_view(), name='entreprise_create'),
    path('entreprise/<slug:slug>/', EntrepriseDetailView.as_view(), name='entreprise_detail'),
    path('entreprise/<slug:slug>/modifier/', EntrepriseUpdateView.as_view(), name='entreprise_update'),
    # Devises
# Devises
    path('devises/', DeviseListView.as_view(), name='devise_list'),
    path('devise/ajouter/', DeviseCreateView.as_view(), name='devise_create'),
    path('devise/<int:pk>/modifier/', DeviseUpdateView.as_view(), name='devise_update'),
    
    # Taux de change
    path('taux-change/', TauxChangeListView.as_view(), name='tauxchange_list'),
    path('taux-change/ajouter/', TauxChangeCreateView.as_view(), name='tauxchange_create'),
     path('taux-change/modifier/<int:pk>/',TauxChangeUpdateView.as_view(), name='tauxchange_update'),
    path('taux-change/supprimer/<int:pk>/',TauxChangeDeleteView.as_view(), name='tauxchange_delete'),
    
    path('convertir-devise/', convertir_devise, name='convertir_devise'),
    
    # Abonnements
    path('abonnements/', AbonnementListView.as_view(), name='abonnement_list'),
    path('abonnements/create/', AbonnementCreateView.as_view(), name='abonnement_create'),
      path('abonnements/<int:pk>/update/', 
         AbonnementUpdateView.as_view(), 
         name='abonnement_update'),
    path('abonnements/<pk>/detail/', AbonnementDetailView.as_view(), name='abonnement_detail'),
    path('abonnements/expirer/', AbonnementExpirerView.as_view(), name='abonnement_expirer'),
    path('entreprises/select/', EntrepriseSelectView.as_view(), name='entreprise_select'), # Nouvelle URL
    
    # API
    path('api/abonnements/verifier-date/', 
         verifier_date_abonnement, 
         name='verifier_date_abonnement'),
    
    path('abonnements/<int:pk>/delete/', 
         AbonnementDeleteView.as_view(), 
         name='abonnement_delete'),
     # Plans 
    path('plans/', PlanTarificationListView.as_view(), name='plantarification_list'),
    path('plan/ajouter/', PlanTarificationCreateView.as_view(), name='plantarification_create'),
    path('plan/<int:pk>/modifier/', PlanTarificationUpdateView.as_view(), name='plantarification_update'),
    path('plan/<int:pk>/supprimer/', PlanTarificationDeleteView.as_view(), name='plantarification_delete'),
    path('config_saas/', ConfigurationSAASUpdateView.as_view(), name='config_saas'),
    
    
    
    

        # URLs pour Module
    path('modules/', ModuleListView.as_view(), name='module_list'),
    path('modules/creer/', ModuleCreateView.as_view(), name='module_create'),
    path('modules/<int:pk>/', ModuleDetailView.as_view(), name='module_detail'),
    path('modules/<int:pk>/modifier/', ModuleUpdateView.as_view(), name='module_update'),
    path('modules/<int:pk>/supprimer/', ModuleDeleteView.as_view(), name='module_delete'),
    
    # URLs pour ModuleEntreprise
    path('modules/<int:module_pk>/entreprise/ajouter/', ModuleEntrepriseCreateView.as_view(), name='module_entreprise_create'),
    path('modules/entreprise/<int:pk>/modifier/', ModuleEntrepriseUpdateView.as_view(), name='module_entreprise_update'),
    
    # URLs pour DependanceModule
    path('modules/<int:module_pk>/dependance/ajouter/', DependanceModuleCreateView.as_view(), name='dependance_module_create'),
    path('modules/dependance/<int:pk>/supprimer/', DependanceModuleDeleteView.as_view(), name='dependance_module_delete'),
]