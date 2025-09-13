from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import *
from STOCK.models import Produit, Client

class EmailRecipientForm(forms.Form):
    recipient_email = forms.EmailField(
        label="Adresse e-mail du destinataire",
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'}) # Default to text input
    )
    
    def __init__(self, *args, **kwargs):
        client_id = kwargs.pop('client_id', None)
        super().__init__(*args, **kwargs)

        # Get the client's main email if a client_id is provided
        initial_email = None
        if client_id:
            try:
                client = Client.objects.get(id=client_id)
                if client.email:
                    initial_email = client.email
            except Client.DoesNotExist:
                pass # Client not found, no initial email

        # Set the initial value for the email field
        if initial_email:
            self.fields['recipient_email'].initial = initial_email
            # You could also consider making it a ChoiceField if you want to explicitly show it as a pre-selected option
            # but for a single primary email, a pre-filled EmailInput is simpler.
        else:
            self.fields['recipient_email'].help_text = "Veuillez saisir l'adresse e-mail du destinataire."

class DevisForm(forms.ModelForm):
    client = forms.ModelChoiceField(
        queryset=Client.objects.none(), 
        label="Client",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = Devis
        fields = ['client', 'date', 'echeance', 'remise', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'echeance': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'remise': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        if self.entreprise:
            self.fields['client'].queryset = Client.objects.filter(
                entreprise=self.entreprise
            ).order_by('nom') 

class LigneDevisForm(forms.ModelForm):
    produit = forms.ModelChoiceField(
        queryset=Produit.objects.none(), 
        label="Produit",
        widget=forms.Select(attrs={
            'class': 'form-select produit-select',
            'data-url': '/ventes/get_prix_produit/'  # URL pour récupérer le prix
        })
    )
    
    class Meta:
        model = LigneDevis
        fields = ['produit', 'quantite', 'prix_unitaire', 'taux_tva']
        widgets = {
            'quantite': forms.NumberInput(attrs={
                'class': 'form-control quantite-input',
                'min': '0.01',
                'step': '0.01'
            }),
            'prix_unitaire': forms.NumberInput(attrs={
                'class': 'form-control prix-unitaire-input',
                'readonly': 'readonly',  # Rendre en lecture seule
                'step': '0.01'
            }),
            'taux_tva': forms.NumberInput(attrs={
                'class': 'form-control taux-tva-input',
                'min': '0',
                'max': '100',
                'step': '0.1'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        if self.entreprise:
            self.fields['produit'].queryset = Produit.objects.filter(
                entreprise=self.entreprise,
                actif=True  # Seulement les produits actifs
            ).order_by('libelle')

class BaseLigneDevisFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        if self.entreprise: 
            kwargs['entreprise'] = self.entreprise
        return kwargs

LigneDevisFormSet = inlineformset_factory(
    Devis,
    LigneDevis,
    form=LigneDevisForm,
    formset=BaseLigneDevisFormSet, 
    extra=1,
    can_delete=True
)

# ventes/forms.py
from django import forms
from django.contrib.auth import get_user_model
from .models import PointDeVente

User = get_user_model()

class PointDeVenteForm(forms.ModelForm):
    class Meta:
        model = PointDeVente
        fields = ['code', 'nom', 'adresse', 'actif']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        # Ajouter les champs de sélection manuellement
        self.fields['responsable'] = forms.ModelChoiceField(
            queryset=User.objects.none(),
            widget=forms.Select(attrs={'class': 'form-control'}),
            required=False,
            label="Responsable principal"
        )
        
        self.fields['caissiers'] = forms.ModelMultipleChoiceField(
            queryset=User.objects.none(),
            widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
            required=False,
            label="Caissiers assignés"
        )

        if self.entreprise:
            # Filtrer les utilisateurs
            caissiers_queryset = User.objects.filter(
                entreprise=self.entreprise,
                role='CAISSIER',
                est_actif=True
            )
            
            self.fields['responsable'].queryset = caissiers_queryset
            self.fields['caissiers'].queryset = caissiers_queryset


class SessionPOSForm(forms.ModelForm):
    """
    Formulaire pour l'ouverture d'une Session de Point de Vente.
    """
    class Meta:
        model = SessionPOS
        fields = ['fonds_ouverture']


class VentePOSForm(forms.ModelForm):
    client = forms.ModelChoiceField(
        queryset=Client.objects.none(),
        required=False,
        label=("Client"),
        widget=forms.Select(attrs={'class': 'form-select select2'})
    )

    class Meta:
        model = VentePOS
        fields = ['client', 'remise', 'notes']
        widgets = {
            'remise': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }
   
    def __init__(self, *args, **kwargs):
        entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)

        if entreprise:
            self.fields['client'].queryset = Client.objects.filter(
                entreprise=entreprise
            ).order_by('nom')

class LigneVentePOSForm(forms.ModelForm):
    produit = forms.ModelChoiceField(
        queryset=Produit.objects.none(),
        label=("Produit"),
        widget=forms.Select(attrs={'class': 'form-select select2-produit'})
    )
   
    class Meta:
        model = LigneVentePOS
        fields = ['produit', 'quantite', 'prix_unitaire', 'taux_tva']
        widgets = {
            'quantite': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01', 'class': 'form-control quantite-input'}),
            'prix_unitaire': forms.NumberInput(attrs={'min': '0', 'step': '0.01', 'class': 'form-control prix-input'}),
           
        }
       
    def __init__(self, *args, **kwargs):
        entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
       
        if entreprise:
            produits = Produit.objects.filter(
                entreprise=entreprise,
                actif=True
            ).order_by('nom')
           
            if produits.exists():
                self.fields['produit'].queryset = produits
   
    def clean(self):
        cleaned_data = super().clean()
        produit = cleaned_data.get('produit')
        quantite = cleaned_data.get('quantite', 0)
       
        if produit and quantite:
            if quantite <= 0:
                raise forms.ValidationError(_("La quantité doit être supérieure à zéro."))
           
            # Vérifier le stock
            if produit.stock < quantite:
                raise forms.ValidationError(
                    _(f"Stock insuffisant. Disponible: {produit.stock}")
                )
       
        return cleaned_data

class LigneVentePOSFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
   
    def _construct_form(self, i, **kwargs):
        kwargs['entreprise'] = self.entreprise
        return super()._construct_form(i, **kwargs)
    
    
LigneVentePOSFormSet = inlineformset_factory(
    VentePOS,
    LigneVentePOS,
    form=LigneVentePOSForm,
    formset=LigneVentePOSFormSet,
    fields=['produit', 'quantite', 'prix_unitaire'],
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True
)

class PaiementPOSForm(forms.ModelForm):
    class Meta:
        model = PaiementPOS
        fields = ['montant', 'mode_paiement', 'reference']
        widgets = {
            'mode_paiement': forms.Select(attrs={'class': 'form-select'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': 0.01}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
        }
   
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['montant'].label = _("Montant à payer")
        self.fields['mode_paiement'].label = _("Mode de paiement")
        self.fields['reference'].label = _("Référence (optionnel)")
        
# Commande
# NEW FORM FOR STATUS UPDATE
class CommandeStatutForm(forms.ModelForm):
    commentaire = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Ajouter un commentaire sur le changement de statut (facultatif)'}),
        required=False,
        label="Commentaire"
    )

    class Meta:
        model = Commande
        fields = ['statut'] # Only allow changing the status field
        # You might add widgets here if you want a custom select, but default is fine.

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional: Disable choices that are final or invalid transitions
        # For a more complex system, you might dynamically filter choices here
        # based on the current instance's status.
        # Example: If current status is 'livre', don't allow 'en_preparation'
        if self.instance and self.instance.is_final:
            # You might want to remove options like 'en_preparation', 'expedie' etc.
            # Or make them unselectable with JavaScript. For simplicity, we rely on model method validation.
            pass

class CommandeForm(forms.ModelForm):
    class Meta:
        model = Commande
        fields = ['client', 'devis', 'date', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'devis': forms.Select(attrs={'id': 'id_devis_select'}),
        }

    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)

        if self.entreprise:
            self.fields['client'].queryset = Client.objects.filter(entreprise=self.entreprise)
            
            # Filtrer les devis acceptés
            self.fields['devis'].queryset = Devis.objects.filter(
                entreprise=self.entreprise,
                statut='accepte' 
            ).order_by('-date')
            
            self.fields['devis'].empty_label = "--- Sélectionner un devis (facultatif) ---"
            
            # Si un devis est pré-sélectionné, désactiver le champ pour éviter les modifications
            if self.instance and self.instance.devis:
                self.fields['devis'].disabled = True
                self.fields['client'].disabled = True

class LigneCommandeForm(forms.ModelForm):
    produit = forms.ModelChoiceField(queryset=Produit.objects.none())
    
    class Meta:
        model = LigneCommande
        fields = ['produit', 'quantite', 'prix_unitaire', 'taux_tva']
    
    def __init__(self, *args, **kwargs):
        entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        if entreprise:
            self.fields['produit'].queryset = Produit.objects.filter(entreprise=entreprise)

    def clean(self):
        cleaned_data = super().clean()
        quantite = cleaned_data.get('quantite')
        prix_unitaire = cleaned_data.get('prix_unitaire')
        taux_tva = cleaned_data.get('taux_tva')

        if quantite is not None and prix_unitaire is not None and taux_tva is not None:
            montant_ht = quantite * prix_unitaire
            montant_tva = montant_ht * (taux_tva / decimal.Decimal('100.00'))
            cleaned_data['montant_ht'] = montant_ht
            cleaned_data['montant_tva'] = montant_tva
        
        return cleaned_data


LigneCommandeFormSet = inlineformset_factory(
    Commande, LigneCommande, 
    form=LigneCommandeForm,
    extra=1,
    can_delete=True
)

# ventes/forms.py
class BonLivraisonForm(forms.ModelForm):
    class Meta:
        model = BonLivraison
        fields = ['commande', 'date', 'notes', 'statut']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'commande': forms.Select(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # --- ADD THESE PRINTS ---
        print(f"Request present: {self.request is not None}")
        if self.request and hasattr(self.request, 'user') and self.request.user.is_authenticated:
            
            # Crucial check: Does the user have an entreprise?
            if hasattr(self.request.user, 'entreprise') and self.request.user.entreprise:
                print(f"User's entreprise: {self.request.user.entreprise.nom} (ID: {self.request.user.entreprise.id})")
                
                # Check the initial queryset before filtering
                initial_queryset_count = self.fields['commande'].queryset.count()
                print(f"Initial Commande queryset count (before filtering by user's entreprise): {initial_queryset_count}")
                
                # Perform the filtering
                self.fields['commande'].queryset = self.fields['commande'].queryset.filter(
                    entreprise=self.request.user.entreprise
                )
                
                # Check the filtered queryset
                filtered_queryset_count = self.fields['commande'].queryset.count()
                print(f"Filtered Commande queryset count for user's entreprise: {filtered_queryset_count}")
                
                if filtered_queryset_count == 0:
                    print("WARNING: No commands found for the current user's enterprise after filtering.")
                    # You might want to check the status or 'bon_livraison_genere' field if you have them
                    # For example:
                    # all_cmds_for_user_ent = Commande.objects.filter(entreprise=self.request.user.entreprise)
                    # print(f"All commands for user's enterprise regardless of other filters: {all_cmds_for_user_ent.count()}")
                    # for cmd in all_cmds_for_user_ent:
                    #     print(f"  - Commande {cmd.numero}, Statut: {cmd.statut}, BL Genere: {cmd.bon_livraison_genere}")
                    
                for cmd in self.fields['commande'].queryset:
                    print(f"  - Commande in queryset: {cmd.numero} (Client: {cmd.client.nom}, Statut: {cmd.statut})")
            else:
                print("User does NOT have an associated 'entreprise' or 'entreprise' is None.")
        else:
            print("Request or user not authenticated in BonLivraisonForm init or no user attribute.")
        print("--- END DEBUG ---")
        # --- END ADDED PRINTS ---
class LigneBonLivraisonForm(forms.ModelForm):
    produit = forms.ModelChoiceField(queryset=None, widget=forms.Select(attrs={'class': 'form-control select2'}))
    
    class Meta:
        model = LigneBonLivraison
        fields = ['produit', 'quantite', 'prix_unitaire', 'taux_tva']
        widgets = {
            'quantite': forms.NumberInput(attrs={'class': 'form-control'}),
            'prix_unitaire': forms.NumberInput(attrs={'class': 'form-control'}),
            'taux_tva': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        # Ensure Produit is imported if not already. This is critical.
        try:
            from STOCK.models import Produit # Adjust this import path as needed
        except ImportError:
            # Handle case where Produit might not be found (e.g., during initial setup)
            Produit = None 

        if entreprise and Produit:
            self.fields['produit'].queryset = Produit.objects.filter(entreprise=entreprise)
        elif Produit: # If no entreprise is passed but Produit exists, keep its default queryset
             self.fields['produit'].queryset = Produit.objects.all()
        else: # Fallback if Produit can't be imported
            self.fields['produit'].queryset = Produit.objects.none()


LigneBonLivraisonFormSet = inlineformset_factory(
    BonLivraison, LigneBonLivraison, 
    form=LigneBonLivraisonForm,
    extra=1, # Number of empty forms to display
    can_delete=True,
    # You might want to add max_num if you want to limit items
    # max_num=10, 
)

#from django import forms
from django.core.exceptions import ValidationError
from .models import Facture
from STOCK.models import Client
# ventes/forms.py
from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import decimal 
from django.apps import apps 

# Import your models from their respective apps
from .models import Facture, LigneFacture, Devis, Commande, BonLivraison
from parametres.models import Entreprise
from STOCK.models import Client, Produit 

import decimal
import logging
from django import forms
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from django.utils.translation import gettext_lazy as _

# Import your models from their respective apps
from .models import Facture, LigneFacture, Devis, Commande, BonLivraison
from parametres.models import Entreprise
from STOCK.models import Client, Produit 

logger = logging.getLogger(__name__)

class FactureForm(forms.ModelForm):
    client = forms.ModelChoiceField(
        queryset=Client.objects.none(),
        label=_("Client"),
        widget=forms.Select(attrs={'class': 'form-select select2'})
    )
    
    # Déclaration explicite des champs avec queryset initial vide
    devis = forms.ModelChoiceField(
        queryset=Devis.objects.none(),
        required=False,
        label=_("Devis lié"),
        widget=forms.Select(attrs={'class': 'form-select select2-documents'})
    )
    
    commande = forms.ModelChoiceField(
        queryset=Commande.objects.none(),
        required=False,
        label=_("Commande liée"),
        widget=forms.Select(attrs={'class': 'form-select select2-documents'})
    )
    
    bon_livraison = forms.ModelChoiceField(
        queryset=BonLivraison.objects.none(),
        required=False,
        label=_("Bon de livraison lié"),
        widget=forms.Select(attrs={'class': 'form-select select2-documents'})
    )

    class Meta:
        model = Facture
        fields = ['client', 'date_facture', 'date_echeance', 'mode_paiement', 'notes',
                  'devis', 'commande', 'bon_livraison']

    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        if self.entreprise:
            self.fields['client'].queryset = Client.objects.filter(
                entreprise=self.entreprise
            ).order_by('nom')
            
            # Correction: Utilisez des guillemets autour des chaînes de caractères
        if 'devis' in self.fields:
            self.fields['devis'].queryset = Devis.objects.filter(
                entreprise=self.entreprise,
                statut='accepte' # <-- CORRECT
            ).select_related('client').order_by('-date_facture')

        if 'commande' in self.fields:
            self.fields['commande'].queryset = Commande.objects.filter(
                entreprise=self.entreprise,
                # Correction: Utilisez des guillemets pour chaque statut
                statut__in=['Confirmee', 'expedie', 'livre'] # <-- CORRECT
            ).select_related('client').order_by('-date_facture')

        if 'bon_livraison' in self.fields:
            self.fields['bon_livraison'].queryset = BonLivraison.objects.filter(
                entreprise=self.entreprise,
                statut='livre' # <-- CORRECT
            ).select_related('commande__client').order_by('-date_facture')

                
class LigneFactureForm(forms.ModelForm):
    produit = forms.ModelChoiceField(
        queryset=Produit.objects.none(),  # Queryset vide initial
        label=_("Article"),
        widget=forms.Select(attrs={'class': 'form-select select2'})
    )
    
    class Meta:
        model = LigneFacture
        fields = ['produit', 'quantite', 'prix_unitaire', 'taux_tva']
        widgets = {
            'quantite': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0.01',
                'step': '0.01'
            }),
            'prix_unitaire': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01'
            }),
            'taux_tva': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.1'
            }),
        }

    def __init__(self, *args, **kwargs):
            self.entreprise = kwargs.pop('entreprise', None)
            super().__init__(*args, **kwargs)
            
            if self.entreprise:
                self.fields['produit'].queryset = Produit.objects.filter(
                    entreprise=self.entreprise,
                    actif=True
        ).order_by('nom')

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Calcul des montants
        instance.montant_ht = instance.quantite * instance.prix_unitaire
        instance.montant_tva = instance.montant_ht * (instance.taux_tva / decimal.Decimal('100.00'))
        
        if commit:
            instance.save()
        
        return instance

class BaseLigneFactureFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)
        
        # CORRECTION: Éviter l'accès à la relation si l'instance n'est pas sauvegardée
        if self.instance and not self.instance.pk:
            self.queryset = LigneFacture.objects.none()

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        if self.entreprise:
            kwargs['entreprise'] = self.entreprise
        return kwargs

    def clean(self):
        super().clean()
        
        # Validation pour s'assurer qu'il y a au moins une ligne
        if not any(not self._should_delete_form(form) and form.has_changed() 
                   for form in self.forms):
            raise forms.ValidationError(_("Vous devez ajouter au moins un produit à la facture."))



LigneFactureFormSet = inlineformset_factory(
    Facture,
    LigneFacture,
    form=LigneFactureForm,
    formset=BaseLigneFactureFormSet,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True
)


class FactureStatutForm(forms.ModelForm):
    commentaire = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _("Commentaire sur le changement de statut")
        }),
        label=_("Commentaire")
    )

    class Meta:
        model = Facture
        fields = ['statut']
        widgets = {
            'statut': forms.Select(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer les choix de statut en fonction du statut actuel
        if self.instance.statut == 'annule':
            self.fields['statut'].choices = [('annule', 'Annulé')]
        elif self.instance.statut == 'paye':
            self.fields['statut'].choices = [('paye', 'Payé')]

# ventes/forms.py
from django import forms
from .models import Paiement, Facture

class PaiementForm(forms.ModelForm):
    class Meta:
        model = Paiement
        fields = ['montant', 'date', 'mode_paiement', 'reference', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'montant': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'mode_paiement': forms.Select(attrs={
                'class': 'form-control'
            }),
            'reference': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }

    def __init__(self, *args, **kwargs):
        self.facture = kwargs.pop('facture', None)
        super().__init__(*args, **kwargs)
        
        if self.facture:
            reste_a_payer = self.facture.montant_restant
            self.fields['montant'].initial = reste_a_payer
            self.fields['montant'].widget.attrs['max'] = str(reste_a_payer)
            self.fields['montant'].widget.attrs['value'] = str(reste_a_payer)
            
# ventes/forms.py
class EcartCaisseForm(forms.ModelForm):
    class Meta:
        model = EcartCaisse
        fields = ['type_ecart', 'montant', 'motif']
        widgets = {
            'motif': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Explication de l\'écart...'}),
            'type_ecart': forms.Select(attrs={'class': 'form-select'}),
            'montant': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['montant'].widget.attrs.update({'class': 'form-control'})