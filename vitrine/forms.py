# forms.py
from django import forms
from .models import DemandeDemo
import re

class DemandeDemoForm(forms.ModelForm):
    class Meta:
        model = DemandeDemo
        fields = ['nom', 'entreprise', 'email', 'telephone', 'message']
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Votre nom complet'
            }),
            'entreprise': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de votre entreprise'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'votre@email.com'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+243 XX XXX XXXX'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Décrivez vos besoins spécifiques...',
                'rows': 4
            }),
        }
        labels = {
            'nom': 'Nom complet',
            'entreprise': 'Entreprise',
            'email': 'Adresse email',
            'telephone': 'Téléphone',
            'message': 'Message additionnel'
        }
    
    def clean_telephone(self):
        telephone = self.cleaned_data.get('telephone')
        # Validation basique du numéro de téléphone
        if telephone:
            # Supprimer les espaces et caractères spéciaux
            telephone = re.sub(r'[^\d+]', '', telephone)
            if len(telephone) < 8:
                raise forms.ValidationError("Numéro de téléphone invalide")
        return telephone