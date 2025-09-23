from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import *

# Configuration de l'interface admin de base
admin.site.site_header = "Administration de FSJ Solution"
admin.site.site_title = "FSJ Solution Admin"
admin.site.index_title = "Gestion de l'application"


from django.contrib import admin
from django.http import HttpResponseRedirect

# @admin.register(SystemeLicence)
# class LicenceAdmin(admin.ModelAdmin):
#     list_display = ('cle_activation', 'date_expiration', 'est_active')
#     actions = ['generer_nouvelle_licence']

#     def generer_nouvelle_licence(self, request, queryset):
#         licence = SystemeLicence.creer_nouvelle_licence()
#         self.message_user(request, f"Nouvelle clé générée: {licence.cle_activation}")
#         return HttpResponseRedirect("/admin/STOCK/systemelicence/")

# Admin personnalisé pour Parametre
class ParametreAdmin(admin.ModelAdmin):
    list_display = ('nom_societe', 'devise_principale', 'taux_tva')
    fieldsets = (
        ('Informations Société', {
            'fields': ('user', 'nom_societe', 'adresse', 'telephone', 'email', 'logo')
        }),
        ('Configuration Financière', {
            'fields': ('devise_principale', 'taux_tva', 'devises_acceptees', 'taux_change_auto')
        }),
    )

# Admin pour TauxChange
class TauxChangeAdmin(admin.ModelAdmin):
    list_display = ('devise_source', 'devise_cible', 'taux', 'date_mise_a_jour', 'est_manuel')
    list_filter = ('est_manuel', 'devise_source', 'devise_cible')
    search_fields = ('devise_source', 'devise_cible')
    ordering = ('devise_source', 'devise_cible')

# Admin pour Produit avec filtres avancés
class ProduitAdmin(admin.ModelAdmin):
    list_display = ('nom', 'categorie', 'prix_achat', 'prix_vente', 'stock', 'seuil_alerte', 'actif')
    list_filter = ('categorie', 'actif')
    search_fields = ('nom', 'code_barre_numero')
    readonly_fields = ('code_barre_numero',)
    actions = ['generer_codes_barres']
    
    def generer_codes_barres(self, request, queryset):
        for produit in queryset:
            produit.generate_barcode()
            produit.save()
        self.message_user(request, f"Codes barres générés pour {queryset.count()} produits")
    generer_codes_barres.short_description = "Générer les codes barres"

# Admin pour Categorie
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'produit_count')
    
    def produit_count(self, obj):
        return obj.produit_set.count()
    produit_count.short_description = "Nombre de produits"

# Admin pour Client avec recherche
class ClientAdmin(admin.ModelAdmin):
    list_display = ('nom', 'email', 'telephone')
    search_fields = ('nom', 'email', 'telephone')



# Admin pour Fournisseur
# class FournisseurAdmin(admin.ModelAdmin):
#     list_display = ('nom', 'type', 'telephone', 'email')
#     list_filter = ('type',)
#     search_fields = ('nom', 'email', 'telephone')


# # Admin pour Achat avec conversion devise
# class AchatAdmin(admin.ModelAdmin):
#     list_display = ('produit', 'fournisseur', 'quantite', 'prix_unitaire', 'total_achat', 'date_achat','entreprise','notes','created_by','montant_original','numero_facture')
#     list_filter = ('fournisseur', 'date_achat')
#     search_fields = ('produit__nom', 'fournisseur__nom')
#     readonly_fields = ('total_achat',)
    
#     def total_achat(self, obj):
#         return obj.total_achat
#     total_achat.short_description = "Total"



    def reste_a_payer(self, obj):
        return obj.reste_a_payer()
    reste_a_payer.short_description = "Reste à payer"

# Admin pour Inventaire Physique
class InventairePhysiqueAdmin(admin.ModelAdmin):
    list_display = ('produit', 'stock_theorique', 'stock_physique', 'ecart', 'date', 'valide')
    list_filter = ('valide', 'date')
    search_fields = ('produit__nom',)
    actions = ['valider_inventaires']
    
    def valider_inventaires(self, request, queryset):
        for inventaire in queryset:
            if not inventaire.valide:
                inventaire.valide = True
                inventaire.save()
        self.message_user(request, f"{queryset.count()} inventaires validés")
    valider_inventaires.short_description = "Valider les inventaires sélectionnés"

# Admin pour Promotion
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('nom', 'type_remise', 'valeur', 'appliquer_a', 'date_debut', 'date_fin', 'actif')
    list_filter = ('type_remise', 'appliquer_a', 'actif')
    search_fields = ('nom', 'code_promo')
    readonly_fields = ('utilisations_actuelles',)




    def solde_actuel(self, obj):
        return obj.solde_actuel()
    solde_actuel.short_description = "Solde actuel"



# Admin pour Notifications
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('destinataire', 'type', 'message_short', 'est_lu', 'date_creation')
    list_filter = ('type', 'est_lu', 'date_creation')
    search_fields = ('destinataire__username', 'message')
    
    def message_short(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_short.short_description = "Message"

# Enregistrement des modèles
admin.site.register(Parametre, ParametreAdmin)
admin.site.register(TauxChange, TauxChangeAdmin)
admin.site.register(Categorie, CategorieAdmin)
admin.site.register(Produit, ProduitAdmin)
admin.site.register(Client, ClientAdmin)

# admin.site.register(Fournisseur, FournisseurAdmin)

admin.site.register(InventairePhysique, InventairePhysiqueAdmin)

admin.site.register(SuggestionReapprovisionnement)
