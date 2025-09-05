from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth.models import Permission
from .models import (
    Devis, LigneDevis, DevisStatutHistory, DevisAuditLog,
    Commande, LigneCommande, CommandeStatutHistory, CommandeAuditLog,
    BonLivraison, LigneBonLivraison, BonLivraisonStatutHistory, BonLivraisonAuditLog,
    Facture, LigneFacture, FactureStatutHistory, FactureAuditLog, Paiement,
    PointDeVente, SessionPOS, VentePOS, LigneVentePOS, PaiementPOS
)

# === ADMIN INLINES ===

class LigneDevisInline(admin.TabularInline):
    model = LigneDevis
    extra = 1
    fields = ['produit', 'quantite', 'prix_unitaire', 'taux_tva', 'montant_ht', 'montant_tva']
    readonly_fields = ['montant_ht', 'montant_tva']

class LigneCommandeInline(admin.TabularInline):
    model = LigneCommande
    extra = 1
    fields = ['produit', 'quantite', 'prix_unitaire', 'taux_tva', 'montant_ht', 'montant_tva']
    readonly_fields = ['montant_ht', 'montant_tva']

class LigneBonLivraisonInline(admin.TabularInline):
    model = LigneBonLivraison
    extra = 1
    fields = ['produit', 'quantite', 'prix_unitaire', 'taux_tva', 'montant_ht', 'montant_tva']
    readonly_fields = ['montant_ht', 'montant_tva']

class LigneFactureInline(admin.TabularInline):
    model = LigneFacture
    extra = 1
    fields = ['article', 'quantite', 'prix_unitaire', 'taux_tva', 'remise', 'montant_ht', 'montant_tva']
    readonly_fields = ['montant_ht', 'montant_tva']

class PaiementInline(admin.TabularInline):
    model = Paiement
    extra = 1
    fields = ['montant', 'date', 'mode_paiement', 'reference', 'notes']
    readonly_fields = ['created_at']

class LigneVentePOSInline(admin.TabularInline):
    model = LigneVentePOS
    extra = 1
    fields = ['article', 'quantite', 'prix_unitaire', 'taux_tva', 'montant_ht', 'montant_tva']
    readonly_fields = ['montant_ht', 'montant_tva']

class PaiementPOSInline(admin.TabularInline):
    model = PaiementPOS
    extra = 1
    fields = ['montant', 'date', 'mode_paiement', 'reference']

# === HISTORY INLINES ===

class DevisStatutHistoryInline(admin.TabularInline):
    model = DevisStatutHistory
    extra = 0
    readonly_fields = ['changed_at', 'changed_by', 'ancien_statut', 'nouveau_statut', 'commentaire']
    can_delete = False

class CommandeStatutHistoryInline(admin.TabularInline):
    model = CommandeStatutHistory
    extra = 0
    readonly_fields = ['changed_at', 'changed_by', 'ancien_statut', 'nouveau_statut', 'commentaire']
    can_delete = False

class BonLivraisonStatutHistoryInline(admin.TabularInline):
    model = BonLivraisonStatutHistory
    extra = 0
    readonly_fields = ['changed_at', 'changed_by', 'ancien_statut', 'nouveau_statut', 'commentaire']
    can_delete = False

class FactureStatutHistoryInline(admin.TabularInline):
    model = FactureStatutHistory
    extra = 0
    readonly_fields = ['changed_at', 'changed_by', 'ancien_statut', 'nouveau_statut', 'commentaire']
    can_delete = False

# === ADMIN MODELS ===

@admin.register(Devis)
class DevisAdmin(admin.ModelAdmin):
    list_display = ['numero', 'client', 'date', 'echeance', 'statut', 'total_ht', 'total_tva', 'total_ttc', 'entreprise']
    list_filter = ['statut', 'date', 'entreprise', 'created_at']
    search_fields = ['numero', 'client__nom', 'client__prenom']
    readonly_fields = ['total_ht', 'total_tva', 'total_ttc', 'created_at', 'updated_at']
    inlines = [LigneDevisInline, DevisStatutHistoryInline]
    fieldsets = (
        ('Informations Générales', {
            'fields': ('entreprise', 'client', 'numero', 'date', 'echeance', 'statut')
        }),
        ('Informations Financières', {
            'fields': ('remise', 'total_ht', 'total_tva', 'total_ttc')
        }),
        ('Notes et Métadonnées', {
            'fields': ('notes', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(entreprise=request.user.entreprise)

@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ['numero', 'client', 'date', 'statut', 'total_ht', 'total_tva', 'total_ttc', 'entreprise']
    list_filter = ['statut', 'date', 'entreprise', 'created_at']
    search_fields = ['numero', 'client__nom', 'client__prenom']
    readonly_fields = ['total_ht', 'total_tva', 'total_ttc', 'created_at', 'updated_at']
    inlines = [LigneCommandeInline, CommandeStatutHistoryInline]
    fieldsets = (
        ('Informations Générales', {
            'fields': ('entreprise', 'client', 'devis', 'numero', 'date', 'statut')
        }),
        ('Informations Financières', {
            'fields': ('total_ht', 'total_tva', 'total_ttc')
        }),
        ('Notes et Métadonnées', {
            'fields': ('notes', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(entreprise=request.user.entreprise)

@admin.register(BonLivraison)
class BonLivraisonAdmin(admin.ModelAdmin):
    list_display = ['numero', 'commande', 'date', 'statut', 'total_ht', 'total_tva', 'total_ttc', 'entreprise']
    list_filter = ['statut', 'date', 'entreprise', 'created_at']
    search_fields = ['numero', 'commande__numero', 'commande__client__nom']
    readonly_fields = ['total_ht', 'total_tva', 'total_ttc', 'created_at', 'updated_at']
    inlines = [LigneBonLivraisonInline, BonLivraisonStatutHistoryInline]
    fieldsets = (
        ('Informations Générales', {
            'fields': ('entreprise', 'commande', 'numero', 'date', 'statut')
        }),
        ('Informations Financières', {
            'fields': ('total_ht', 'total_tva', 'total_ttc')
        }),
        ('Notes et Métadonnées', {
            'fields': ('notes', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(entreprise=request.user.entreprise)

@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ['numero', 'client', 'date_facture', 'date_echeance', 'statut', 'total_ttc', 'montant_restant', 'entreprise']
    list_filter = ['statut', 'date_facture', 'mode_paiement', 'entreprise', 'created_at']
    search_fields = ['numero', 'client__nom', 'client__prenom']
    readonly_fields = ['total_ht', 'total_tva', 'total_ttc', 'montant_restant', 'created_at', 'updated_at']
    inlines = [LigneFactureInline, PaiementInline, FactureStatutHistoryInline]
    fieldsets = (
        ('Informations Générales', {
            'fields': ('entreprise', 'client', 'devis', 'commande', 'bon_livraison', 'numero', 'date', 'echeance', 'statut')
        }),
        ('Informations Financières', {
            'fields': ('remise', 'total_ht', 'total_tva', 'total_ttc', 'montant_restant', 'mode_paiement')
        }),
        ('Informations Supplémentaires', {
            'fields': ('conditions_paiement', 'reference_client', 'notes', 'devise', 'langue'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(entreprise=request.user.entreprise)

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ['facture', 'montant', 'date', 'mode_paiement', 'entreprise']
    list_filter = ['mode_paiement', 'date', 'entreprise', 'created_at']
    search_fields = ['facture__numero', 'reference']
    readonly_fields = ['created_at']
    fields = ['entreprise', 'facture', 'montant', 'date', 'mode_paiement', 'reference', 'notes', 'created_by', 'created_at']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(entreprise=request.user.entreprise)

# === POINT DE VENTE ADMIN ===

@admin.register(PointDeVente)
class PointDeVenteAdmin(admin.ModelAdmin):
    list_display = ['code', 'nom', 'adresse', 'responsable', 'actif', 'entreprise']
    list_filter = ['actif', 'entreprise', 'created_at']
    search_fields = ['code', 'nom', 'adresse']
    fields = ['entreprise', 'code', 'nom', 'adresse', 'responsable', 'actif', 'created_at', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(entreprise=request.user.entreprise)

@admin.register(SessionPOS)
class SessionPOSAdmin(admin.ModelAdmin):
    list_display = ['point_de_vente', 'utilisateur', 'date_ouverture', 'date_fermeture', 'statut', 'fonds_ouverture', 'fonds_fermeture']
    list_filter = ['statut', 'point_de_vente', 'date_ouverture']
    readonly_fields = ['date_ouverture', 'date_fermeture']
    fields = ['point_de_vente', 'utilisateur', 'fonds_ouverture', 'fonds_fermeture', 'statut', 'date_ouverture', 'date_fermeture']

@admin.register(VentePOS)
class VentePOSAdmin(admin.ModelAdmin):
    list_display = ['numero', 'session', 'client', 'date', 'total_ttc']
    list_filter = ['session', 'date']
    search_fields = ['numero', 'client__nom']
    readonly_fields = ['total_ht', 'total_tva', 'total_ttc', 'date']
    inlines = [LigneVentePOSInline, PaiementPOSInline]
    fieldsets = (
        ('Informations Générales', {
            'fields': ('session', 'client', 'numero', 'date')
        }),
        ('Informations Financières', {
            'fields': ('remise', 'total_ht', 'total_tva', 'total_ttc')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

# === AUDIT LOGS ADMIN ===

@admin.register(DevisAuditLog)
class DevisAuditLogAdmin(admin.ModelAdmin):
    list_display = ['devis', 'action', 'performed_by', 'performed_at']
    list_filter = ['action', 'performed_at']
    search_fields = ['devis__numero', 'description']
    readonly_fields = ['performed_at']
    fields = ['devis', 'action', 'description', 'performed_by', 'performed_at', 'details']

@admin.register(CommandeAuditLog)
class CommandeAuditLogAdmin(admin.ModelAdmin):
    list_display = ['commande', 'action', 'performed_by', 'performed_at']
    list_filter = ['action', 'performed_at']
    search_fields = ['commande__numero', 'description']
    readonly_fields = ['performed_at']
    fields = ['commande', 'action', 'description', 'performed_by', 'performed_at', 'details']

@admin.register(BonLivraisonAuditLog)
class BonLivraisonAuditLogAdmin(admin.ModelAdmin):
    list_display = ['bon_livraison', 'action', 'performed_by', 'performed_at']
    list_filter = ['action', 'performed_at']
    search_fields = ['bon_livraison__numero', 'description']
    readonly_fields = ['performed_at']
    fields = ['bon_livraison', 'action', 'description', 'performed_by', 'performed_at', 'details']

@admin.register(FactureAuditLog)
class FactureAuditLogAdmin(admin.ModelAdmin):
    list_display = ['facture', 'action', 'performed_by', 'performed_at']
    list_filter = ['action', 'performed_at']
    search_fields = ['facture__numero', 'description']
    readonly_fields = ['performed_at']
    fields = ['facture', 'action', 'description', 'performed_by', 'performed_at', 'details']

# === HISTORY ADMIN ===

@admin.register(DevisStatutHistory)
class DevisStatutHistoryAdmin(admin.ModelAdmin):
    list_display = ['devis', 'ancien_statut', 'nouveau_statut', 'changed_by', 'changed_at']
    list_filter = ['nouveau_statut', 'changed_at']
    search_fields = ['devis__numero', 'commentaire']
    readonly_fields = ['changed_at']
    fields = ['devis', 'ancien_statut', 'nouveau_statut', 'changed_by', 'changed_at', 'commentaire']

@admin.register(CommandeStatutHistory)
class CommandeStatutHistoryAdmin(admin.ModelAdmin):
    list_display = ['commande', 'ancien_statut', 'nouveau_statut', 'changed_by', 'changed_at']
    list_filter = ['nouveau_statut', 'changed_at']
    search_fields = ['commande__numero', 'commentaire']
    readonly_fields = ['changed_at']
    fields = ['commande', 'ancien_statut', 'nouveau_statut', 'changed_by', 'changed_at', 'commentaire']

@admin.register(BonLivraisonStatutHistory)
class BonLivraisonStatutHistoryAdmin(admin.ModelAdmin):
    list_display = ['bon_livraison', 'ancien_statut', 'nouveau_statut', 'changed_by', 'changed_at']
    list_filter = ['nouveau_statut', 'changed_at']
    search_fields = ['bon_livraison__numero', 'commentaire']
    readonly_fields = ['changed_at']
    fields = ['bon_livraison', 'ancien_statut', 'nouveau_statut', 'changed_by', 'changed_at', 'commentaire']

@admin.register(FactureStatutHistory)
class FactureStatutHistoryAdmin(admin.ModelAdmin):
    list_display = ['facture', 'ancien_statut', 'nouveau_statut', 'changed_by', 'changed_at']
    list_filter = ['nouveau_statut', 'changed_at']
    search_fields = ['facture__numero', 'commentaire']
    readonly_fields = ['changed_at']
    fields = ['facture', 'ancien_statut', 'nouveau_statut', 'changed_by', 'changed_at', 'commentaire']

# === PERMISSIONS ===

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'content_type', 'codename']
    list_filter = ['content_type']
    search_fields = ['name', 'codename']

# === REGISTRATION DES MODÈLES RESTANTS ===

admin.site.register(LigneDevis)
admin.site.register(LigneCommande)
admin.site.register(LigneBonLivraison)
admin.site.register(LigneFacture)
admin.site.register(LigneVentePOS)
admin.site.register(PaiementPOS)

# === CONFIGURATION DE L'ADMIN ===

admin.site.site_header = "Administration GStock"
admin.site.site_title = "Portail d'Administration GStock"
admin.site.index_title = "Gestion des Ventes"