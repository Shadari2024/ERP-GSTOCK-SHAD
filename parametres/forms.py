from django import forms
from django.core.exceptions import ValidationError
from .models import *
class EntrepriseForm(forms.ModelForm):
    class Meta:
        model = Entreprise
        fields = [
            'nom', 'slogan', 'adresse', 'telephone', 'email',
            'site_web', 'domaine', 'logo', 'statut', 'active',
            'plan_tarification', 'date_debut_abonnement',
            'date_fin_abonnement', 'numero_fiscal',
            'taux_tva_defaut' # <-- Add the new VAT field here
        ]
        widgets = {
            'date_debut_abonnement': forms.DateInput(attrs={'type': 'date'}),
            'date_fin_abonnement': forms.DateInput(attrs={'type': 'date'}),
            'adresse': forms.Textarea(attrs={'rows': 3}),
            # You might want to add a widget for taux_tva_defaut if you need specific styling or type.
            # For example, if you want a number input with a specific step:
            # 'taux_tva_defaut': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['plan_tarification'].queryset = PlanTarification.objects.all()
        self.fields['statut'].widget.attrs.update({'class': 'form-select'})

        # Optional: Add Bootstrap classes to new fields if not handled globally
        # if 'taux_tva_defaut' in self.fields:
        #     self.fields['taux_tva_defaut'].widget.attrs.update({'class': 'form-control'})

class DeviseForm(forms.ModelForm):
    class Meta:
        model = Devise
        fields = '__all__'

    def clean_code(self):
        code = self.cleaned_data.get('code')
        return code.upper()

class TauxChangeForm(forms.ModelForm):
    class Meta:
        model = TauxChange
        fields = '__all__'
        widgets = {
            'date_application': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        # Extraire l'argument devises avant d'appeler le parent
        devises = kwargs.pop('devises', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les choix si devises est fourni
        if devises is not None:
            self.fields['devise_source'].queryset = devises
            self.fields['devise_cible'].queryset = devises

class ParametreDocumentForm(forms.ModelForm):
    class Meta:
        model = ParametreDocument
        fields = '__all__'
        widgets = {
            'entreprise': forms.HiddenInput(),
        }

class ConfigurationSAASForm(forms.ModelForm):
    class Meta:
        model = ConfigurationSAAS
        fields = '__all__'
        widgets = {
            'modules_actifs': forms.CheckboxSelectMultiple(),
        }
# parametres/forms.py


from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
from django.core.exceptions import ValidationError
from .models import Abonnement, Entreprise, PlanTarification
import logging

logger = logging.getLogger(__name__)

class AbonnementForm(forms.ModelForm):
    class Meta:
        model = Abonnement
        fields = ['entreprise', 'plan_actuel', 'date_debut', 'date_fin',
                 'montant_paye', 'est_actif', 'prochain_paiement',
                 'methode_paiement', 'id_abonnement_paiement']
        
        widgets = {
            'plan_actuel': forms.Select(attrs={
                'class': 'form-control',
                'data-bs-toggle': 'tooltip',
                'title': _('Sélectionnez le plan tarifaire')
            }),
            'date_debut': forms.DateTimeInput(attrs={
                'class': 'form-control datetimepicker',
                'type': 'datetime-local'
            }),
            'date_fin': forms.DateTimeInput(attrs={
                'class': 'form-control datetimepicker',
                'type': 'datetime-local',
                'placeholder': _('Laissez vide pour illimité')
            }),
            'prochain_paiement': forms.DateTimeInput(attrs={
                'class': 'form-control datetimepicker',
                'type': 'datetime-local'
            }),
            'montant_paye': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'est_actif': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'checked': 'checked'
            }),
            'methode_paiement': forms.Select(attrs={
                'class': 'form-control'
            }),
            'id_abonnement_paiement': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('ID fourni par le processeur de paiement')
            }),
        }
        
        labels = {
            'plan_actuel': _("Plan tarifaire"),
            'date_debut': _("Date de début"),
            'date_fin': _("Date de fin (optionnel)"),
            'prochain_paiement': _("Prochain paiement"),
            'montant_paye': _("Montant payé (€)"),
            'est_actif': _("Activer immédiatement"),
            'methode_paiement': _("Méthode de paiement"),
            'id_abonnement_paiement': _("Référence paiement"),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        
        # Initialisation sécurisée de l'instance avant le super()
        if 'instance' not in kwargs:
            kwargs['instance'] = self._meta.model()
            
        super().__init__(*args, **kwargs)

        # Configuration initiale automatique
        self.set_initial_values()
        self.configure_field_access()
        self.setup_querysets()

        # Ajout de classes CSS supplémentaires
        for field in self.fields.values():
            field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-control-sm'

    def set_initial_values(self):
        """Définit les valeurs initiales automatiques"""
        if not self.instance.pk:  # Nouvel abonnement seulement
            self.initial.setdefault('date_debut', timezone.now())
            self.initial.setdefault('est_actif', True)

            # Définir la date de fin selon le plan sélectionné
            if 'plan_actuel' in self.initial and self.initial['plan_actuel']:
                try:
                    plan = PlanTarification.objects.get(pk=self.initial['plan_actuel'])
                    if hasattr(plan, 'duree_mois') and plan.duree_mois:
                        self.initial['date_fin'] = timezone.now() + timedelta(days=plan.duree_mois*30)
                except (PlanTarification.DoesNotExist, AttributeError) as e:
                    logger.debug(f"Erreur initialisation date fin: {str(e)}")

    def configure_field_access(self):
        """Configure les droits d'accès aux champs selon le type d'utilisateur"""
        if not self.request:
            return

        # Gestion du champ entreprise
        if not self.request.user.is_superuser:
            self.fields['entreprise'].widget = forms.HiddenInput()
            if hasattr(self.request.user, 'entreprise') and self.request.user.entreprise:
                self.initial['entreprise'] = self.request.user.entreprise
            elif hasattr(self.request, 'current_entreprise') and self.request.current_entreprise:
                self.initial['entreprise'] = self.request.current_entreprise
        else:
            self.fields['entreprise'].queryset = Entreprise.objects.all()
            if hasattr(self.request, 'current_entreprise') and self.request.current_entreprise:
                self.initial['entreprise'] = self.request.current_entreprise

        # Désactiver certains champs en édition
        if self.instance and self.instance.pk:
            self.fields['entreprise'].disabled = True
            self.fields['plan_actuel'].disabled = True

    def setup_querysets(self):
        """Configure les querysets pour les champs relationnels"""
        try:
            # Vérifie si le modèle PlanTarification a le champ 'est_actif'
            if hasattr(PlanTarification, 'est_actif'):
                self.fields['plan_actuel'].queryset = PlanTarification.objects.filter(est_actif=True)
            else:
                self.fields['plan_actuel'].queryset = PlanTarification.objects.all()
        except Exception as e:
            logger.error(f"Erreur configuration queryset plan tarifaire: {str(e)}")
            self.fields['plan_actuel'].queryset = PlanTarification.objects.none()

    def clean(self):
        cleaned_data = super().clean()

        # Validation des dates
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')

        if date_debut and date_fin and date_fin < date_debut:
            self.add_error('date_fin', _("La date de fin ne peut pas être antérieure à la date de début."))

        # Validation du montant - version robuste
        montant = cleaned_data.get('montant_paye')
        plan = cleaned_data.get('plan_actuel')

        if montant is not None and plan:
            try:
                # Gestion des différents noms de champ possibles pour le prix
                prix_plan = getattr(plan, 'prix_mensuel', None) or getattr(plan, 'prix', 0)

                if montant < prix_plan:
                    self.add_error('montant_paye',
                                 _("Le montant payé ne peut pas être inférieur au prix du plan ({} €).").format(prix_plan))
            except Exception as e:
                logger.error(f"Erreur validation prix: {str(e)}")
                self.add_error(None, _("Erreur de validation du prix du plan"))

        return cleaned_data

    def save(self, commit=True):
        try:
            # Vérification que l'instance existe avant sauvegarde
            if not hasattr(self, 'instance') or self.instance is None:
                self.instance = self._meta.model()

            instance = super().save(commit=False)

            # Nouvel abonnement - configuration automatique
            if not instance.pk:
                instance.est_actif = True

            # Si paiement complet, définir la date de prochain paiement
            if instance.montant_paye is not None and instance.plan_actuel:
                try:
                    # Gestion des différents noms de champ possibles
                    prix_plan = getattr(instance.plan_actuel, 'prix_mensuel', None) or getattr(instance.plan_actuel, 'prix', 0)
                    duree = getattr(instance.plan_actuel, 'duree_mois', None)

                    if instance.montant_paye >= prix_plan and duree and instance.date_debut:
                        instance.prochain_paiement = instance.date_debut + timedelta(days=duree*30)
                except Exception as e:
                    logger.error(f"Erreur calcul prochain paiement: {str(e)}")

            if commit:
                instance.save()
                self.save_m2m()

            return instance
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de l'abonnement: {str(e)}", exc_info=True)
            raise ValidationError(_("Une erreur est survenue lors de la création de l'abonnement. Veuillez réessayer."))
        
# forms.py
class PlanTarificationForm(forms.ModelForm):
    class Meta:
        model = PlanTarification
        fields = '__all__'
        widgets = {
            'limites': forms.Textarea(attrs={'rows': 3}),
            'prix_mensuel': forms.NumberInput(attrs={'step': '0.01'}),
            'modules_inclus': forms.SelectMultiple(attrs={
                'class': 'selectpicker',
                'data-live-search': 'true',
                'title': 'Sélectionnez les modules inclus'
            }),
            'modules_optionnels': forms.SelectMultiple(attrs={
                'class': 'selectpicker',
                'data-live-search': 'true',
                'title': 'Sélectionnez les modules optionnels'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configuration de base des champs
        self.fields['niveau'].widget.attrs.update({'class': 'form-select'})
        self.fields['prix_mensuel'].widget.attrs.update({'min': '0'})
        self.fields['utilisateurs_inclus'].widget.attrs.update({'min': '1'})
        self.fields['stockage_go'].widget.attrs.update({'min': '1'})
        
        # Gestion des champs ManyToMany s'ils existent
        if 'modules_inclus' in self.fields:
            self.fields['modules_inclus'].queryset = Module.objects.filter(actif_par_defaut=True)
            self.fields['modules_inclus'].required = False
            
        if 'modules_optionnels' in self.fields:
            self.fields['modules_optionnels'].queryset = Module.objects.filter(actif_par_defaut=True)
            self.fields['modules_optionnels'].required = False
        
        # Gestion du champ est_actif
        if 'est_actif' in self.fields:
            self.fields['est_actif'].initial = True
            
        # Style uniforme pour tous les champs
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                if isinstance(field.widget, forms.SelectMultiple):
                    field.widget.attrs['class'] = 'form-control selectpicker'
                else:
                    field.widget.attrs['class'] = 'form-control'

    def clean(self):
        cleaned_data = super().clean()
        
        # Validation seulement si les champs existent
        if 'modules_inclus' in cleaned_data and 'modules_optionnels' in cleaned_data:
            modules_inclus = cleaned_data.get('modules_inclus', [])
            modules_optionnels = cleaned_data.get('modules_optionnels', [])
            
            # Vérification des doublons
            doublons = set(modules_inclus) & set(modules_optionnels)
            if doublons:
                noms = [m.nom for m in doublons]
                raise ValidationError(
                    _("Les modules suivants ne peuvent pas être à la fois inclus et optionnels: %(modules)s"),
                    code='invalid',
                    params={'modules': ', '.join(noms)}
                )
        
        return cleaned_data
# parametres/forms.py

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Entreprise # Importez le modèle Entreprise

class EntrepriseSelectForm(forms.Form):
    entreprise = forms.ModelChoiceField(
        queryset=Entreprise.objects.all(),
        label=_("Sélectionnez votre entreprise"),
        empty_label=_("--- Choisissez une entreprise ---"),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    

#module

class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_code(self):
        code = self.cleaned_data['code']
        
        # Vérifier que le code est en majuscules
        if not code.isupper():
            raise ValidationError("Le code doit être en majuscules.")
        
        # Vérifier que le code correspond à une app installée
        installed_apps = [app.split('.')[0] for app in settings.INSTALLED_APPS]
        if code not in installed_apps:
            raise ValidationError(
                f"Ce code module doit correspondre à une application installée. "
                f"Applications disponibles: {', '.join(installed_apps)}"
            )
        
        return code

class ModuleEntrepriseForm(forms.ModelForm):
    class Meta:
        model = ModuleEntreprise
        fields = ['entreprise', 'est_actif']

class DependanceModuleForm(forms.ModelForm):
    class Meta:
        model = DependanceModule
        fields = ['module_principal', 'module_dependance', 'obligatoire']

    def clean(self):
        cleaned_data = super().clean()
        module_principal = cleaned_data.get('module_principal')
        module_dependance = cleaned_data.get('module_dependance')

        if module_principal and module_dependance and module_principal == module_dependance:
            raise ValidationError("Un module ne peut pas dépendre de lui-même.")

        return cleaned_data