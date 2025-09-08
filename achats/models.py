from django.db import models
from django.conf import settings
from parametres.models import Entreprise, Devise
from STOCK.models import Produit
from django.utils.translation import gettext_lazy as _
from decimal import Decimal, ROUND_HALF_UP # Important pour les calculs de précision
from django.utils import timezone
    
    

# Ajoutez cette ligne au début de votre fichier models.py
from decimal import Decimal 
# achats/models.py
from django.db import models
# Importe ton modèle Entreprise. Assure-toi que le chemin est correct.
# from mon_app_entreprise.models import Entreprise # Exemple
# from parametres.models import Entreprise # Si c'est dans parametres

class Fournisseur(models.Model):
    entreprise = models.ForeignKey(
        Entreprise,
        on_delete=models.CASCADE,
        related_name='achats_fournisseurs'
    )
    # Le champ 'code' ne doit plus être unique ici, car la contrainte Meta le gère.
    # On va le laisser modifiable en base pour le code généré, mais pas dans le form.
    code = models.CharField(max_length=50, blank=True, unique=True) # Ajout de blank=True
    nom = models.CharField(max_length=100)
    email = models.EmailField()
    telephone = models.CharField(max_length=20)
    adresse = models.TextField()
    # SUPPRESSION DU CHAMP devise_preferee
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            # Cette contrainte assure que le code est unique PAR entreprise.
            # Elle est nécessaire si tu as plusieurs entreprises.
            models.UniqueConstraint(fields=['entreprise', 'code'], name='unique_code_fournisseur_entreprise')
        ]
        # Optionnel : tri par défaut
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.code})"

    # Nouvelle méthode pour générer le code avant la sauvegarde
    def save(self, *args, **kwargs):
        if not self.code: # Si le code n'est pas déjà défini
            self.code = self.generate_unique_code()
        super().save(*args, **kwargs)

    def generate_unique_code(self):
        # Logique de génération du code.
        # Tu peux utiliser un timestamp, un UUID partiel, ou une séquence.
        # Pour un code aléatoire de 8 chiffres par exemple :
        import random
        import string
        from django.utils import timezone

        while True:
            # Exemple 1: Combinaison date/heure + aléatoire
            # prefix = timezone.now().strftime("%Y%m%d") # AnnéeMoisJour
            # random_part = ''.join(random.choices(string.digits, k=4)) # 4 chiffres aléatoires
            # new_code = f"F-{prefix}-{random_part}"

            # Exemple 2: Code alphanumérique plus simple
            # new_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8)) # 8 caractères alphanumériques

            # Exemple 3: Basé sur un ID ou un compteur (plus complexe à gérer sans collision)
            # Pour l'instant, restons sur de l'aléatoire simple pour éviter les complications
            new_code = ''.join(random.choices(string.digits, k=6)) # 6 chiffres aléatoires pour le code

            # Vérifie si le code existe déjà pour cette entreprise
            # Important : utilise self.entreprise pour la contrainte UniqueConstraint
            if not Fournisseur.objects.filter(entreprise=self.entreprise, code=new_code).exists():
                return new_code

# achats/models.py
from django.db import models
from django.conf import settings
# Assurez-vous d'importer le bon modèle Entreprise et Produit
# from mon_app_entreprise.models import Entreprise # Exemple
# from mon_app_produit.models import Produit # Exemple
# Assurez-vous d'importer la Devise si elle est utilisée ailleurs, mais pas ici pour CommandeAchat
# from parametres.models import Devise, ConfigurationSAAS # Importez ConfigurationSAAS ici
class CommandeAchat(models.Model):
    STATUT_CHOICES = [
        ('brouillon', _('Brouillon')),
        ('envoyee', _('Envoyée')),
        ('recue', _('Reçue')),
        ('partiellement_livree', _('Partiellement livrée')),
        ('livree', _('Livrée')),
        ('annulee', _('Annulée')),
    ]
    entreprise = models.ForeignKey(
        Entreprise,
        on_delete=models.CASCADE,
        related_name='achats_commandes',
        verbose_name=_("Entreprise")
    )
    fournisseur = models.ForeignKey(
        Fournisseur,
        on_delete=models.PROTECT,
        related_name='commandes',
        verbose_name=_("Fournisseur")
    )
    numero_commande = models.CharField(_("Numéro de Commande"), max_length=50, unique=False) # unique=False car on a unique_together
    date_commande = models.DateField(_("Date de commande"))
    date_livraison_prevue = models.DateField(_("Date de livraison prévue"), null=True, blank=True)
    statut = models.CharField(_("Statut"), max_length=50, choices=STATUT_CHOICES, default='brouillon')
    notes = models.TextField(_("Notes"), blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name=_("Créée par"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Commande d'Achat")
        verbose_name_plural = _("Commandes d'Achat")
        permissions = [
            ("valider_commandeachat", _("Peut valider une commande d'achat")),
            ("annuler_commandeachat", _("Peut annuler une commande d'achat")),
            ("exporter_commandeachat", _("Peut exporter les commandes d'achat")),
        ]
        constraints = [
            models.UniqueConstraint(fields=['entreprise', 'numero_commande'], name='unique_commande_achat_par_entreprise')
        ]
        ordering = ['-date_commande', '-created_at'] # Ajout d'un ordre par défaut

    def __str__(self):
        return f"CA-{self.numero_commande} ({self.fournisseur.nom})"

    @property
    def total_ht(self):
        """Calcule le total Hors Taxe de toutes les lignes de commande."""
        # Utilise .aggregate pour une meilleure performance en base de données
        # Assurez-vous que 'lignes' est bien le related_name dans LigneCommandeAchat
        return self.lignes.aggregate(
            total=models.Sum(
                models.F('quantite') * models.F('prix_unitaire') * (Decimal('1') - models.F('remise') / Decimal('100')),
                output_field=models.DecimalField(max_digits=10, decimal_places=2) # Spécifier le type de sortie
            )
        )['total'] or Decimal('0.00') # Retourne Decimal('0.00') si pas de lignes

    @property
    def total_tva(self):
        """Calcule le total de la TVA de toutes les lignes de commande."""
        # Summe les montants_tva_ligne de chaque ligne
        return self.lignes.aggregate(
            total=models.Sum('montant_tva_ligne', output_field=models.DecimalField(max_digits=10, decimal_places=2))
        )['total'] or Decimal('0.00')

    @property
    def total_ttc(self):
        """Calcule le total Toutes Taxes Comprises de toutes les lignes de commande."""
        # Les calculs doivent toujours être faits avec Decimal pour la précision
        return (self.total_ht + self.total_tva).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @property
    def devise(self):
        """
        Récupère la devise principale de l'entreprise associée.
        Nécessite que votre modèle Entreprise ait une relation ou une propriété pour sa devise.
        """
        if hasattr(self.entreprise, 'configurationsaas') and self.entreprise.configurationsaas.devise_principale:
            return self.entreprise.configurationsaas.devise_principale
        # Ou si la devise est directement sur le modèle Entreprise :
        # if hasattr(self.entreprise, 'devise_principale') and self.entreprise.devise_principale:
        #     return self.entreprise.devise_principale
        return None # Ou une instance de Devise par défaut si aucune n'est trouvée


class LigneCommandeAchat(models.Model):
    commande = models.ForeignKey(CommandeAchat, on_delete=models.CASCADE, related_name='lignes', verbose_name=_("Commande"))
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT, verbose_name=_("Produit"))
    quantite = models.DecimalField(_("Quantité"), max_digits=10, decimal_places=2)
    prix_unitaire = models.DecimalField(_("Prix Unitaire HT"), max_digits=10, decimal_places=2)
    remise = models.DecimalField(_("Remise (%)"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # NOUVEAU CHAMP: Taux de TVA pour cette ligne spécifique
    taux_tva = models.DecimalField(
        _("Taux TVA (%)"),
        max_digits=5,      # Ex: 99.99
        decimal_places=2,  # Ex: 19.50 pour 19.5%
        default=Decimal('0.00'),
        help_text=_("Taux de TVA à appliquer à cette ligne (en pourcentage).")
    )
    # NOUVEAU CHAMP: Montant de la TVA calculé pour cette ligne
    montant_tva_ligne = models.DecimalField(
        _("Montant TVA"),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_("Montant de la TVA calculé pour cette ligne."),
        editable=False # Ce champ est calculé, pas directement éditable par l'utilisateur
    )

    livree = models.BooleanField(_("Livrée"), default=False)
    quantite_livree = models.DecimalField(_("Quantité Livrée"), max_digits=10, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = _("Ligne de Commande d'Achat")
        verbose_name_plural = _("Lignes de Commandes d'Achat")
        unique_together = ('commande', 'produit') # Une commande ne peut avoir qu'une ligne par produit

    def __str__(self):
        return f"{self.quantite} x {self.produit.nom} ({self.commande.numero_commande})"

    @property
    def total_ht_ligne(self):
        """Calcule le total Hors Taxe pour cette ligne (après remise)."""
        total = self.quantite * self.prix_unitaire
        if self.remise > 0:
            total = total * (Decimal('1') - self.remise / Decimal('100'))
        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) # Arrondi au centième le plus proche

    @property
    def total_ttc_ligne(self):
        """Calcule le total Toutes Taxes Comprises pour cette ligne."""
        return (self.total_ht_ligne + self.montant_tva_ligne).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour calculer et mettre à jour
        le montant de la TVA avant la sauvegarde de l'objet.
        """
        # S'assurer que les valeurs nécessaires existent avant le calcul
        if all([self.quantite is not None, self.prix_unitaire is not None, self.remise is not None, self.taux_tva is not None]):
            montant_ht = self.total_ht_ligne
            taux_tva_facteur = self.taux_tva / Decimal('100.00')
            self.montant_tva_ligne = (montant_ht * taux_tva_facteur).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            self.montant_tva_ligne = Decimal('0.00') # Valeur par défaut si des champs sont manquants

        super().save(*args, **kwargs)
        

from django.conf import settings
from parametres.models import Entreprise
from STOCK.models import Produit
from django.utils.translation import gettext_lazy as _
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
import random
import string

class BonReception(models.Model):
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    numero_bon = models.CharField(max_length=50)  # Retirer unique=True ici
    commande = models.ForeignKey('CommandeAchat', on_delete=models.PROTECT)
    date_reception = models.DateField()
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='bons_reception_crees'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_reception']
        verbose_name = "Bon de réception"
        verbose_name_plural = "Bons de réception"
        # Ajouter une contrainte d'unicité par entreprise
        constraints = [
            models.UniqueConstraint(
                fields=['entreprise', 'numero_bon'],
                name='unique_numero_bon_par_entreprise'
            )
        ]

    def __str__(self):
        return f"BR-{self.numero_bon}"
    
    def save(self, *args, **kwargs):
        # Générer le numéro de bon automatiquement s'il n'existe pas
        if not self.numero_bon:
            self.numero_bon = self.generer_numero_unique()
        super().save(*args, **kwargs)
    
    def generer_numero_unique(self):
        """Génère un numéro de bon unique pour cette entreprise"""
        from django.db import models
        
        # Format: BR-YYYY-NNNN (BR-2024-0001)
        annee = timezone.now().year
        
        # Trouver le dernier numéro pour cette entreprise et cette année
        dernier_bon = BonReception.objects.filter(
            entreprise=self.entreprise,
            numero_bon__startswith=f"BR-{annee}-"
        ).order_by('-numero_bon').first()
        
        if dernier_bon:
            try:
                # Extraire le numéro séquentiel
                dernier_numero = int(dernier_bon.numero_bon.split('-')[-1])
                nouveau_numero = dernier_numero + 1
            except (ValueError, IndexError):
                nouveau_numero = 1
        else:
            nouveau_numero = 1
        
        return f"BR-{annee}-{nouveau_numero:04d}"
    
class LigneBonReception(models.Model):
    bon = models.ForeignKey(BonReception, on_delete=models.CASCADE, related_name='lignes')
    ligne_commande = models.ForeignKey(
        'LigneCommandeAchat',
        on_delete=models.PROTECT,
        related_name='lignes_reception'
    )
    quantite = models.DecimalField(max_digits=10, decimal_places=2)
    conditionnement = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Ligne BR {self.bon.numero_bon} - {self.ligne_commande.produit.nom} ({self.quantite.normalize()})"
# achats/models.py (ajouts)
from django.db import models
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from django.db.models import Sum

class FactureFournisseur(models.Model):
    """Modèle pour les factures fournisseurs"""
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('validee', 'Validée'),
        ('payee', 'Payée'),
        ('partiellement_payee', 'Partiellement payée'),
        ('annulee', 'Annulée'),
    ]

    entreprise = models.ForeignKey('parametres.Entreprise', on_delete=models.CASCADE)
    fournisseur = models.ForeignKey('achats.Fournisseur', on_delete=models.CASCADE)
    bon_reception = models.ForeignKey('achats.BonReception', on_delete=models.CASCADE, null=True, blank=True)
    numero_facture = models.CharField(max_length=50, unique=True)
    date_facture = models.DateField()
    date_echeance = models.DateField()
    montant_ht = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    montant_tva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    montant_ttc = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Facture Fournisseur"
        verbose_name_plural = "Factures Fournisseurs"
        ordering = ['-date_facture', '-created_at']

    def __str__(self):
        return f"Facture {self.numero_facture} - {self.fournisseur.nom}"

    def save(self, *args, **kwargs):
        if not self.numero_facture:
            self.numero_facture = self.generate_numero_facture()
        super().save(*args, **kwargs)

    def generate_numero_facture(self):
        """Génère un numéro de facture unique"""
        today = timezone.now().date()
        last_facture = FactureFournisseur.objects.filter(
            entreprise=self.entreprise,
            numero_facture__startswith=f"FF-{today.year}-"
        ).order_by('-numero_facture').first()

        sequence = 1
        if last_facture:
            try:
                sequence = int(last_facture.numero_facture.split('-')[-1]) + 1
            except (ValueError, IndexError):
                pass

        return f"FF-{today.year}-{sequence:04d}"
    
    @property
    def montant_paye(self):
        """Retourne le montant total payé sur cette facture"""
        from .models import PaiementFournisseur
        return self.paiements.filter(statut='valide').aggregate(
            total=Sum('montant', output_field=models.DecimalField(max_digits=12, decimal_places=2))
        )['total'] or Decimal('0.00')
    
    @property
    def reste_a_payer(self):
        """Retourne le montant restant à payer"""
        return max(self.montant_ttc - self.montant_paye, Decimal('0.00'))
    
    def get_ecritures_comptables(self):
        """Retourne les écritures comptables liées à cette facture"""
        from comptabilite.models import EcritureComptable
        return EcritureComptable.objects.filter(facture_fournisseur_liee=self)
    
    def get_paiements(self):
        """Retourne tous les paiements associés à cette facture"""
        from .models import PaiementFournisseur
        return self.paiements.all().order_by('-date_paiement')
    
    def update_statut(self):
        """Met à jour le statut de la facture en fonction des paiements"""
        montant_paye = self.montant_paye
        
        if montant_paye >= self.montant_ttc:
            self.statut = 'payee'
        elif montant_paye > 0:
            self.statut = 'partiellement_payee'
        elif self.statut != 'annulee':
            self.statut = 'validee'
        
        self.save()
        
from django.db import models
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from django.db.models import Sum

class PaiementFournisseur(models.Model):
    """Modèle pour les paiements des factures fournisseurs"""
    MODE_PAIEMENT_CHOICES = [
        ('virement', 'Virement bancaire'),
        ('cheque', 'Chèque'),
        ('espece', 'Espèces'),
        ('carte', 'Carte bancaire'),
        ('autre', 'Autre'),
    ]

    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('valide', 'Validé'),
        ('annule', 'Annulé'),
    ]

    entreprise = models.ForeignKey('parametres.Entreprise', on_delete=models.CASCADE)
    facture = models.ForeignKey('FactureFournisseur', on_delete=models.CASCADE, related_name='paiements')
    mode_paiement = models.CharField(max_length=20, choices=MODE_PAIEMENT_CHOICES, default='virement')
    reference = models.CharField(max_length=100, blank=True)
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    date_paiement = models.DateField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Paiement Fournisseur"
        verbose_name_plural = "Paiements Fournisseurs"
        ordering = ['-date_paiement', '-created_at']

    def __str__(self):
        return f"Paiement {self.reference} - {self.montant}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generate_reference()
        super().save(*args, **kwargs)

        # Mettre à jour le statut de la facture après sauvegarde
        self.facture.update_statut()

    def generate_reference(self):
        """Génère une référence de paiement unique"""
        today = timezone.now().date()
        last_paiement = PaiementFournisseur.objects.filter(
            entreprise=self.entreprise,
            reference__startswith=f"PAY-{today.year}-"
        ).order_by('-reference').first()

        sequence = 1
        if last_paiement:
            try:
                sequence = int(last_paiement.reference.split('-')[-1]) + 1
            except (ValueError, IndexError):
                pass

        return f"PAY-{today.year}-{sequence:04d}"

    def creer_ecriture_comptable(self):
        """Crée l'écriture comptable pour le paiement"""
        from comptabilite.models import EcritureComptable, LigneEcriture, PlanComptableOHADA, JournalComptable
        
        try:
            # Récupérer les comptes nécessaires
            compte_fournisseurs = PlanComptableOHADA.objects.get(
                numero='401',  # Fournisseurs
                entreprise=self.entreprise
            )
            
            # Déterminer le compte de trésorerie selon le mode de paiement
            if self.mode_paiement == 'virement':
                compte_tresorerie = PlanComptableOHADA.objects.get(
                    numero='512',  # Banque
                    entreprise=self.entreprise
                )
            elif self.mode_paiement == 'cheque':
                compte_tresorerie = PlanComptableOHADA.objects.get(
                    numero='511',  # Chèques à encaisser
                    entreprise=self.entreprise
                )
            elif self.mode_paiement == 'espece':
                compte_tresorerie = PlanComptableOHADA.objects.get(
                    numero='53',  # Caisse
                    entreprise=self.entreprise
                )
            else:
                compte_tresorerie = PlanComptableOHADA.objects.get(
                    numero='58',  # Autres moyens de paiement
                    entreprise=self.entreprise
                )
            
            # Récupérer le journal de trésorerie
            journal_tresorerie = JournalComptable.objects.get(
                code='BQ' if self.mode_paiement == 'virement' else 'CA',
                entreprise=self.entreprise
            )
            
            # Créer l'écriture comptable
            ecriture = EcritureComptable(
                journal=journal_tresorerie,
                date_ecriture=timezone.now(),
                date_comptable=self.date_paiement,
                libelle=f"Paiement {self.reference} - {self.facture.fournisseur.nom}",
                piece_justificative=self.reference,
                entreprise=self.entreprise,
                created_by=self.created_by,
                facture_fournisseur_liee=self.facture
            )
            ecriture.save()
            
            # Ligne 1: Débit des fournisseurs
            LigneEcriture.objects.create(
                ecriture=ecriture,
                compte=compte_fournisseurs,
                libelle=f"Paiement fournisseur - {self.facture.fournisseur.nom}",
                debit=self.montant,
                credit=Decimal('0.00'),
                entreprise=self.entreprise
            )
            
            # Ligne 2: Crédit de trésorerie
            LigneEcriture.objects.create(
                ecriture=ecriture,
                compte=compte_tresorerie,
                libelle=f"Paiement {self.get_mode_paiement_display()} - {self.facture.fournisseur.nom}",
                debit=Decimal('0.00'),
                credit=self.montant,
                entreprise=self.entreprise
            )
            
            return ecriture
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur création écriture comptable paiement: {e}")
            return None