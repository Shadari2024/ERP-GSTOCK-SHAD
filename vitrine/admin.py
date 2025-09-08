from django.contrib import admin
from .models import DemandeDemo

@admin.register(DemandeDemo)
class DemandeDemoAdmin(admin.ModelAdmin):
    list_display = ('nom', 'entreprise', 'email', 'date_soumission', 'traite')
    list_filter = ('traite', 'date_soumission')
    search_fields = ('nom', 'entreprise', 'email')
    readonly_fields = ('date_soumission',)
    list_editable = ('traite',)