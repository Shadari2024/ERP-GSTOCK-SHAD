from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import UtilisateurPersonnalise, ProfilUtilisateur
from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError
#from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth.models import Group, Permission
from datetime import timedelta


class ConnexionForm(forms.Form):
    username = forms.CharField(
        label="Nom d'utilisateur",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Nom d'utilisateur"})
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': "Mot de passe"})
    )




from parametres.models import Entreprise # <--- N'oubliez pas d'importer le modèle Entreprise

class UtilisateurForm(UserCreationForm):
    # Ajoutez le champ 'entreprise' explicitement ici
    # Il s'agit d'un ModelChoiceField qui affichera une liste déroulante des entreprises
    entreprise = forms.ModelChoiceField(
        queryset=Entreprise.objects.all(), # Récupère toutes les entreprises
        required=False, # Définissez à False si un utilisateur peut être créé sans entreprise (ex: Super-Admin)
        label=_("Entreprise associée"),
        widget=forms.Select(attrs={'class': 'form-control'}) # Pour le style Bootstrap
    )

    class Meta:
        model = UtilisateurPersonnalise
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'role',
            'telephone',
            'est_actif',
            'entreprise' # <--- AJOUTEZ LE CHAMP ICI
        ]
        # Les champs 'password1' et 'password2' sont automatiquement gérés par UserCreationForm.
        # Il n'est généralement pas nécessaire de les lister explicitement dans 'fields'
        # quand vous héritez de UserCreationForm, sauf si vous voulez les personnaliser.
        # Si vous les laissez, assurez-vous de ne pas avoir de conflit avec UserCreationForm.

        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'XX XXXX XXXX'
            }),
            'est_actif': forms.CheckboxInput(attrs={'class': 'form-check-input'})
            # Le widget pour 'entreprise' est déjà défini directement sur le ModelChoiceField ci-dessus,
            # donc pas besoin de le répéter ici.
        }

    def clean_telephone(self):
        telephone = self.cleaned_data['telephone']
        if telephone:
            number = telephone.replace(' ', '')
            if not number.isdigit():
                raise ValidationError(_('Le numéro de téléphone doit contenir uniquement des chiffres.'))
            if len(number) != 10:
                raise ValidationError(_('Le numéro de téléphone doit contenir 10 chiffres.'))
        return telephone

class ProfilForm(forms.ModelForm):
    class Meta:
        model = ProfilUtilisateur
        fields = [
            'photo',
            'signature',
            'signature_svg',
            'signature_date',
            'poste',
            'date_embauche',
            'notes'
        ]
        widgets = {
            'photo': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'signature': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'poste': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'date_embauche': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'signature_svg': forms.HiddenInput(),
            'signature_date': forms.HiddenInput()
        }

    def clean_photo(self):
        photo = self.cleaned_data.get('photo')
        if photo and photo.size > 24 * 1024 * 1024:
            raise ValidationError(_('La photo ne doit pas dépasser 2MB.'))
        return photo

    def clean_signature(self):
        signature = self.cleaned_data.get('signature')
        if signature and signature.size > 1 * 1024 * 1024:
            raise ValidationError(_('La signature ne doit pas dépasser 1MB.'))
        return signature


class SignatureForm(forms.ModelForm):
    DRAW = 'draw'
    UPLOAD = 'upload'
    METHOD_CHOICES = [
        (DRAW, 'Dessiner la signature'),
        (UPLOAD, 'Uploader une image'),
    ]

    method = forms.ChoiceField(
        choices=METHOD_CHOICES,
        widget=forms.RadioSelect,
        initial=DRAW
    )
    signature_image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'accept': 'image/*',
            'class': 'form-control',
            'style': 'display: none;'
        })
    )
    signature_data = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

    class Meta:
        model = ProfilUtilisateur
        fields = []

    def clean(self):
        cleaned_data = super().clean()
        method = cleaned_data.get('method')

        if method == self.UPLOAD and not cleaned_data.get('signature_image'):
            raise forms.ValidationError("Veuillez sélectionner une image à uploader.")
        elif method == self.DRAW and not cleaned_data.get('signature_data'):
            raise forms.ValidationError("Veuillez dessiner votre signature.")
        return cleaned_data

    def save(self, commit=True):
        profile = super().save(commit=False)
        method = self.cleaned_data.get('method')

        if method == self.UPLOAD:
            profile.signature = self.cleaned_data['signature_image']
            profile.signature_svg = None
        elif method == self.DRAW:
            profile.signature_svg = self.cleaned_data['signature_data']
            profile.signature = None

        profile.signature_date = timezone.now().date()

        if commit:
            profile.save()

        return profile


class GroupAdminForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Group
        fields = ('name', 'permissions')


from django import forms
from django.utils import timezone
from datetime import timedelta
from .models import UtilisateurPersonnalise  # Ajoutez cet import

class FiltreUtilisateurForm(forms.Form):
    STATUT_CHOICES = [
        ('', 'Tous les statuts'),
        ('actif', 'Actifs seulement'),
        ('inactif', 'Inactifs seulement'),
    ]
    
    TRI_CHOICES = [
        ('-date_joined', 'Plus récents'),
        ('date_joined', 'Plus anciens'),
        ('last_name', 'Nom (A-Z)'),
        ('-last_name', 'Nom (Z-A)'),
    ]
    
    statut = forms.ChoiceField(
        choices=STATUT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    role = forms.ChoiceField(
        choices=[],  # Initialisé vide, sera rempli dans __init__
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    recherche = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom, email, username...'
        })
    )
    
    date_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    tri = forms.ChoiceField(
        choices=TRI_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Utilisez ROLES au lieu de ROLE_CHOICES
        self.fields['role'].choices = [('', 'Tous les rôles')] + list(UtilisateurPersonnalise.ROLES)
        
        # Définir des dates par défaut (30 derniers jours)
        aujourd_hui = timezone.now().date()
        il_y_a_30_jours = aujourd_hui - timedelta(days=30)
        self.fields['date_debut'].initial = il_y_a_30_jours
        self.fields['date_fin'].initial = aujourd_hui