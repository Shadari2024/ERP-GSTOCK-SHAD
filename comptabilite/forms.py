from django import forms
from django.utils.translation import gettext_lazy as _
from .models import PlanComptableOHADA, JournalComptable, EcritureComptable, LigneEcriture, CompteAuxiliaire
from django.forms import inlineformset_factory
from django.forms.models import BaseInlineFormSet
class PlanComptableForm(forms.ModelForm):
    class Meta:
        model = PlanComptableOHADA
        fields = ['classe', 'numero', 'intitule', 'description', 'type_compte']
        # NE PAS utiliser exclude = ['entreprise'] car cela empêcherait
        # l'assignation de l'entreprise via form.save(commit=False)
    
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        # Validation des numéros de compte selon le plan OHADA
        self.fields['numero'].help_text = _("Format: Classe (1 chiffre) + Sous-classe (2 chiffres) + Numéro (2 chiffres). Ex: 40101")

    def clean_numero(self):
        numero = self.cleaned_data['numero']
        classe = self.cleaned_data.get('classe')
        
        # Vérifier que le numéro commence par la classe
        if classe and not numero.startswith(classe):
            raise forms.ValidationError(_("Le numéro de compte doit commencer par le numéro de classe."))
        
        # Vérifier l'unicité du numéro pour l'entreprise
        if self.entreprise and PlanComptableOHADA.objects.filter(
            numero=numero, 
            entreprise=self.entreprise
        ).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError(_("Ce numéro de compte existe déjà pour cette entreprise."))
        
        return numero
    
class JournalComptableForm(forms.ModelForm):
    class Meta:
        model = JournalComptable
        fields = ['code', 'intitule', 'type_journal', 'actif']
    
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)

    def clean_code(self):
        code = self.cleaned_data['code']
        
        # Vérifier l'unicité du code pour l'entreprise
        if self.entreprise and JournalComptable.objects.filter(
            code=code, 
            entreprise=self.entreprise
        ).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError(_("Ce code de journal existe déjà pour cette entreprise."))
        
        return code

class EcritureComptableForm(forms.ModelForm):
    class Meta:
        model = EcritureComptable
        fields = ['journal', 'date_ecriture', 'date_comptable', 'libelle', 'piece_justificative', 
                 'montant_devise_etrangere', 'code_devise_etrangere', 'taux_change']
        # Exclure montant_devise car il sera calculé automatiquement
        widgets = {
            'date_ecriture': forms.DateInput(attrs={'type': 'date'}),
            'date_comptable': forms.DateInput(attrs={'type': 'date'}),
            'libelle': forms.TextInput(attrs={'placeholder': "Libellé de l'écriture"}),
        }
    
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        if self.entreprise:
            # Filtrer les journaux par entreprise
            self.fields['journal'].queryset = JournalComptable.objects.filter(
                entreprise=self.entreprise, 
                actif=True
            )
        
        # Rendre certains champs optionnels
        self.fields['montant_devise_etrangere'].required = False
        self.fields['code_devise_etrangere'].required = False
        self.fields['taux_change'].required = False

    def clean(self):
        cleaned_data = super().clean()
        montant_devise_etrangere = cleaned_data.get('montant_devise_etrangere')
        code_devise_etrangere = cleaned_data.get('code_devise_etrangere')
        taux_change = cleaned_data.get('taux_change')
        
        # Validation cohérente des champs de devise étrangère
        if any([montant_devise_etrangere, code_devise_etrangere, taux_change]):
            if not all([montant_devise_etrangere, code_devise_etrangere, taux_change]):
                raise forms.ValidationError(_("Si vous renseignez un montant en devise étrangère, vous devez également renseigner le code devise et le taux de change."))
        
        return cleaned_data

class LigneEcritureForm(forms.ModelForm):
    class Meta:
        model = LigneEcriture
        fields = ['compte', 'libelle', 'debit', 'credit']
        widgets = {
            'debit': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
            'credit': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        if self.entreprise:
            # Filtrer les comptes par entreprise
            self.fields['compte'].queryset = PlanComptableOHADA.objects.filter(entreprise=self.entreprise)
    
    def clean(self):
        cleaned_data = super().clean()
        debit = cleaned_data.get('debit', 0)
        credit = cleaned_data.get('credit', 0)
        
        # Une ligne ne peut pas avoir à la fois un débit et un crédit
        if debit and credit:
            raise forms.ValidationError(_("Une ligne ne peut pas avoir à la fois un débit et un crédit."))
        
        # Une ligne doit avoir soit un débit, soit un crédit
        if not debit and not credit:
            raise forms.ValidationError(_("Une ligne doit avoir soit un débit, soit un crédit."))
        
        return cleaned_data
    
class BaseLigneEcritureFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)

    def _construct_form(self, i, **kwargs):
        kwargs['entreprise'] = self.entreprise
        return super()._construct_form(i, **kwargs)

# Formset pour les lignes d'écriture
LigneEcritureFormSet = inlineformset_factory(
    EcritureComptable,
    LigneEcriture,
    form=LigneEcritureForm,
    formset=BaseLigneEcritureFormSet,
    extra=2,
    can_delete=True,
    min_num=2,  # Au moins 2 lignes (une au débit, une au crédit)
    validate_min=True,
)
class CompteAuxiliaireForm(forms.ModelForm):
    class Meta:
        model = CompteAuxiliaire
        fields = ['code', 'intitule', 'type_compte', 'compte_general', 'actif']
    
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        if self.entreprise:
            # Filtrer les comptes généraux par entreprise
            self.fields['compte_general'].queryset = PlanComptableOHADA.objects.filter(entreprise=self.entreprise)
            
            # Adapter les choix en fonction du type de compte
            type_compte = self.data.get('type_compte') if self.data else self.instance.type_compte if self.instance else None
            
            if type_compte == 'client':
                self.fields['compte_general'].queryset = self.fields['compte_general'].queryset.filter(numero__startswith='411')
            elif type_compte == 'fournisseur':
                self.fields['compte_general'].queryset = self.fields['compte_general'].queryset.filter(numero__startswith='401')

    def clean_code(self):
        code = self.cleaned_data['code']
        
        # Vérifier l'unicité du code pour l'entreprise
        if self.entreprise and CompteAuxiliaire.objects.filter(
            code=code, 
            entreprise=self.entreprise
        ).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError("Ce code de compte auxiliaire existe déjà pour cette entreprise.")
        
        return code

    def clean(self):
        cleaned_data = super().clean()
        type_compte = cleaned_data.get('type_compte')
        compte_general = cleaned_data.get('compte_general')
        
        # Validation de la cohérence entre le type de compte et le compte général
        if type_compte and compte_general:
            if type_compte == 'client' and not compte_general.numero.startswith('411'):
                raise forms.ValidationError("Pour un compte client, le compte général doit commencer par 411.")
            elif type_compte == 'fournisseur' and not compte_general.numero.startswith('401'):
                raise forms.ValidationError("Pour un compte fournisseur, le compte général doit commencer par 401.")
            elif type_compte == 'autre' and not (compte_general.numero.startswith('40') or compte_general.numero.startswith('41')):
                raise forms.ValidationError("Pour un compte autre, le compte général doit commencer par 40 ou 41.")
        
        return cleaned_data