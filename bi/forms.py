from django import forms
from django.utils.translation import gettext_lazy as _
from .models import KPI, Report, DataExport, DataImport, AIIntegration
from parametres.models import ConfigurationSAAS

class KPIForm(forms.ModelForm):
    class Meta:
        model = KPI
        fields = ['nom', 'code', 'description', 'type_kpi', 'formule', 'periodicite', 
                 'unite', 'cible', 'seuil_alerte', 'module_lie', 'actif']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'formule': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ex: ventes__montant_total / ventes__nombre_commandes'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
    
    def clean_code(self):
        code = self.cleaned_data['code']
        if self.entreprise and KPI.objects.filter(code=code, entreprise=self.entreprise).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(_("Ce code KPI existe déjà pour cette entreprise"))
        return code

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['nom', 'description', 'type_rapport', 'requete_sql', 'parametres', 
                 'colonnes', 'options_graphique', 'public']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'requete_sql': forms.Textarea(attrs={'rows': 5, 'class': 'sql-editor'}),
            'parametres': forms.Textarea(attrs={'rows': 3, 'class': 'json-editor'}),
            'colonnes': forms.Textarea(attrs={'rows': 3, 'class': 'json-editor'}),
            'options_graphique': forms.Textarea(attrs={'rows': 3, 'class': 'json-editor'}),
        }

class ExportForm(forms.ModelForm):
    format_export = forms.ChoiceField(
        choices=DataExport.FORMAT_CHOICES,
        widget=forms.RadioSelect,
        initial='excel'
    )
    date_debut = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    date_fin = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    
    class Meta:
        model = DataExport
        fields = ['nom_fichier', 'format_export']

class ImportForm(forms.ModelForm):
    fichier = forms.FileField(label=_("Fichier à importer"))
    
    class Meta:
        model = DataImport
        fields = ['type_import', 'nom_fichier']

class AIForm(forms.ModelForm):
    class Meta:
        model = AIIntegration
        fields = ['nom', 'type_ia', 'modele_ia', 'parametres', 'actif']
        widgets = {
            'parametres': forms.Textarea(attrs={'rows': 3, 'class': 'json-editor'}),
        }