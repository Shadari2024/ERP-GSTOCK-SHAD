from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from .models import UtilisateurPersonnalise, ProfilUtilisateur, JournalActivite

class ProfilUtilisateurInline(admin.StackedInline):
    model = ProfilUtilisateur
    can_delete = False
    verbose_name_plural = 'Profils'

class UtilisateurPersonnaliseAdmin(UserAdmin):
    inlines = (ProfilUtilisateurInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'email', 'telephone')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'role'),
        }),
    )
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)

class JournalActiviteAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'action', 'date_heure', 'ip_address')
    list_filter = ('action', 'date_heure')
    search_fields = ('utilisateur__username', 'details', 'ip_address')
    readonly_fields = ('utilisateur', 'action', 'details', 'ip_address', 'date_heure')
    
    def has_add_permission(self, request):
        return False

admin.site.register(UtilisateurPersonnalise, UtilisateurPersonnaliseAdmin)
admin.site.register(JournalActivite, JournalActiviteAdmin)

# Personnalisation de l'interface admin
admin.site.site_header = "Administration du Système de Gestion"
admin.site.site_title = "Système de Gestion"
admin.site.index_title = "Tableau de bord d'administration"