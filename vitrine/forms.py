from django import forms
from django.utils.translation import gettext_lazy as _
from .models import DemandeDemo

class DemandeDemoForm(forms.ModelForm):
    class Meta:
        model = DemandeDemo
        fields = ['nom', 'entreprise', 'email', 'telephone', 'message']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Votre nom complet')}),
            'entreprise': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Nom de votre entreprise')}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': _('Votre adresse email')}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Votre numéro de téléphone')}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': _('Décrivez vos besoins...')}),
        }
        labels = {
            'nom': _('Nom complet'),
            'entreprise': _('Entreprise'),
            'email': _('Email'),
            'telephone': _('Téléphone'),
            'message': _('Message'),
        }