from django.contrib import admin
from .models import KPI, KPIValue, Report, DataExport, DataImport, AIIntegration

@admin.register(KPI)
class KPIAdmin(admin.ModelAdmin):
    list_display = ['nom', 'code', 'type_kpi', 'periodicite', 'entreprise', 'actif']
    list_filter = ['type_kpi', 'periodicite', 'entreprise', 'actif']
    search_fields = ['nom', 'code', 'description']

@admin.register(KPIValue)
class KPIValueAdmin(admin.ModelAdmin):
    list_display = ['kpi', 'valeur', 'date_mesure', 'entreprise']
    list_filter = ['date_mesure', 'entreprise']
    readonly_fields = ['created_at']

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_rapport', 'public', 'entreprise']
    list_filter = ['type_rapport', 'public', 'entreprise']
    search_fields = ['nom', 'description']

@admin.register(DataExport)
class DataExportAdmin(admin.ModelAdmin):
    list_display = ['nom_fichier', 'format_export', 'taille_fichier', 'entreprise', 'created_at']
    list_filter = ['format_export', 'entreprise']
    readonly_fields = ['created_at']

@admin.register(DataImport)
class DataImportAdmin(admin.ModelAdmin):
    list_display = ['nom_fichier', 'type_import', 'statut', 'entreprise', 'created_at']
    list_filter = ['type_import', 'statut', 'entreprise']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(AIIntegration)
class AIIntegrationAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_ia', 'precision', 'actif', 'entreprise']
    list_filter = ['type_ia', 'actif', 'entreprise']