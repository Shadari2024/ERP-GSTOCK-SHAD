from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from .models import (
    ClientCRM, Opportunite, Activite, NoteClient,
    SourceLead, StatutOpportunite, TypeActivite,
    PipelineVente, EtapePipeline, ObjectifCommercial
)

User = get_user_model()

@admin.register(ClientCRM)
class ClientCRMAdmin(admin.ModelAdmin):
    list_display = ['nom', 'type_client', 'statut', 'ville', 'valeur_commerciale', 'entreprise']
    list_filter = ['type_client', 'statut', 'ville', 'pays', 'entreprise']
    search_fields = ['nom', 'email', 'telephone', 'ville']
    readonly_fields = ['cree_le', 'modifie_le', 'valeur_commerciale']
    fieldsets = (
        (None, {
            'fields': ('entreprise', 'type_client', 'statut', 'code_client', 'nom')
        }),
        (_('Coordonnées'), {
            'fields': ('telephone', 'telephone_secondaire', 'email', 'website')
        }),
        (_('Adresse'), {
            'fields': ('adresse', 'ville', 'code_postal', 'pays')
        }),
        (_('Informations commerciales'), {
            'fields': ('devise_preferee', 'limite_credit', 'delai_paiement', 'taux_remise')
        }),
        (_('Informations fiscales'), {
            'fields': ('numero_tva', 'numero_fiscal', 'exonere_tva')
        }),
        (_('Métadonnées'), {
            'fields': ('notes', 'cree_par', 'cree_le', 'modifie_le')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(entreprise=request.user.entreprise)

@admin.register(Opportunite)
class OpportuniteAdmin(admin.ModelAdmin):
    list_display = ['nom', 'client', 'montant_estime', 'probabilite', 'statut', 'priorite', 'entreprise']
    list_filter = ['statut', 'priorite', 'date_creation', 'entreprise']
    search_fields = ['nom', 'client__nom', 'description']
    readonly_fields = ['date_creation', 'date_modification', 'valeur_attendue']
    fieldsets = (
        (None, {
            'fields': ('entreprise', 'client', 'nom', 'description')
        }),
        (_('Valeur'), {
            'fields': ('montant_estime', 'probabilite', 'valeur_attendue')
        }),
        (_('Statut'), {
            'fields': ('statut', 'priorite', 'date_fermeture_prevue', 'date_fermeture_reelle')
        }),
        (_('Assignation'), {
            'fields': ('assigne_a', 'cree_par')
        }),
        (_('Documents liés'), {
            'fields': ('devis_lie', 'commande_liee')
        }),
        (_('Métadonnées'), {
            'fields': ('date_creation', 'date_modification')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(entreprise=request.user.entreprise)

@admin.register(Activite)
class ActiviteAdmin(admin.ModelAdmin):
    list_display = ['sujet', 'type_activite', 'date_debut', 'date_echeance', 'statut', 'priorite', 'entreprise']
    list_filter = ['type_activite', 'statut', 'priorite', 'date_debut', 'entreprise']
    search_fields = ['sujet', 'description', 'clients__nom', 'opportunites__nom']
    filter_horizontal = ['clients', 'opportunites']
    readonly_fields = ['date_creation', 'date_modification']
    fieldsets = (
        (None, {
            'fields': ('entreprise', 'type_activite', 'sujet', 'description')
        }),
        (_('Planning'), {
            'fields': ('date_debut', 'date_echeance', 'statut', 'priorite')
        }),
        (_('Assignation'), {
            'fields': ('assigne_a', 'cree_par')
        }),
        (_('Relations'), {
            'fields': ('clients', 'opportunites')
        }),
        (_('Rappel'), {
            'fields': ('rappel', 'date_rappel')
        }),
        (_('Résultat'), {
            'fields': ('resultat',)
        }),
        (_('Métadonnées'), {
            'fields': ('date_creation', 'date_modification')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(entreprise=request.user.entreprise)

# Enregistrement des autres modèles
admin.site.register(SourceLead)
admin.site.register(StatutOpportunite)
admin.site.register(TypeActivite)
admin.site.register(PipelineVente)
admin.site.register(EtapePipeline)
admin.site.register(ObjectifCommercial)
admin.site.register(NoteClient)


