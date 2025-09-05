from django import forms
from django.forms import inlineformset_factory
from .models import *
from STOCK.models import Produit
from parametres.models import *

# achats/forms.py (ou où ton FournisseurForm est défini)
from django import forms
from .models import Fournisseur # Assure-toi d'importer le bon modèle

class FournisseurForm(forms.ModelForm):
    class Meta:
        model = Fournisseur
      
        fields = ['nom', 'email', 'telephone', 'adresse'] # Liste explicitement les champs que tu veu
        widgets = {
            'adresse': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        # Retire l'argument 'entreprise' du pop si tu n'en as plus besoin pour d'autres logiques
        # ou gère-le si tu l'utilises toujours pour autre chose.
        entreprise = kwargs.pop('entreprise', None)
        super().__init__(*args, **kwargs)

        # Si le champ 'code' ne doit pas être affiché du tout dans le formulaire
        if 'code' in self.fields:
            del self.fields['code']

        # Si tu veux le laisser affiché mais en lecture seule :
        # if 'code' in self.fields:
        #     self.fields['code'].widget.attrs['readonly'] = True
        #     self.fields['code'].required = False # Pas obligatoire dans le form
class CommandeAchatForm(forms.ModelForm):
    class Meta:
        model = CommandeAchat
        # Excluez 'statut' car il a une valeur par défaut dans le modèle.
        # Aussi, excluez les champs gérés automatiquement ou non destinés à être modifiés par l'utilisateur.
        exclude = ['entreprise', 'created_by', 'numero_commande', 'devise', 'taux_change', 'statut']
        widgets = {
            'date_commande': forms.DateInput(attrs={'type': 'date'}),
            'date_livraison_prevue': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, entreprise=None, **kwargs):
        super().__init__(*args, **kwargs)
        if entreprise:
            self.fields['fournisseur'].queryset = Fournisseur.objects.filter(entreprise=entreprise)
        else:
            self.fields['fournisseur'].queryset = Fournisseur.objects.none()

### `LigneCommandeAchatForm` (Updated for TVA)

class LigneCommandeAchatForm(forms.ModelForm):
    # 'produit_code' est un champ additionnel non directement sur le modèle,
    # utilisé pour l'affichage ou les recherches dynamiques dans le template.
    produit_code = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = LigneCommandeAchat
        # Exclure 'commande', 'livree', 'quantite_livree', 'montant_tva_ligne'.
        # 'commande' est géré par le formset.
        # 'livree' et 'quantite_livree' sont probablement gérés en dehors du formulaire de création initiale.
        # 'montant_tva_ligne' est calculé dans la méthode save du modèle, donc il est exclu.
        exclude = ['commande', 'livree', 'quantite_livree', 'montant_tva_ligne']

        # Ajout de widgets pour une meilleure expérience utilisateur avec les DecimalFields
        widgets = {
            'quantite': forms.NumberInput(attrs={'step': '0.01'}),
            'prix_unitaire': forms.NumberInput(attrs={'step': '0.01'}),
            'remise': forms.NumberInput(attrs={'step': '0.01'}),
            'taux_tva': forms.NumberInput(attrs={'step': '0.01'}), # Nouveau : Widget pour le taux de TVA
        }

    def __init__(self, *args, entreprise=None, **kwargs):
        super().__init__(*args, **kwargs)

        if entreprise:
            # Filtre le queryset 'produit' pour l'entreprise actuelle
            # et n'inclut que les produits 'actifs'.
            # Il pré-charge également 'categorie' pour des gains de performance potentiels.
            self.fields['produit'].queryset = Produit.objects.filter(
                entreprise=entreprise,
                actif=True
            ).select_related('categorie')

            # --- Logique pour définir le taux de TVA initial ---
            # Si nous éditons une ligne existante, le taux_tva sera déjà dans self.instance.
            if self.instance.pk:
                # Le formulaire affichera naturellement la valeur sauvegardée, pas besoin de set 'initial'.
                pass
            # Si c'est une nouvelle ligne et que des données initiales de commande/fournisseur sont disponibles
            # via l'argument initial du formset (peu probable pour les 'extra' forms)
            elif 'fournisseur' in self.initial and self.initial['fournisseur']: # S'assurer que fournisseur n'est pas None/vide
                try:
                    # Assurez-vous que votre modèle Fournisseur a un champ 'taux_tva_defaut'
                    fournisseur = Fournisseur.objects.get(pk=self.initial['fournisseur'])
                    if fournisseur.taux_tva_defaut is not None:
                        self.fields['taux_tva'].initial = fournisseur.taux_tva_defaut
                except Fournisseur.DoesNotExist:
                    # Si le fournisseur n'est pas trouvé (cas rare), on utilise le taux de l'entreprise.
                    if entreprise and entreprise.taux_tva_defaut is not None:
                        self.fields['taux_tva'].initial = entreprise.taux_tva_defaut
                    else:
                        self.fields['taux_tva'].initial = Decimal('0.00')
            # Si aucune information de fournisseur spécifique n'est disponible (nouvelles lignes 'extra'),
            # ou si le fournisseur n'a pas de taux par défaut, on utilise le taux de l'entreprise.
            elif entreprise and entreprise.taux_tva_defaut is not None:
                self.fields['taux_tva'].initial = entreprise.taux_tva_defaut
            else:
                # Par défaut à 0.00 si aucun taux de TVA spécifique ne peut être déduit.
                self.fields['taux_tva'].initial = Decimal('0.00')

        else:
            # Si aucune 'entreprise' n'est fournie (ce qui ne devrait pas arriver avec votre mixin),
            # assurez-vous qu'aucun produit n'est sélectionnable pour éviter les fuites de données.
            self.fields['produit'].queryset = Produit.objects.none()
            self.fields['taux_tva'].initial = Decimal('0.00') # Assurer un défaut même sans entreprise

LigneCommandeAchatFormSet = inlineformset_factory(
    CommandeAchat,
    LigneCommandeAchat,
    form=LigneCommandeAchatForm, # This correctly references the custom form above
    extra=1,
    can_delete=True
)

from decimal import Decimal 
from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory
from django.db import models # Pour F()

# Assurez-vous que ces imports sont corrects selon votre structure de projet
# NOTE : J'ai mis 'stock' en minuscules. Si votre dossier d'application est 'STOCK' (en majuscules),
# vous devrez changer 'stock.models' en 'STOCK.models' ici.
from .models import LigneBonReception, CommandeAchat, LigneCommandeAchat, BonReception
from STOCK.models import Produit 
class LigneBonReceptionForm(forms.ModelForm):
    produit_commande = forms.CharField(
        label="Produit sur la Commande",
        required=False,
        disabled=True, 
        help_text="Affiche le produit et la quantité restant à livrer pour la ligne de commande sélectionnée."
    )

    class Meta:
        model = LigneBonReception
        fields = ['ligne_commande', 'quantite', 'conditionnement', 'notes']
        widgets = {
            'ligne_commande': forms.Select(attrs={'class': 'form-control'}),
            'quantite': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}), 
            'conditionnement': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        commande_id = kwargs.pop('commande', None)
        super().__init__(*args, **kwargs)

        if commande_id:
            self.fields['ligne_commande'].queryset = LigneCommandeAchat.objects.filter(
                commande_id=commande_id,
                quantite__gt=models.F('quantite_livree') 
            ).select_related('produit') 

            self.fields['ligne_commande'].label_from_instance = self.get_ligne_commande_label

            if not self.fields['ligne_commande'].queryset.exists():
                self.fields['ligne_commande'].help_text = "Aucune ligne de commande disponible pour la réception."
        else:
            self.fields['ligne_commande'].queryset = LigneCommandeAchat.objects.none()
            self.fields['ligne_commande'].help_text = "Aucune commande fournie."

        ligne = getattr(self.instance, 'ligne_commande', None)
        if ligne:
            self.fields['produit_commande'].initial = self.get_ligne_commande_label(ligne)
        else:
            self.fields['produit_commande'].initial = "Sélectionnez une ligne de commande ci-dessous."

        self.fields['produit_commande'].widget.attrs['readonly'] = True

    def get_ligne_commande_label(self, obj):
        if not obj or not hasattr(obj, 'produit') or obj.produit is None:
            return f"Ligne Commande ID {obj.pk} - Produit introuvable"

        quantite_commandee = Decimal(str(obj.quantite))
        quantite_livree = Decimal(str(obj.quantite_livree))

        if self.instance.pk and self.instance.ligne_commande_id == obj.pk:
            quantite_livree -= Decimal(str(self.instance.quantite))
            quantite_livree = max(Decimal('0'), quantite_livree)

        quantite_restante = max(Decimal('0'), quantite_commandee - quantite_livree)

        return (
            f"{obj.produit.nom} "
            f"(Commandé: {quantite_commandee.normalize()}, "
            f"Déjà livré: {quantite_livree.normalize()}, "
            f"Reste à livrer: {quantite_restante.normalize()})"
        )

class BaseLigneBonReceptionFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        self.commande = kwargs.pop('form_kwargs', {}).get('commande', None)
        super().__init__(*args, **kwargs)

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs['commande'] = self.commande
        return kwargs

    def clean(self):
        super().clean()
        if any(self.errors):
            return

        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get('DELETE', False):
                continue

            ligne_cmd = form.cleaned_data.get('ligne_commande')
            quantite_recue = form.cleaned_data.get('quantite')

            if not ligne_cmd or quantite_recue is None:
                continue

            quantite_recue_decimal = Decimal(str(quantite_recue))
            quantite_deja_enregistree = ligne_cmd.quantite_livree or Decimal('0')

            if form.instance.pk and form.instance.ligne_commande_id == ligne_cmd.pk:
                quantite_deja_enregistree = max(
                    Decimal('0'),
                    quantite_deja_enregistree - (form.instance.quantite or Decimal('0'))
                )

            nouveau_total_livre = quantite_deja_enregistree + quantite_recue_decimal

            if nouveau_total_livre > ligne_cmd.quantite:
                form.add_error(
                    'quantite',
                    forms.ValidationError(
                        f"La quantité totale reçue pour '{ligne_cmd.produit.nom}' ({nouveau_total_livre.normalize()}) "
                        f"dépasse la quantité commandée ({ligne_cmd.quantite.normalize()}). "
                        f"Quantité restante à recevoir : {(ligne_cmd.quantite - quantite_deja_enregistree).normalize()}."
                    )
                )

LigneBonReceptionFormSet = inlineformset_factory(
    BonReception,
    LigneBonReception,
    form=LigneBonReceptionForm,
    extra=1,
    can_delete=True,
    formset=BaseLigneBonReceptionFormSet
)
            
class ImportFournisseurForm(forms.Form):
    fichier_excel = forms.FileField(
        label="Fichier Excel",
        help_text="Téléchargez un fichier Excel (.xlsx) contenant les données des fournisseurs. "
                  "Colonnes requises : Nom, Code, Email, Telephone, Adresse.",
        widget=forms.FileInput(attrs={'accept': '.xlsx, .xls'})
    )