from django.contrib import admin
from .models import Fournisseur, CommandeAchat, LigneCommandeAchat, BonReception
from parametres.mixins import EntrepriseAccessMixin

class LigneCommandeAchatInline(admin.TabularInline):
    model = LigneCommandeAchat
    extra = 0
    raw_id_fields = ['produit']

@admin.register(CommandeAchat)
class CommandeAchatAdmin(EntrepriseAccessMixin, admin.ModelAdmin):
    list_display = ('numero_commande', 'fournisseur', 'date_commande', 'statut', 'entreprise')
    list_filter = ('statut', 'entreprise')
    search_fields = ('numero_commande', 'fournisseur__nom')
    inlines = [LigneCommandeAchatInline]
    readonly_fields = ('entreprise', 'created_by')

@admin.register(Fournisseur)
class FournisseurAdmin(EntrepriseAccessMixin, admin.ModelAdmin):
    list_display = ('code', 'nom', 'email', 'telephone', 'entreprise')
    search_fields = ('code', 'nom', 'email')
    list_filter = ('entreprise',)

@admin.register(BonReception)
class BonReceptionAdmin(EntrepriseAccessMixin, admin.ModelAdmin):
    list_display = ('numero_bon', 'commande', 'date_reception', 'entreprise')
    list_filter = ('entreprise',)