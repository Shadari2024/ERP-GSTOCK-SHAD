from django.contrib import admin
from .models import (
    PlanTarification,
    Entreprise,
    Abonnement,
    ConfigurationSAAS,
    Devise,
    TauxChange,
    ParametreDocument,
    AuditConfiguration
)

@admin.register(PlanTarification)
class PlanTarificationAdmin(admin.ModelAdmin):
    list_display = ('nom', 'niveau', 'prix_mensuel', 'utilisateurs_inclus')
    list_filter = ('niveau', 'support_24h')
    search_fields = ('nom',)

@admin.register(Entreprise)
class EntrepriseAdmin(admin.ModelAdmin):
    list_display = ('nom', 'domaine', 'statut', 'plan_tarification')
    list_filter = ('statut', 'plan_tarification', 'active')
    search_fields = ('nom', 'domaine', 'email')
    readonly_fields = ('slug',)
    filter_horizontal = ()

@admin.register(Abonnement)
class AbonnementAdmin(admin.ModelAdmin):
    list_display = ('entreprise', 'plan_actuel', 'methode_paiement', 'date_fin')
    list_filter = ('plan_actuel', 'methode_paiement')
    search_fields = ('entreprise__nom', 'id_abonnement_paiement')

@admin.register(ConfigurationSAAS)
class ConfigurationSAASAdmin(admin.ModelAdmin):
    list_display = ('entreprise', 'langue', 'devise_principale')
    list_filter = ('langue',)

@admin.register(Devise)
class DeviseAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'symbole', 'active')
    list_editable = ('active',)
    search_fields = ('code', 'nom')

@admin.register(TauxChange)
class TauxChangeAdmin(admin.ModelAdmin):
    list_display = ('devise_source', 'devise_cible', 'taux', 'date_application', 'est_actif')
    list_filter = ('devise_source', 'devise_cible', 'est_actif')
    date_hierarchy = 'date_application'

@admin.register(ParametreDocument)
class ParametreDocumentAdmin(admin.ModelAdmin):
    list_display = ('entreprise', 'type_document', 'prefixe', 'compteur')
    list_filter = ('type_document', 'reinitialisation')

@admin.register(AuditConfiguration)
class AuditConfigurationAdmin(admin.ModelAdmin):
    list_display = ('entreprise', 'action', 'modele', 'timestamp')
    list_filter = ('action', 'modele')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp',)