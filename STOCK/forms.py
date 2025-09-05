from django import forms
from .models import *
from django import forms

from django import forms
from decimal import Decimal


        
from django import forms
from .models import Parametre, TauxChange

class DeviseForm(forms.ModelForm):
    devises_acceptees = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = Parametre
        fields = ['devise_principale', 'devises_acceptees', 'taux_change_auto']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Liste des devises courantes - peut être externalisée dans les paramètres
        DEVISE_CHOICES = [
            ('USD', 'Dollar US (USD)'),
            ('EUR', 'Euro (EUR)'),
            ('CDF', 'Franc Congolais (CDF)'),
            ('FC', 'Franc CFA (FC)'),
        ]
        self.fields['devises_acceptees'].choices = DEVISE_CHOICES
        self.fields['devise_principale'].choices = DEVISE_CHOICES

class TauxChangeForm(forms.ModelForm):
    class Meta:
        model = TauxChange
        fields = ['devise_source', 'devise_cible', 'taux']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        parametres = Parametre.objects.first()
        if parametres:
            devises = parametres.devises_acceptees + [parametres.devise_principale]
            self.fields['devise_source'].choices = [(d, d) for d in devises]
            self.fields['devise_cible'].choices = [(d, d) for d in devises]
    
    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('devise_source') == cleaned_data.get('devise_cible'):
            raise forms.ValidationError("Les devises source et cible doivent être différentes")
        return cleaned_data
    
    
    
    