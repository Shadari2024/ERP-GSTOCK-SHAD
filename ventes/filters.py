# ventes/filters.py

import django_filters
from django import forms # <<< IMPORT THIS LINE
from .models import *
from STOCK.models import Client # Assurez-vous que Client est importé

class CommandeFilter(django_filters.FilterSet):
    # Recherche par numéro de commande (contient)
    numero = django_filters.CharFilter(
        field_name='numero', 
        lookup_expr='icontains', # 'i' pour insensible à la casse
        label="Numéro de commande"
    )
    
    # Recherche par client (sélection)
    client = django_filters.ModelChoiceFilter(
        queryset=Client.objects.all(), # Sera filtré par entreprise dans la vue
        field_name='client',
        label="Client"
    )

    # Filtrage par statut (sélection multiple)
    statut = django_filters.MultipleChoiceFilter(
        choices=Commande.STATUT_CHOICES,
        # For multiple choices, CSVWidget is fine or you can use CheckboxSelectMultiple
        widget=forms.CheckboxSelectMultiple, # This is often more user-friendly than CSVWidget
        label="Statut(s)"
    )

    # Filtrage par date de commande (plage)
    date_min = django_filters.DateFilter(
        field_name='date', 
        lookup_expr='gte', # Greater than or equal to
        widget=forms.DateInput(attrs={'type': 'date'}), # <<< CHANGE THIS LINE
        label="Date de commande (min)"
    )
    date_max = django_filters.DateFilter(
        field_name='date', 
        lookup_expr='lte', # Less than or equal to
        widget=forms.DateInput(attrs={'type': 'date'}), # <<< CHANGE THIS LINE
        label="Date de commande (max)"
    )

    class Meta:
        model = Commande
        fields = ['numero', 'client', 'statut', 'date_min', 'date_max']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'request' in kwargs and hasattr(kwargs['request'], 'entreprise'):
            self.filters['client'].queryset = Client.objects.filter(entreprise=kwargs['request'].entreprise)
            
            
            
            
            
# --- NEW: DevisFilter ---
class DevisFilter(django_filters.FilterSet):
    numero = django_filters.CharFilter(
        field_name='numero', 
        lookup_expr='icontains', 
        label="Numéro de devis"
    )
    client = django_filters.ModelChoiceFilter(
        queryset=Client.objects.all(), # Will be filtered by entreprise in the view
        field_name='client',
        label="Client"
    )
    statut = django_filters.MultipleChoiceFilter(
        choices=Devis.STATUT_CHOICES, # Use Devis's status choices
        widget=forms.CheckboxSelectMultiple, 
        label="Statut(s)"
    )
    date_min = django_filters.DateFilter(
        field_name='date', # Assuming your Devis model has a 'date' field for the quote date
        lookup_expr='gte', 
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Date du devis (min)"
    )
    date_max = django_filters.DateFilter(
        field_name='date', 
        lookup_expr='lte', 
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Date du devis (max)"
    )

    class Meta:
        model = Devis
        fields = ['numero', 'client', 'statut', 'date_min', 'date_max']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter client queryset by the user's entreprise
        if 'request' in kwargs and hasattr(kwargs['request'], 'entreprise'):
            self.filters['client'].queryset = Client.objects.filter(entreprise=kwargs['request'].entreprise)



# ventes/filters.py
import django_filters
from django import forms 
from django.db.models import Q # <--- ADD THIS IMPORT!
from .models import BonLivraison, Commande 
 
# --- Corrected BonLivraisonFilter ---
class BonLivraisonFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='filter_by_search_query',
        label='Recherche',
        widget=forms.TextInput(attrs={'placeholder': 'Numéro BL'}) # Changed placeholder
    )
    
    statut = django_filters.ChoiceFilter(
        choices=BonLivraison.STATUT_CHOICES, 
        empty_label='Tous les statuts',
        label='Statut'
    )
    
    date_gte = django_filters.DateFilter(
        field_name='date', 
        lookup_expr='gte', 
        label='Date de début',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    date_lte = django_filters.DateFilter(
        field_name='date', 
        lookup_expr='lte', 
        label='Date de fin',
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = BonLivraison
        fields = ['q', 'statut', 'date_gte', 'date_lte']

    def filter_by_search_query(self, queryset, name, value):
        # Only filter by BonLivraison number, removing client name lookups
        return queryset.filter(
            Q(numero__icontains=value) 
            # Removed: Q(commande__client__nom__icontains=value) |
            # Removed: Q(commande__client__prenom__icontains=value)
        )
        
        
        

class FactureFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='filter_by_search_query',
        label='Recherche',
        widget=forms.TextInput(attrs={'placeholder': 'Numéro Facture ou Nom Client'})
    )
    
    statut = django_filters.ChoiceFilter(
        choices=Facture.STATUT_CHOICES, 
        empty_label='Tous les statuts',
        label='Statut'
    )
    
    date_gte = django_filters.DateFilter(
        field_name='date', 
        lookup_expr='gte', 
        label='Date de début',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    date_lte = django_filters.DateFilter(
        field_name='date', 
        lookup_expr='lte', 
        label='Date de fin',
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = Facture
        fields = ['q', 'statut', 'date_gte', 'date_lte']

    def filter_by_search_query(self, queryset, name, value):
        # We can try to re-enable client name search here for Facture,
        # as Facture has a direct ForeignKey to Client.
        # This assumes your Client model has 'nom' and 'prenom' fields.
        return queryset.filter(
            Q(numero__icontains=value) | 
            Q(client__nom__icontains=value) | 
            Q(client__prenom__icontains=value) 
        ).distinct() # Use distinct to avoid duplicate results if a client matches multiple criteria