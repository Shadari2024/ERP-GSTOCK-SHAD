from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Promotion, PromotionLigne
from STOCK.models import Produit

class PromotionForm(forms.ModelForm):
    class Meta:
        model = Promotion
        fields = ['nom', 'description', 'type_promotion', 'valeur', 'date_debut', 'date_fin']
        widgets = {
            'date_debut': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'date_fin': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'type_promotion': forms.Select(attrs={'class': 'form-control'}),
            'valeur': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk:
            self.fields['type_promotion'].disabled = True
    
    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        type_promotion = cleaned_data.get('type_promotion')
        valeur = cleaned_data.get('valeur')
        
        if date_debut and date_fin and date_debut >= date_fin:
            raise forms.ValidationError(_('La date de fin doit être postérieure à la date de début.'))
        
        if type_promotion in ['pourcentage', 'montant_fixe', 'prix_specifique'] and valeur is None:
            raise forms.ValidationError(_('Une valeur est requise pour ce type de promotion.'))
        
        return cleaned_data

class PromotionLigneForm(forms.ModelForm):
    class Meta:
        model = PromotionLigne
        fields = ['produit', 'valeur_secondaire', 'quantite_min']
        widgets = {
            'produit': forms.Select(attrs={'class': 'form-control select2'}),
            'valeur_secondaire': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quantite_min': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    # La validation de la valeur secondaire est déplacée dans la vue pour éviter l'erreur.
    # Ne pas implémenter la méthode clean ici.

PromotionLigneFormSet = forms.inlineformset_factory(
    Promotion, 
    PromotionLigne, 
    form=PromotionLigneForm,
    extra=1,
    can_delete=True
)