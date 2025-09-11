from django import forms

from .models import (
    ClientCRM, Opportunite, Activite, NoteClient, 
    SourceLead, StatutOpportunite, TypeActivite,
    PipelineVente, ObjectifCommercial
)

from django.contrib.auth import get_user_model
from parametres.models import ConfigurationSAAS
from .models import Opportunite, ClientCRM, StatutOpportunite
from ventes.models import *
from django.utils.translation import gettext_lazy as _
from STOCK.models import Client  # Importez le modèle Client réel

class ClientCRMForm(forms.ModelForm):
    class Meta:
        model = Client  # Utilisez le modèle Client réel
        fields = [
            'type_client', 'nom', 'telephone', 'email', 'adresse', 
            'ville', 'code_postal', 'pays', 'limite_credit', 
            'delai_paiement', 'taux_remise', 'numero_tva', 
            'numero_fiscal', 'exonere_tva', 'notes'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'adresse': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        # Masquer le champ code_client car il est généré automatiquement
        if 'code_client' in self.fields:
            self.fields['code_client'].widget = forms.HiddenInput()
            self.fields['code_client'].required = False
        
        # Masquer le champ statut car il a une valeur par défaut
        if 'statut' in self.fields:
            self.fields['statut'].widget = forms.HiddenInput()
            self.fields['statut'].required = False
        
        # Masquer le champ entreprise
        if 'entreprise' in self.fields:
            self.fields['entreprise'].widget = forms.HiddenInput()
            self.fields['entreprise'].required = False
        
        # Configurer les champs facultatifs
        for field_name in ['telephone_secondaire', 'website', 'numero_tva', 'numero_fiscal']:
            if field_name in self.fields:
                self.fields[field_name].required = False
class StatutOpportuniteForm(forms.ModelForm):
    class Meta:
        model = StatutOpportunite
        fields = ['nom', 'ordre', 'couleur', 'est_gagnant', 'est_perdant']
        widgets = {
            'couleur': forms.TextInput(attrs={'type': 'color'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
    
    def clean(self):
        cleaned_data = super().clean()
        est_gagnant = cleaned_data.get('est_gagnant')
        est_perdant = cleaned_data.get('est_perdant')
        
        if est_gagnant and est_perdant:
            raise ValidationError(_("Un statut ne peut pas être à la fois gagnant et perdant"))
        
        return cleaned_data
class OpportuniteForm(forms.ModelForm):
    # Ajoutez le champ valeur_attendue comme champ calculé en lecture seule
    valeur_attendue = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}),
        label=_("Valeur attendue")
    )
    
    class Meta:
        model = Opportunite
        fields = [
            'client', 'nom', 'description', 'montant_estime', 
            'probabilite', 'statut', 'priorite', 'date_fermeture_prevue',
            'assigne_a', 'devis_lie'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'date_fermeture_prevue': forms.DateInput(attrs={'type': 'date'}),
            'devis_lie': forms.Select(attrs={'disabled': 'disabled'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        if self.entreprise:
            self.fields['client'].queryset = ClientCRM.objects.filter(entreprise=self.entreprise)
            self.fields['statut'].queryset = StatutOpportunite.objects.filter(entreprise=self.entreprise)
            self.fields['assigne_a'].queryset = User.objects.filter(entreprise=self.entreprise)
            self.fields['devis_lie'].queryset = Devis.objects.filter(entreprise=self.entreprise)
            
            # Rendre le champ devis_lie en lecture seule si déjà lié
            if self.instance and self.instance.devis_lie:
                self.fields['devis_lie'].disabled = True
                self.fields['devis_lie'].help_text = "Ce devis a été créé à partir de cette opportunité"


class TypeActiviteForm(forms.ModelForm):
    class Meta:
        model = TypeActivite
        fields = ['nom', 'description', 'duree_par_defaut', 'couleur']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'couleur': forms.TextInput(attrs={'type': 'color'}),
            'duree_par_defaut': forms.TextInput(attrs={
                'placeholder': 'HH:MM:SS (ex: 01:30:00 pour 1h30)'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)

            
class ActiviteForm(forms.ModelForm):
    clients = forms.ModelMultipleChoiceField(
        queryset=ClientCRM.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'select2'})
    )
    
    opportunites = forms.ModelMultipleChoiceField(
        queryset=Opportunite.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'select2'})
    )
    
    class Meta:
        model = Activite
        fields = [
            'type_activite', 'sujet', 'description', 'date_debut', 
            'date_echeance', 'statut', 'priorite', 'assigne_a',
            'clients', 'opportunites', 'rappel', 'date_rappel', 'resultat'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'resultat': forms.Textarea(attrs={'rows': 3}),
            'date_debut': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'date_echeance': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'date_rappel': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        if self.entreprise:
            self.fields['type_activite'].queryset = TypeActivite.objects.filter(entreprise=self.entreprise)
            self.fields['assigne_a'].queryset = User.objects.filter(entreprise=self.entreprise)
            self.fields['clients'].queryset = ClientCRM.objects.filter(entreprise=self.entreprise)
            self.fields['opportunites'].queryset = Opportunite.objects.filter(entreprise=self.entreprise)

class NoteClientForm(forms.ModelForm):
    class Meta:
        model = NoteClient
        fields = ['titre', 'contenu', 'est_important']
        widgets = {
            'contenu': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)

class ObjectifCommercialForm(forms.ModelForm):
    equipe = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'select2'})
    )
    
    class Meta:
        model = ObjectifCommercial
        fields = [
            'nom', 'description', 'type_objectif', 'valeur_cible',
            'periodicite', 'date_debut', 'date_fin', 'assigne_a', 'equipe'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'date_debut': forms.DateInput(attrs={'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        if self.entreprise:
            self.fields['assigne_a'].queryset = User.objects.filter(entreprise=self.entreprise)
            self.fields['equipe'].queryset = User.objects.filter(entreprise=self.entreprise)