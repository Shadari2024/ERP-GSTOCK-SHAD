from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import PlanComptableOHADA, JournalComptable, EcritureComptable, LigneEcriture, CompteAuxiliaire

@admin.register(PlanComptableOHADA)
class PlanComptableOHADAAdmin(admin.ModelAdmin):
    list_display = ('numero', 'intitule', 'classe', 'type_compte', 'entreprise')
    list_filter = ('classe', 'type_compte', 'entreprise')
    search_fields = ('numero', 'intitule')
    ordering = ('numero',)

@admin.register(JournalComptable)
class JournalComptableAdmin(admin.ModelAdmin):
    list_display = ('code', 'intitule', 'type_journal', 'actif', 'entreprise')
    list_filter = ('type_journal', 'actif', 'entreprise')
    search_fields = ('code', 'intitule')
    ordering = ('code',)

@admin.register(EcritureComptable)
class EcritureComptableAdmin(admin.ModelAdmin):
    list_display = ('numero', 'journal', 'date_ecriture', 'libelle', 'entreprise')
    list_filter = ('journal', 'date_ecriture', 'entreprise')
    search_fields = ('numero', 'libelle')
    ordering = ('-date_ecriture', '-numero')
    date_hierarchy = 'date_ecriture'

@admin.register(LigneEcriture)
class LigneEcritureAdmin(admin.ModelAdmin):
    list_display = ('ecriture', 'compte', 'debit', 'credit')
    list_filter = ('compte',)
    search_fields = ('ecriture__numero', 'compte__numero')

@admin.register(CompteAuxiliaire)
class CompteAuxiliaireAdmin(admin.ModelAdmin):
    list_display = ('code', 'intitule', 'type_compte', 'compte_general', 'actif', 'entreprise')
    list_filter = ('type_compte', 'actif', 'entreprise')
    search_fields = ('code', 'intitule')
    ordering = ('code',)