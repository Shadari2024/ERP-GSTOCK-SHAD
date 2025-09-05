from django.urls import path
from . views import *

app_name = 'ventes'

urlpatterns = [
    # # Clients
    # path('clients/', ClientListView.as_view(), name='client_list'),
    # path('clients/nouveau/', ClientCreateView.as_view(), name='client_create'),
    # path('clients/<int:pk>/modifier/', ClientUpdateView.as_view(), name='client_update'),
    # path('clients/<int:pk>/supprimer/', ClientDeleteView.as_view(), name='client_delete'),
    
    # Devis
    path('devis/', DevisListView.as_view(), name='devis_list'),
    path('devis/nouveau/', DevisCreateView.as_view(), name='devis_create'),
    path('devis/<int:pk>/', DevisDetailView.as_view(), name='devis_detail'),
    path('devis/<int:pk>/modifier/', DevisUpdateView.as_view(), name='devis_update'),
    path('devis/<int:pk>/supprimer/', DevisDeleteView.as_view(), name='devis_delete'),
      path('get_prix_produit/', GetPrixProduitView.as_view(), name='get_prix_produit'),
    path('devis/<int:pk>/imprimer/', DevisPrintView.as_view(), name='devis_print'), # <-- NOUVELLE LIGNE
     # URL pour le journal d'audit des devis
    path('devis/audit-logs/', DevisAuditLogListView.as_view(), name='devis_audit_logs'),
      path('devis/<int:pk>/accept/', DevisAcceptView.as_view(), name='devis_accept'),
    # Commandes
    path('commandes/', CommandeListView.as_view(), name='commande_list'),
    path('commandes/nouveau/', CommandeCreateView.as_view(), name='commande_create'),
    path('commandes/<int:pk>/', CommandeDetailView.as_view(), name='commande_detail'),
    path('commandes/<int:pk>/modifier/', CommandeUpdateView.as_view(), name='commande_update'),
    path('commandes/<int:pk>/supprimer/', CommandeDeleteView.as_view(), name='commande_delete'),
    path('commandes/<int:pk>/annuler/', CommandeCancelView.as_view(), name='commande_cancel'), # NEW
    path('commandes/audit-logs/', CommandeAuditLogListView.as_view(), name='commande_audit_logs'), # NEW
      path('commandes/<int:pk>/changer-statut/', CommandeStatutUpdateView.as_view(), name='commande_change_status'), # NEW URL
       path('commandes/<int:pk>/imprimer/',CommandePrintView.as_view(), name='commande_print'),
        path('commandes/<int:pk>/envoyer-email/', CommandeSendEmailView.as_view(), name='commande_send_email'),
        path('devis/<int:pk>/convertir-en-commande/', DevisConvertView.as_view(), name='devis_convert_to_commande'),
        # URL pour la requête AJAX de sélection du client
        path('api/client-info/<int:client_id>/',get_client_info, name='api_get_client_info'),
        # urls.py
  path('api/get_devis_lignes/<int:devis_id>/', get_devis_lignes, name='get_devis_lignes'),

     path('commandes/<int:pk>/convertir-bl/', CommandeConvertToBLView.as_view(), name='commande_convert_bl'),


    


    
    # Bons de livraison
    path('livraisons/', BonLivraisonListView.as_view(), name='livraison_list'),
    path('livraisons/nouveau/', BonLivraisonCreateView.as_view(), name='livraison_create'),
    path('livraisons/<int:pk>/', BonLivraisonDetailView.as_view(), name='livraison_detail'),
    path('livraisons/<int:pk>/modifier/', BonLivraisonUpdateView.as_view(), name='livraison_update'),
    path('livraisons/<int:pk>/supprimer/', BonLivraisonDeleteView.as_view(), name='livraison_delete'),
    path('livraisons/<int:pk>/changer-statut/', BonLivraisonChangeStatusView.as_view(), name='livraison_change_status'),
    path('livraisons/<int:pk>/imprimer/', BonLivraisonPrintView.as_view(), name='livraison_print'),
    path('livraisons/<int:pk>/envoyer-email/', BonLivraisonSendEmailView.as_view(), name='livraison_send_email'),
    path('livraisons/<int:pk>/annuler/', BonLivraisonCancelView.as_view(), name='livraison_cancel'),
       path('livraisons/<int:pk>/convertir-facture/', BonLivraisonConvertToFactureView.as_view(), name='livraison_convert_facture'),

    # Factures
    path('factures/', FactureListView.as_view(), name='facture_list'),
    path('factures/nouveau/', FactureCreateView.as_view(), name='facture_create'),
    path('factures/<int:pk>/', FactureDetailView.as_view(), name='facture_detail'),
    path('factures/<int:pk>/modifier/', FactureUpdateView.as_view(), name='facture_update'),
    path('factures/<int:pk>/supprimer/', FactureDeleteView.as_view(), name='facture_delete'),
     # Ajoutez cette ligne pour la vue d'impression
    path('factures/<int:pk>/imprimer/', FacturePrintView.as_view(), name='facture_print'),
    path('factures/<int:pk>/emeil/', FactureSendEmailView.as_view(), name='facture_send_email'),
     path('factures/<int:pk>/valider/',FactureValidateView.as_view(), name='facture_validate'),
    path('factures/<int:pk>/generer-ecriture/',FactureGenerateEcritureView.as_view(), name='facture_generate_ecriture'),
    
    
    # Paiements
    path('factures/<int:facture_pk>/paiement/ajouter/',PaiementCreateView.as_view(), name='paiement_create'),
    path('paiements/<int:pk>/supprimer/', PaiementDeleteView.as_view(), name='paiement_delete'),
    
    # Point de Vente
    path('pos/', PointDeVenteListView.as_view(), name='pos_list'),
    path('pos/nouveau/', PointDeVenteCreateView.as_view(), name='pos_create'),
    path('pos/<int:pk>/', POSDashboardView.as_view(), name='pos_dashboard'),
    path('pos/<int:pk>/modifier/', PointDeVenteUpdateView.as_view(), name='pos_update'),
    path('pos/<int:pk>/supprimer/', PointDeVenteDeleteView.as_view(), name='pos_delete'),
    path('api/caissier-info/', get_caissier_info, name='get_caissier_info'),
    path('pos/caissiers/',CaissierListView.as_view(), name='caissier_list'),
       # ... autres URLs ...
    path('caissier/dashboard/', CaissierDashboardView.as_view(), name='caissier_dashboard'),
  
    # Sessions POS
    
    path('pos/<int:pk>/ouvrir-session/', OuvrirSessionPOSView.as_view(), name='ouvrir_session_pos'),
    path('pos/<int:pk>/fermer-session/<int:session_pk>/', FermerSessionPOSView.as_view(), name='fermer_session_pos'),
    
     # Paiement et ticket
    path('vente/<int:vente_id>/paiement/', PaiementVenteView.as_view(), name='paiement_vente'),
       path('vente/<int:vente_id>/paiement/', PaiementVenteView.as_view(), 
         name='paiement_vente'),
    path('vente/<int:vente_id>/impression/', ImpressionTicketView.as_view(), 
         name='impression_ticket'),
    path('vente/<int:vente_id>/ticket-pdf/', GenererTicketPDFView.as_view(), 
         name='generer_ticket_pdf'),
    # Ventes POS
    path('pos/<int:pk>/session/<int:session_pk>/nouvelle-vente/', NouvelleVentePOSView.as_view(), name='nouvelle_vente_pos'),
     # URL simple pour commencer une nouvelle vente (gère la session automatiquement)
    path('pos/<int:pk>/nouvelle-vente/', NouvelleVenteSimpleView.as_view(), name='vente_create'),
    

    # Statistiques
    path('statistiques/ventes/', StatistiquesVentesView.as_view(), name='statistiques_ventes'),
    path('statistiques/facturation/', StatistiquesFacturationView.as_view(), name='statistiques_facturation'),
    
    # API
    path('api/search-article/', APISearchArticleView.as_view(), name='api_search_article'),
    path('api/client-info/', APIClientInfoView.as_view(), name='api_client_info'),


#  # Inventaire POS
#     path('pos/<int:pk>/inventaire/', InventairePOSView.as_view(),  name='inventaire_pos'),
#   path('pos/<int:pk>/inventaire/ajuster/<int:produit_id>/', AjusterStockPOSView.as_view(), name='ajuster_stock_pos'),
  
  
    path('pos/<int:pk>/rapports/', RapportsPOSView.as_view(), name='rapports_pos'),
    path('pos/<int:pk>/rapports/export/', ExportRapportPOSView.as_view(), name='export_rapports_pos'),
  
    # Historique POS
    path('pos/<int:pk>/historique/', HistoriquePOSView.as_view(), name='historique_pos'),
    path('pos/vente/<int:pk>/detail/', DetailVentePOSView.as_view(), name='detail_vente_pos'),
    
     # Écarts de caisse
    path('pos/<int:pk>/ecarts-caisse/', EcartsCaisseView.as_view(), name='ecarts_caisse'),
    path('pos/<int:pk>/session/<int:session_pk>/creer-ecart/', CreerEcartCaisseView.as_view(),  name='creer_ecart_caisse'),
    path('pos/<int:pk>/rapport-ecarts/', RapportEcartsCaisseView.as_view(), name='rapport_ecarts_caisse'),
     path('pos/session/<int:pk>/resume/', ResumeSessionView.as_view(), name='resume_session'),
  
]