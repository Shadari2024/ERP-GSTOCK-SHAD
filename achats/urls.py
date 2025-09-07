from django.urls import path
from .views import  *

app_name = 'achats'

urlpatterns = [
    # Commandes
    path('commandes/', ListeCommandesView.as_view(), name='liste_commandes'),
    path('commandes/creer/', CreerCommandeView.as_view(), name='creer_commande'),
    path('commandes/<int:pk>/', DetailCommandeView.as_view(), name='detail_commande'),
    path('commandes/<int:pk>/modifier/', ModifierCommandeView.as_view(), name='modifier_commande'),
   path('commandes/<int:pk>/valider/',ValiderCommandeView.as_view(), name='valider_commande'),
    path('', DashboardView.as_view(), name='dashboard'),
     # Exportation de toutes les commandes (filtrées)
    path('commandes/exporter/excel/',exporter_commandes_excel, name='exporter_commandes_excel_all'),
    # Exportation d'une commande spécifique par PK en Excel
    path('commandes/<int:pk>/exporter/excel/',exporter_commandes_excel, name='exporter_commande_excel'),
    # Exportation d'une commande spécifique par PK en PDF
    path('commandes/<int:pk>/exporter/pdf/',exporter_commande_pdf, name='exporter_commande_pdf'),
    # Fournisseurs
    path('fournisseurs/', ListeFournisseursView.as_view(), name='liste_fournisseurs'),
    path('fournisseurs/creer/', CreerFournisseurView.as_view(), name='creer_fournisseur'),
    path('fournisseurs/<int:pk>/', DetailFournisseurView.as_view(), name='detail_fournisseur'),
    path('fournisseurs/<int:pk>/modifier/', ModifierFournisseurView.as_view(), name='modifier_fournisseur'),
    path('fournisseurs/<int:pk>/supprimer/', SupprimerFournisseurView.as_view(), name='supprimer_fournisseur'),
    
    path('fournisseurs/importer/', ImporterFournisseursView.as_view(), name='importer_fournisseurs'),
    path('fournisseurs/exporter/excel/', exporter_fournisseurs_excel, name='exporter_fournisseurs_excel'),
    path('fournisseurs/exporter/pdf/', exporter_fournisseurs_pdf, name='exporter_fournisseurs_pdf'),

    # Bons de réception
    path('bons/', ListeBonsView.as_view(), name='liste_bons'),
    path('bons/creer/<int:commande_pk>/', CreerBonView.as_view(), name='creer_bon'),
    path('bons/<int:pk>/', DetailBonView.as_view(), name='detail_bon'),
    path('diagnostic/', diagnostic_comptabilite, name='diagnostic_comptabilite'),
    path('init-comptabilite/', init_comptabilite_manuelle, name='init_comptabilite'),
    path('commandes/<int:commande_pk>/bon/automatique/', 
         CreerBonAutomatique.as_view(), 
         name='creer_bon_automatique'),
      # URLs pour les factures
    path('factures/', FactureListView.as_view(), name='liste_factures'),
    path('factures/nouvelle/', FactureCreateView.as_view(), name='creer_facture'),
    path('factures/<int:pk>/', FactureDetailView.as_view(), name='detail_facture'),
    path('factures/<int:pk>/modifier/', FactureUpdateView.as_view(), name='modifier_facture'),
    
    # URLs pour les paiements
    path('factures/<int:facture_id>/paiement/nouveau/', PaiementCreateView.as_view(), name='creer_paiement'),
    path('paiements/<int:pk>/modifier/', PaiementUpdateView.as_view(), name='modifier_paiement'),
]