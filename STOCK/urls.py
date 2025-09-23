
from django.urls import path
from.views import *
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('client/',ClientListView.as_view(), name="liste_client"),
    path('client/ajout',FormulaireViewClient.as_view(), name="ajoute_client"),
    path('client/details/<int:my_id>',Detailsclient.as_view(), name="details_client"),
    path('client/<int:pk>/supprimer/', ClientDeleteView.as_view(), name='sup_client'),
    path('client/modif/<int:client_id>/', ModifClient.as_view(), name='modif_client'),
    path('cat/',CatView.as_view(), name="liste_cat"),
    path('cat/form',FormulaireCat.as_view(), name="ajoute_cat"),
    path('categories/modifier/<int:pk>/', UpdateCatView.as_view(), name='modifier_cat'),
    path('categories/supprimer/<int:pk>/', DeleteCatView.as_view(), name='supprimer_cat'),
    path('produit/ajouter/', AjouterProduitView.as_view(), name='ajouter_produit'),
    # path('produits/', / ` produits_view, name='produits_par_categorie'),
    path('produits/', produits_list, name='produits_par_categorie'),
 path('produits/tickets/imprimer-stock/', imprimer_tickets_en_stock_pdf, name='imprimer_tickets_en_stock'),
    # ,
    path('produits/search/', produits_search, name='produits_search'),
  path('supprimer/<int:pk>/', DeleteProduitView.as_view(), name='supprimer_produit'),
    path('produits/etiquette_produit/<int:pk>/', ticket_produit_pdf, name='etiquette_produit'),
path('produit/<int:pk>/suppression-bloquee/', DeleteProduitView.as_view(), name='produit_delete_blocked'),
    
      # --- Nouvelles URLs pour les dettes ---

    path('ventes-du-jour/', ventes_du_jour, name='ventes_du_jour'),
    path('ticket/<int:commande_id>/',ticket_pdf, name='ticket_pdf'),
    path('commande/<int:commande_id>/pdf/',bon_commande_pdf, name='bon_commande_pdf'),
    path('api/produit/', chercher_produit_par_code_barres, name='api_produit_par_code'),
    path('historique-ventes/',historique_ventes, name='historique_ventes'),
    path('statistiques/', statistiques, name='statistiquesVente'),
  
    

    path('parametres/', modifier_parametres, name='modifier_parametres'),
    path("parametres/", afficher_parametres, name="afficher_parametres"),

    path('', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    # path('logout/', logout_view, name='logout'),

    path('statistiques/produits/',tableau_de_bord, name='statistiques_produits'),

    path('stats/commandes/', commande_stats, name='commande_stats'),
    path('inventaitre/', inventaire, name='inventaitre_liste'),
    path('inventaire/etat-stock/', etat_stock, name='etat_stock'),
    path('inventaire/exporter-stock/',exporter_stock, name='exporter_stock'),
    path('stock/ajout/',ajouter_mouvement_stock, name='ajouter_mouvement_stock'),
    path('stock/mouvements/',liste_mouvements_stock, name='liste_mouvements_stock'),
    path('saisie/', saisie_inventaire, name='saisie_inventaire'),
    path('liste/', liste_inventaires, name='liste_inventaires'),
    path('valider/', valider_inventaire, name='valider_inventaire'),
     path('test-ecriture/', test_creation_ecriture, name='test_ecriture'),
    path("rapports/",rapport, name="rapport"),
    path("rapports/mouvements/",rapport_mouvements, name="rapport_mouvements"),

    path("clotures-du-jour/", clotures_du_jour, name="clotures_du_jour"),
    path("clotures-du-jour/pdf/", telecharger_rapport_cloture_pdf, name="rapport_cloture_pdf"),
 
    #user
   
    path('rapports/produits-alerte/pdf/', rapport_alertes_pdf, name='rapport_produits_alerte_pdf'),
    path('rapports/alerte/', rapport_alertes_pdf, name='rapport_alert'),
    path('rapports/ecarts-inventaire/', rapport_ecarts_inventaire_pdf, name='rapport_ecarts_pd'),
    path('ajouter-produits/',AjoutMultipleProduitsView.as_view() ,name='ajout_multiple_produits'),
     path('produit/<int:pk>/', ModifierProduitView.as_view(), name='modif_produit'),
    path('produit/voir/<int:pk>/', voir_produit, name='voir_produit'),
    path('produit/imprimer/<int:pk>/', imprimer_produit, name='imprime_produit'),
    path('produits/export/excel/', exporter_produits_excel, name='exporter_produits_excel'),
    path('produits/export/pdf/', exporter_produits_pdf, name='exporter_produits_pdf'),
    path('admin/telecharger-sauvegarde/', telecharger_sauvegarde, name='telecharger_sauvegarde'),
    path('creer-facture/<int:commande_id>/',creer_facture, name='creer_facture'),
    
   
    
    # URL corrigée pour enregistrer un paiement (en POST seulement)
    path('enregistrer-paiement/<int:facture_id>/',enregistrer_paiement, name='enregistrer_paiement'),
    path('factures/', liste_factures, name='liste_factures'),
    path('factures/<int:pk>/imprimer/', FacturePDFView.as_view(), name='facture_pdf'),
    path('paiements/', liste_paiements, name='liste_paiements'),
    path('facture/<int:facture_id>/actions/', actions_facture, name='actions_facture'),
    path('facture/<int:pk>/', detail_facture, name='detail_facture'),
    path('paiements/',liste_paiements, name='liste_paiements'),
    path('notifications/', liste_notifications, name='notifications'),
    
    
    
    path('retour/', liste_retours, name='liste_retours'),
    path('commandes/<int:commande_id>/retour/', creer_retour, name='creer_retour'),
    path('retour/<int:retour_id>/', detail_retour, name='detail_retour'),
    path('retour/<int:retour_id>/traiter/', traiter_retour, name='traiter_retour'),
    path('api/commandes/<int:commande_id>/lignes/', get_lignes_commande, name='get_lignes_commande'),

    
    path('api/lignes_commande/<int:commande_id>/',get_lignes_commande, name='get_lignes_commande'),
    path('paramettre/param',parametre,name="Liste_parametres"),
    
    #promotions et remises 
    path('promotion/',liste_promotions, name='liste_promotions'),
    path('nouvelle/', creer_promotion, name='creer_promotion'),
    path('<int:promotion_id>/toggle/', toggle_promotion, name='toggle_promotion'),
    path('<int:promotion_id>/supprimer/', supprimer_promotion, name='supprimer_promotion'),
    path('commande/<int:commande_id>/appliquer/',appliquer_promotion_commande, name='appliquer_promotion'),

    path('chatbot/', chatbot_view, name='chatbot_view'),
    path('chatbot/query/', chatbot_query, name='chatbot_query'),
    path('produit/<int:pk>/prevision/',forecast_view, name='forecast'),
    path('produit/<int:pk>/', product_detail, name='product_detail'),  # Nouvelle 
    path('produit/<int:pk>/prevision/', forecast_view, name='forecast'),

    # path('achats/<int:achat_id>/retour/',retour_fournisseur, name='retour_fournisseur'),
    # path('retours/supprimer/<int:retour_id>/', supprimer_retour, name='supprimer_retour'),
    # path('retours/<int:pk>/pdf/', RetourFournisseurDetailPDF.as_view(), name='retour_fournisseur_pdf'),
    
    
      # Créer un bon de livraison depuis une commande
    path('commandes/<int:commande_id>/generer-bl/', generer_bon_livraison, name='generer_bon_livraison'),

    # Liste des bons de livraison
    path('bons-livraison/', liste_bons_livraison, name='liste_bons_livraison'),
    path('creer-bon-livraison/', choisir_commande_pour_bl, name='creer_bon_livraison'),

    # Détail du BL
    path('bons-livraison/<int:bl_id>/', detail_bon_livraison, name='detail_bon_livraison'),

    # Générer PDF du BL
    path('bons-livraison/<int:bl_id>/pdf/', bon_livraison_pdf, name='bon_livraison_pdf'),
    
    
    
    
    
    
     path("gestion_stock_et_produit/xkahhdtw/", gestion_stock_et_produit, name="gestion_stock_et_produit"),
      path("ventemodule/xkahhdtw/", venteModule, name="venteModule"),
    
     # Comptes
    path('comptes/', liste_comptes, name='liste_comptes'),
    path('comptes/ajouter/', ajouter_compte, name='ajouter_compte'),
    path('comptes/<int:pk>/', detail_compte, name='detail_compte'),
    
    # Transactions
    path('transactions/', liste_transactions, name='liste_transactions'),
    path('transactions/ajouter/', ajouter_transaction, name='ajouter_transaction'),
    path('transactions/<int:pk>/', detail_transaction, name='detail_transaction'),
    
    # Catégories
    path('categories/', liste_categories, name='liste_categories'),
    path('categories/ajouter/', ajouter_categorie, name='ajouter_categorie'),
    
    # Rapports
    path('rapports/journal-caisse/', journal_caisse, name='journal_caisse'),
    path('rapports/balance/', balance_comptes, name='balance_comptes'),
    path('rapports/bilan-simplifie/', bilan_simplifie, name='bilan_simplifie'),
    path('rapports/journal-caisse/export-excel/', export_journal_excel, name='export_journal_excel'),
    path('tresorerie/dashboard/', dashboard_tresorerie, name='dashboard_tresorerie'),
    path('module_tresorerie/xlx2m,',Tresorerie,name="Tresorerie"),
    
    
    
      # URLs existantes...
    path('paiements/',liste_paiements, name='liste_paiements'),
    path('paiements/<int:pk>/',detail_paiement, name='detail_paiement'),

    path('set-devise/', set_devise, name='set_devise'),

    # urls.py

     # Devises et taux de change
    path('devises/',liste_devises, name='liste_devises'),
    path('devises/modifier/<int:taux_id>/', modifier_taux, name='modifier_taux'),
    path('devises/supprimer/<int:taux_id>/', supprimer_taux, name='supprimer_taux'),
    path('devises/ajouter/',ajouter_devise, name='ajouter_devise'),
    path('devises/taux/ajouter/',ajouter_taux, name='ajouter_taux'),
    path('devises/taux/maj-auto/',maj_taux_auto, name='maj_taux_auto'),
    path('devises-disponibles/',obtenir_devises_disponibles, name='devises_disponibles'),

    path('Historique/taux-change/', historique_taux, name='historique_taux'),
    path('changer-devise/',changer_devise, name='changer_devise'),
    path('api/taux-change/', obtenir_taux_change, name='obtenir_taux_change'),

    
    
    #reception

  
    #backup
   # Backup URLs
path('backup/', backup_management, name='backup_management'),
path('backup/create/', manual_backup, name='manual_backup'),
path('backup/download/<str:filename>/', download_backup, name='download_backup'),
path('backup/delete/', delete_backup, name='delete_backup'),
path('backup/restore/', restore_backup, name='restore_backup'),

#licence et abonnement app
  # path('licence/expiree/', page_licence_expiree, name='licence_expiree'),
  # path('licence/activer/', activer_licence, name='activer_licence'),
  # path('api/generer-licence/', generer_licence_api, name='generer_licence_api'),
  # path('api/licences/', LicenceListCreateAPIView.as_view(), name='licence-list'),
  # path('api/licences/<int:pk>/', LicenceDetailAPIView.as_view(), name='licence-detail'),
  # path('api/activate-licence/', ActivateLicenceView.as_view(), name='activate-licence'),
  #  path('api/licences/', LicenceAPIView.as_view(), name='licence-api'),
  #   path('api/licences/activate/', LicenceActivationAPIView.as_view(), name='activate-licence'),
  #   path('api/generer-licence/', generer_licence_api, name='legacy-generate-licence'),

    
    
    
]

    
    

 

    




  
  



    
    



    

