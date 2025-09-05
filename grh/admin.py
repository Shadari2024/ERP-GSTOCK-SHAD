from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Departement, Poste, Employe, Contrat, BulletinPaie, LigneBulletinPaie, Conge
from comptabilite.models import PlanComptableOHADA

class DepartementForm(forms.ModelForm):
    class Meta:
        model = Departement
        fields = ['code', 'nom', 'description', 'responsable', 'compte_comptable', 'actif']
        
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        if self.entreprise:
            self.fields['responsable'].queryset = Employe.objects.filter(entreprise=self.entreprise, statut='ACTIF')
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
        
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        if self.entreprise:
            self.fields['employe'].queryset = Employe.objects.filter(entreprise=self.entreprise)
            self.fields['poste'].queryset = Poste.objects.filter(entreprise=self.entreprise, actif=True)

class BulletinPaieForm(forms.ModelForm):
    class Meta:
        model = BulletinPaie
        fields = ['employe', 'contrat', 'periode', 'salaire_brut', 'total_cotisations', 
                 'salaire_net', 'net_a_payer', 'jours_travailles', 'heures_travaillees', 'fichier_bulletin']
        
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        if self.entreprise:
            self.fields['employe'].queryset = Employe.objects.filter(entreprise=self.entreprise)
            self.fields['contrat'].queryset = Contrat.objects.filter(entreprise=self.entreprise, statut='EN_COURS')

class LigneBulletinPaieForm(forms.ModelForm):
    class Meta:
        model = LigneBulletinPaie
        fields = ['type_ligne', 'libelle', 'montant', 'ordre']

LigneBulletinPaieFormSet = forms.inlineformset_factory(
    BulletinPaie, LigneBulletinPaie, form=LigneBulletinPaieForm,
    extra=1, can_delete=True, can_order=False
)

class CongeForm(forms.ModelForm):
    class Meta:
        model = Conge
        fields = ['employe', 'type_conge', 'date_debut', 'date_fin', 'nombre_jours', 'statut', 'motif']
        
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        if self.entreprise:
            self.fields['employe'].queryset = Employe.objects.filter(entreprise=self.entreprise)