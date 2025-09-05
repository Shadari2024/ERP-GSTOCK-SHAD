from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Departement, Poste, Employe, Contrat, BulletinPaie, LigneBulletinPaie, Conge,Presence
from comptabilite.models import PlanComptableOHADA
from django.forms import inlineformset_factory


class DepartementForm(forms.ModelForm):
    class Meta:
        model = Departement
        fields = ['code', 'nom', 'description', 'responsable', 'compte_comptable', 'actif']
        
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        if self.entreprise:
            # Filtrer les employés actifs de l'entreprise
            employes = Employe.objects.filter(entreprise=self.entreprise, statut='ACTIF')
            
            if employes.exists():
                self.fields['responsable'].queryset = employes
                self.fields['responsable'].empty_label = "Sélectionner un responsable"
            else:
                # S'il n'y a pas d'employés, désactiver le champ et ajouter un message d'aide
                self.fields['responsable'].widget = forms.HiddenInput()
                self.fields['responsable'].help_text = "Aucun employé disponible. Veuillez d'abord créer des employés."
                self.fields['responsable'].required = False
            
            self.fields['compte_comptable'].queryset = PlanComptableOHADA.objects.filter(entreprise=self.entreprise)

class PosteForm(forms.ModelForm):
    class Meta:
        model = Poste
        fields = ['code', 'intitule', 'departement', 'description', 'type_contrat', 'salaire_min', 'salaire_max', 'actif']
        
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        if self.entreprise:
            self.fields['departement'].queryset = Departement.objects.filter(entreprise=self.entreprise, actif=True)

class EmployeForm(forms.ModelForm):
    class Meta:
        model = Employe
        fields = ['matricule', 'nom', 'prenom', 'genre', 'date_naissance', 'email', 
                 'telephone', 'adresse', 'ville', 'code_postal', 'pays', 'date_embauche', 
                 'poste', 'statut', 'photo', 'cv']
        
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        if self.entreprise:
            self.fields['poste'].queryset = Poste.objects.filter(entreprise=self.entreprise, actif=True)


class ContratForm(forms.ModelForm):
    class Meta:
        model = Contrat
        fields = ['employe', 'reference', 'type_contrat', 'date_debut', 'date_fin', 
                 'poste', 'salaire_base', 'statut', 'duree_essai', 'date_fin_essai', 
                 'heures_semaine', 'jours_conges_an', 'fichier_contrat']
        widgets = {
            'date_debut': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_fin_essai': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        if self.entreprise:
            self.fields['employe'].queryset = Employe.objects.filter(entreprise=self.entreprise)
            self.fields['poste'].queryset = Poste.objects.filter(entreprise=self.entreprise, actif=True)
    
    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        date_fin_essai = cleaned_data.get('date_fin_essai')
        
        # Validation des dates
        if date_fin and date_debut and date_fin < date_debut:
            raise forms.ValidationError("La date de fin ne peut pas être antérieure à la date de début.")
        
        if date_fin_essai and date_debut and date_fin_essai < date_debut:
            raise forms.ValidationError("La date de fin d'essai ne peut pas être antérieure à la date de début.")
            
        return cleaned_data

class PresenceForm(forms.ModelForm):
    class Meta:
        model = Presence
        fields = ['employe', 'date', 'heure_arrivee', 'heure_depart', 'statut', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'heure_arrivee': forms.TimeInput(attrs={'type': 'time'}),
            'heure_depart': forms.TimeInput(attrs={'type': 'time'}),
        }
        
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        if self.entreprise:
            self.fields['employe'].queryset = Employe.objects.filter(entreprise=self.entreprise, statut='ACTIF')

class ImportPresenceForm(forms.Form):
    fichier_csv = forms.FileField(label="Fichier CSV")
    mois = forms.CharField(max_length=7, widget=forms.TextInput(attrs={'type': 'month'}))
    
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)



class BulletinPaieForm(forms.ModelForm):
    class Meta:
        model = BulletinPaie
        fields = ['employe', 'contrat', 'periode', 'salaire_brut', 'total_cotisations', 
                 'salaire_net', 'net_a_payer', 'jours_travailles', 'heures_travaillees', 'fichier_bulletin']
        widgets = {
            'periode': forms.TextInput(attrs={'type': 'month', 'class': 'form-control'}),
            'salaire_brut': forms.NumberInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext'}),
            'total_cotisations': forms.NumberInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext'}),
            'salaire_net': forms.NumberInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext'}),
            'net_a_payer': forms.NumberInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext'}),
            'jours_travailles': forms.NumberInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext'}),
            'heures_travaillees': forms.NumberInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext'}),
        }
        
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        if self.entreprise:
            self.fields['employe'].queryset = Employe.objects.filter(entreprise=self.entreprise)
            self.fields['contrat'].queryset = Contrat.objects.filter(entreprise=self.entreprise, statut='EN_COURS')
            
            # Rendre le contrat obligatoire seulement si l'employé est sélectionné
            self.fields['contrat'].required = False
            
            # Ajouter des classes pour le JavaScript
            self.fields['employe'].widget.attrs.update({'class': 'employe-select form-control', 'onchange': 'calculerPaie()'})
            self.fields['periode'].widget.attrs.update({'class': 'periode-select form-control', 'onchange': 'calculerPaie()'})
            self.fields['contrat'].widget.attrs.update({'class': 'form-control'})
    
    def clean_periode(self):
        periode = self.cleaned_data.get('periode')
        # Validation du format YYYY-MM
        if periode and len(periode) != 7:
            raise forms.ValidationError("Le format de période doit être YYYY-MM (ex: 2025-09)")
        return periode
class LigneBulletinPaieForm(forms.ModelForm):
    class Meta:
        model = LigneBulletinPaie
        fields = ['type_ligne', 'libelle', 'montant', 'ordre']

# Définition du FormSet
LigneBulletinPaieFormSet = inlineformset_factory(
    BulletinPaie, 
    LigneBulletinPaie, 
    form=LigneBulletinPaieForm,
    extra=1, 
    can_delete=True, 
    can_order=False
)

class CongeForm(forms.ModelForm):
    class Meta:
        model = Conge
        fields = ['employe', 'type_conge', 'date_debut', 'date_fin', 'nombre_jours', 'statut', 'motif']
        widgets = {
            'date_debut': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'motif': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
        
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        if self.entreprise:
            self.fields['employe'].queryset = Employe.objects.filter(entreprise=self.entreprise)
    
    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        
        if date_fin and date_debut and date_fin < date_debut:
            raise forms.ValidationError("La date de fin ne peut pas être antérieure à la date de début.")
        
        return cleaned_data