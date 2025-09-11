from django.db import models
from django.conf import settings
from parametres.models import Entreprise, Devise
from STOCK.models import Produit
from django.utils.translation import gettext_lazy as _
from decimal import Decimal, ROUND_HALF_UP # Important pour les calculs de précision
from django.utils import timezone
from django.db.models import Sum, F
from django.db.models.functions import Coalesce    
from django.db import models
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from django.db.models import Sum
import logging
logger = logging.getLogger(__name__)   

# Ajoutez cette ligne au début de votre fichier models.py
from decimal import Decimal 
# achats/models.py
from django.db import models
# Importe ton modèle Entreprise. Assure-toi que le chemin est correct.
# from mon_app_entreprise.models import Entreprise # Exemple
# from parametres.models import Entreprise # Si c'est dans parametres


logger = logging.getLogger(__name__)

class Fournisseur(models.Model):
    entreprise = models.ForeignKey(
        Entreprise,
        on_delete=models.CASCADE,
        related_name='achats_fournisseurs'
    )
    code = models.CharField(max_length=50, blank=True, unique=True)
    nom = models.CharField(max_length=100)
    email = models.EmailField()
    telephone = models.CharField(max_length=20)
    adresse = models.TextField()
    
    # NOUVEAU CHAMP: Taux de TVA par défaut
    taux_tva_defaut = models.DecimalField(
        _("Taux TVA par défaut (%)"),
        max_digits=5,
        decimal_places=2,
        default=Decimal('16.00'),
        help_text=_("Taux de TVA par défaut pour ce fournisseur (en pourcentage)")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['entreprise', 'code'], name='unique_code_fournisseur_entreprise')
        ]
        ordering = ['nom']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.taux_tva_defaut is None:
            self.taux_tva_defaut = Decimal('16.00')

    def __str__(self):
        return f"{self.nom} ({self.code})"

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_unique_code()
        if self.taux_tva_defaut is None:
            self.taux_tva_defaut = Decimal('16.00')
        super().save(*args, **kwargs)

    def generate_unique_code(self):
        import random
        import string
        while True:
            new_code = ''.join(random.choices(string.digits, k=6))
            if not Fournisseur.objects.filter(entreprise=self.entreprise, code=new_code).exists():
                return new_code

class CommandeAchat(models.Model):
    STATUT_CHOICES = [
        ('brouillon', _('Brouillon')),
        ('envoyee', _('Envoyée')),
        ('recue', _('Reçue')),
        ('partiellement_livree', _('Partiellement livrée')),
        ('livree', _('Livrée')),
        ('annulee', _('Annulée')),
    ]
    
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, related_name='achats_commandes')
    fournisseur = models.ForeignKey(Fournisseur, on_delete=models.PROTECT, related_name='commandes')
    numero_commande = models.CharField(_("Numéro de Commande"), max_length=50)
    date_commande = models.DateField(_("Date de commande"))
    date_livraison_prevue = models.DateField(_("Date de livraison prévue"), null=True, blank=True)
    statut = models.CharField(_("Statut"), max_length=50, choices=STATUT_CHOICES, default='brouillon')
    notes = models.TextField(_("Notes"), blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Commande d'Achat")
        verbose_name_plural = _("Commandes d'Achat")
        constraints = [
            models.UniqueConstraint(fields=['entreprise', 'numero_commande'], name='unique_commande_achat_par_entreprise')
        ]
        ordering = ['-date_commande', '-created_at']

    def __str__(self):
        return f"CA-{self.numero_commande} ({self.fournisseur.nom})"

    @property
    def total_ht(self):
        return self.lignes.aggregate(
            total=models.Sum(
                models.F('quantite') * models.F('prix_unitaire') * (Decimal('1') - models.F('remise') / Decimal('100')),
                output_field=models.DecimalField(max_digits=10, decimal_places=2)
            )
        )['total'] or Decimal('0.00')

    @property
    def total_tva(self):
        return self.lignes.aggregate(
            total=models.Sum('montant_tva_ligne', output_field=models.DecimalField(max_digits=10, decimal_places=2))
        )['total'] or Decimal('0.00')

    @property
    def total_ttc(self):
        return (self.total_ht + self.total_tva).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

class LigneCommandeAchat(models.Model):
    commande = models.ForeignKey(CommandeAchat, on_delete=models.CASCADE, related_name='lignes')
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT)
    quantite = models.DecimalField(_("Quantité"), max_digits=10, decimal_places=2)
    prix_unitaire = models.DecimalField(_("Prix Unitaire HT"), max_digits=10, decimal_places=2)
    remise = models.DecimalField(_("Remise (%)"), max_digits=5, decimal_places=2, default=Decimal('0.00'))
    taux_tva = models.DecimalField(_("Taux TVA (%)"), max_digits=5, decimal_places=2, default=Decimal('16.00'))
    montant_tva_ligne = models.DecimalField(_("Montant TVA"), max_digits=10, decimal_places=2, default=Decimal('0.00'), editable=False)
    livree = models.BooleanField(_("Livrée"), default=False)
    quantite_livree = models.DecimalField(_("Quantité Livrée"), max_digits=10, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = _("Ligne de Commande d'Achat")
        verbose_name_plural = _("Lignes de Commandes d'Achat")
        unique_together = ('commande', 'produit')

    def __str__(self):
        return f"{self.quantite} x {self.produit.nom} ({self.commande.numero_commande})"

    @property
    def total_ht_ligne(self):
        total = self.quantite * self.prix_unitaire
        if self.remise > 0:
            total = total * (Decimal('1') - self.remise / Decimal('100'))
        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @property
    def total_ttc_ligne(self):
        return (self.total_ht_ligne + self.montant_tva_ligne).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def save(self, *args, **kwargs):
        if all([self.quantite is not None, self.prix_unitaire is not None, self.remise is not None, self.taux_tva is not None]):
            montant_ht = self.total_ht_ligne
            taux_tva_facteur = self.taux_tva / Decimal('100.00')
            self.montant_tva_ligne = (montant_ht * taux_tva_facteur).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        else:
            self.montant_tva_ligne = Decimal('0.00')
        
        super().save(*args, **kwargs)
        
from django.conf import settings
from parametres.models import Entreprise
from STOCK.models import Produit
from django.utils.translation import gettext_lazy as _
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from django.db import models
from django.db.models import Sum, F, Q
from django.db.models.functions import Coalesce
import random
import string

class BonReception(models.Model):
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    numero_bon = models.CharField(max_length=50)
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
    total_ht = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_tva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_ttc = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ['-date_reception']
        verbose_name = "Bon de réception"
        verbose_name_plural = "Bons de réception"
        constraints = [
            models.UniqueConstraint(
                fields=['entreprise', 'numero_bon'],
                name='unique_numero_bon_par_entreprise'
            )
        ]

    def calculer_totaux(self):
        """
        Recalcule et met à jour les totaux du bon de réception.
        VERSION ULTRA-SÉCURISÉE
        """
        try:
            total_ht = Decimal('0.00')
            total_tva = Decimal('0.00')
            
            for ligne in self.lignes.all():
                # VÉRIFICATION CRITIQUE : S'assurer que tous les champs nécessaires existent
                if not ligne.ligne_commande:
                    logger.error(f"Ligne {ligne.id} n'a pas de ligne_commande associée")
                    continue
                
                if ligne.quantite is None or ligne.prix_unitaire_ht is None:
                    logger.error(f"Ligne {ligne.id} a des champs manquants")
                    continue
                
                # Calcul cohérent avec LigneCommandeAchat
                remise = ligne.ligne_commande.remise or Decimal('0.00')
                remise_factor = Decimal('1') - (remise / Decimal('100'))
                prix_apres_remise = ligne.prix_unitaire_ht * remise_factor
                
                ligne_ht = ligne.quantite * prix_apres_remise
                
                # VÉRIFICATION CRITIQUE : Taux TVA - FORCER la cohérence
                taux_tva = ligne.taux_tva
                if taux_tva is None:
                    # Si le taux TVA est null, utiliser celui de la ligne de commande
                    taux_tva = ligne.ligne_commande.taux_tva or Decimal('16.00')
                    ligne.taux_tva = taux_tva
                    ligne.save(update_fields=['taux_tva'])
                
                ligne_tva = ligne_ht * (taux_tva / Decimal('100'))
                
                total_ht += ligne_ht
                total_tva += ligne_tva
            
            # Arrondir les totaux avec précision
            self.total_ht = total_ht.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.total_tva = total_tva.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            self.total_ttc = (total_ht + total_tva).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            # Sauvegarder
            self.save(update_fields=['total_ht', 'total_tva', 'total_ttc'])
            
            logger.info(f"Totaux recalculés pour bon {self.numero_bon}: HT={self.total_ht}, TVA={self.total_tva}, TTC={self.total_ttc}")
            
        except Exception as e:
            logger.error(f"Erreur critique dans calculer_totaux: {e}")
            # En cas d'erreur, utiliser des valeurs par défaut cohérentes
            self.total_ht = Decimal('0.00')
            self.total_tva = Decimal('0.00')
            self.total_ttc = Decimal('0.00')
            self.save(update_fields=['total_ht', 'total_tva', 'total_ttc'])
            raise

    def __str__(self):
        return f"BR-{self.numero_bon}"

    def creer_facture(self, created_by):
        """Crée une facture fournisseur à partir de ce bon de réception - VERSION ULTRA-SÉCURISÉE"""
        from .models import FactureFournisseur
        
        try:
            # FORCER le recalcul des totaux AVANT de créer la facture
            self.calculer_totaux()
            self.refresh_from_db()  # S'assurer d'avoir les dernières valeurs
            
            # VÉRIFICATION CRITIQUE : S'assurer que les totaux sont cohérents
            if self.total_ht <= 0 or self.total_ttc <= 0:
                logger.error(f"Totaux invalides pour le bon {self.numero_bon}: HT={self.total_ht}, TTC={self.total_ttc}")
                raise ValueError("Les totaux du bon de réception sont invalides")
            
            # CRÉATION DE LA FACTURE AVEC LES DONNÉES DU BON RECALCULÉES
            facture = FactureFournisseur.objects.create(
                entreprise=self.entreprise,
                fournisseur=self.commande.fournisseur,
                bon_reception=self,
                numero_facture=self.generer_numero_facture(),
                date_facture=timezone.now().date(),
                date_echeance=timezone.now().date() + timezone.timedelta(days=30),
                montant_ht=self.total_ht,      # UTILISER LES VALEURS RECALCULÉES
                montant_tva=self.total_tva,    # UTILISER LES VALEURS RECALCULÉES  
                montant_ttc=self.total_ttc,    # UTILISER LES VALEURS RECALCULÉES
                statut='brouillon',
                created_by=created_by
            )
            
            logger.info(f"Facture créée: {facture.numero_facture} - HT: {facture.montant_ht}, TVA: {facture.montant_tva}, TTC: {facture.montant_ttc}")
            return facture
            
        except Exception as e:
            logger.error(f"Erreur critique création facture depuis bon {self.numero_bon}: {e}")
            raise
        
    def generer_numero_facture(self):
        """Génère un numéro de facture unique"""
        from .models import FactureFournisseur
        
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
    
    def generer_numero_unique(self):
        """Génère un numéro de bon unique pour cette entreprise - Version SÉCURISÉE"""
        from django.db import transaction
        from django.db.utils import IntegrityError
        import time

        annee = timezone.now().year
        prefix = f"BR-{annee}-"

        for _ in range(100):  # Limite de 100 tentatives pour éviter une boucle infinie
            # Trouver le dernier numéro pour cette entreprise et cette année
            dernier_bon = BonReception.objects.filter(
                entreprise=self.entreprise,
                numero_bon__startswith=prefix
            ).order_by('-numero_bon').first()

            if dernier_bon:
                try:
                    dernier_numero = int(dernier_bon.numero_bon.split('-')[-1])
                    nouveau_numero = dernier_numero + 1
                except (ValueError, IndexError):
                    nouveau_numero = 1
            else:
                nouveau_numero = 1

            numero_propose = f"{prefix}{nouveau_numero:04d}"

            # Vérifier en base si ce numéro existe déjà
            if not BonReception.objects.filter(
                entreprise=self.entreprise,
                numero_bon=numero_propose
            ).exists():
                return numero_propose

            # Si le numéro existe, attendre un peu et réessayer (éviter les collisions en concurrence)
            time.sleep(0.01)

        # Si on a épuisé les tentatives, lever une exception
        raise Exception("Impossible de générer un numéro de bon unique après 100 tentatives")

# Modèle LigneBonReception avec les champs nécessaires
class LigneBonReception(models.Model):
    bon = models.ForeignKey(BonReception, on_delete=models.CASCADE, related_name='lignes')
    ligne_commande = models.ForeignKey(
        'LigneCommandeAchat',
        on_delete=models.PROTECT,
        related_name='lignes_reception'
    )
    quantite = models.DecimalField(max_digits=10, decimal_places=2)
    prix_unitaire_ht = models.DecimalField(max_digits=10, decimal_places=2)  # Prix HT au moment de la réception
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Taux TVA au moment de la réception
    conditionnement = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ligne de bon de réception"
        verbose_name_plural = "Lignes de bons de réception"

    def save(self, *args, **kwargs):
        # FORCER la copie cohérente des données depuis la ligne de commande
        if self.ligne_commande:
            # Copier le prix unitaire HT
            if not self.prix_unitaire_ht:
                self.prix_unitaire_ht = self.ligne_commande.prix_unitaire
            
            # FORCER la copie du taux TVA depuis la ligne de commande
            # C'EST LA CORRECTION CRITIQUE
            if self.ligne_commande.taux_tva is not None:
                self.taux_tva = self.ligne_commande.taux_tva
            elif not self.taux_tva:
                self.taux_tva = Decimal('16.00')  # Fallback sécurisé
        
        super().save(*args, **kwargs)
        # Recalculer les totaux du bon après sauvegarde
        self.bon.calculer_totaux()

    def delete(self, *args, **kwargs):
        bon = self.bon
        super().delete(*args, **kwargs)
        # Recalculer les totaux du bon après suppression
        bon.calculer_totaux()

    def __str__(self):
        return f"Ligne BR {self.bon.numero_bon} - {self.ligne_commande.produit.nom} ({self.quantite.normalize()})"

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
    bon_reception = models.ForeignKey(
        'achats.BonReception', 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        related_name='factures'
    )
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
        is_new = self.pk is None
        
        if not self.numero_facture:
            self.numero_facture = self.generate_numero_facture()
        
        # S'assurer que les totaux sont cohérents
        if self.montant_ht and self.montant_tva:
            self.montant_ttc = self.montant_ht + self.montant_tva
        
        super().save(*args, **kwargs)

        # Créer l'écriture comptable uniquement pour les nouvelles factures validées
        if is_new and self.statut == 'validee':
            self.creer_ecriture_comptable()

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
    
    def creer_ecriture_comptable(self):
        """Crée l'écriture comptable pour la facture fournisseur - VERSION ULTIME CORRIGÉE"""
        from comptabilite.models import EcritureComptable, LigneEcriture, PlanComptableOHADA, JournalComptable
        
        try:
            # VÉRIFICATION CRITIQUE : Montants valides
            if self.montant_ttc <= Decimal('0.00') or self.montant_ht <= Decimal('0.00'):
                logger.error(f"Montants invalides pour la facture {self.numero_facture}: HT={self.montant_ht}, TTC={self.montant_ttc}")
                return None
            
            # Vérifier qu'une écriture n'existe pas déjà
            if self.get_ecritures_comptables().exists():
                logger.warning(f"Écriture existe déjà pour la facture {self.numero_facture}")
                return None
            
            # Récupérer les comptes nécessaires avec gestion d'erreur
            try:
                compte_achats = PlanComptableOHADA.objects.get(
                    numero='607',  # Achats de marchandises
                    entreprise=self.entreprise
                )
                
                compte_tva = PlanComptableOHADA.objects.get(
                    numero='4456',  # TVA déductible
                    entreprise=self.entreprise
                )
                
                compte_fournisseurs = PlanComptableOHADA.objects.get(
                    numero='401',  # Fournisseurs
                    entreprise=self.entreprise
                )
                
                journal_achats = JournalComptable.objects.get(
                    code='ACH',
                    entreprise=self.entreprise
                )
            except (PlanComptableOHADA.DoesNotExist, JournalComptable.DoesNotExist) as e:
                logger.error(f"Compte ou journal introuvable: {e}")
                return None
            
            # CORRECTION ULTIME : Créer l'écriture avec le bon montant DÈS LE DÉBUT
            ecriture = EcritureComptable(
                journal=journal_achats,
                date_ecriture=timezone.now(),
                date_comptable=self.date_facture,
                libelle=f"Facture {self.numero_facture} - {self.fournisseur.nom}",
                piece_justificative=self.numero_facture,
                montant_devise=self.montant_ttc,  # CORRECTION: Définir le montant IMMÉDIATEMENT
                entreprise=self.entreprise,
                created_by=self.created_by,
                facture_fournisseur_liee=self
            )
            ecriture.save()
            
            # Ligne 1: Débit des achats (HT)
            LigneEcriture.objects.create(
                ecriture=ecriture,
                compte=compte_achats,
                libelle=f"Achat marchandises - {self.fournisseur.nom}",
                debit=self.montant_ht,
                credit=Decimal('0.00'),
                entreprise=self.entreprise
            )
            
            # Ligne 2: Débit de la TVA déductible (si TVA > 0)
            if self.montant_tva > Decimal('0.00'):
                LigneEcriture.objects.create(
                    ecriture=ecriture,
                    compte=compte_tva,
                    libelle=f"TVA déductible - {self.fournisseur.nom}",
                    debit=self.montant_tva,
                    credit=Decimal('0.00'),
                    entreprise=self.entreprise
                )
            
            # Ligne 3: Crédit des fournisseurs (TTC)
            LigneEcriture.objects.create(
                ecriture=ecriture,
                compte=compte_fournisseurs,
                libelle=f"Dette fournisseur - {self.fournisseur.nom}",
                debit=Decimal('0.00'),
                credit=self.montant_ttc,
                entreprise=self.entreprise
            )
            
            # CORRECTION ULTIME : FORCER la validation et l'équilibrage
            ecriture.full_clean()  # Validation complète
            if not ecriture.est_equilibree:
                ecriture.equilibrer_ecriture()
            
            # CORRECTION ULTIME : Recalcul final pour garantir l'exactitude
            ecriture.recalculer_montant_devise()
            ecriture.save()  # Resauvegarder avec les valeurs finales
            
            logger.info(f"Écriture comptable créée pour la facture {self.numero_facture}: HT={self.montant_ht}, TVA={self.montant_tva}, TTC={self.montant_ttc}")
            return ecriture
            
        except Exception as e:
            logger.error(f"Erreur critique création écriture comptable: {e}")
            # En cas d'erreur, supprimer l'écriture incomplète
            if 'ecriture' in locals() and ecriture.pk:
                ecriture.delete()
            return None
    
    @property
    def montant_paye(self):
        """Retourne le montant total payé sur cette facture"""
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
        return self.paiements.all().order_by('-date_paiement')
    
    def update_statut(self):
        """Met à jour le statut de la facture en fonction des paiements"""
        montant_paye = self.montant_paye
        
        if montant_paye >= self.montant_ttc:
            nouveau_statut = 'payee'
        elif montant_paye > 0:
            nouveau_statut = 'partiellement_payee'
        elif self.statut != 'annulee':
            nouveau_statut = 'validee'
        else:
            nouveau_statut = self.statut
        
        if nouveau_statut != self.statut:
            self.statut = nouveau_statut
            self.save()
            

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
        is_new = self.pk is None
        
        if not self.reference:
            self.reference = self.generate_reference()
        
        super().save(*args, **kwargs)

        # Créer l'écriture comptable uniquement pour les nouveaux paiements validés
        if is_new and self.statut == 'valide':
            # Utiliser un délai pour éviter les problèmes de concurrence
            import threading
            def creer_ecriture_apres_delai():
                import time
                time.sleep(1)  # Délai plus long pour être sûr
                try:
                    # Recharger l'instance depuis la base
                    from .models import PaiementFournisseur
                    paiement_actualise = PaiementFournisseur.objects.get(pk=self.pk)
                    paiement_actualise.creer_ecriture_comptable()
                except Exception as e:
                    logger.error(f"Erreur création différée écriture: {e}")
            
            threading.Thread(target=creer_ecriture_apres_delai, daemon=True).start()
        
        # Mettre à jour le statut de la facture
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
        """Crée l'écriture comptable pour le paiement fournisseur - VERSION ULTIME CORRIGÉE"""
        from comptabilite.models import EcritureComptable, LigneEcriture, PlanComptableOHADA, JournalComptable
        
        try:
            logger.info(f"Tentative création écriture pour paiement {self.reference} (montant: {self.montant})")
            
            # VÉRIFICATION CRITIQUE : Montant valide
            if self.montant <= Decimal('0.00'):
                logger.error(f"Montant invalide pour le paiement {self.reference}: {self.montant}")
                return None
            
            # Vérifier qu'une écriture n'existe pas déjà
            if hasattr(self, 'ecritures_comptables') and self.ecritures_comptables.exists():
                logger.warning(f"Écriture existe déjà pour le paiement {self.reference}")
                return None
            
            # Récupérer les comptes nécessaires avec gestion d'erreur
            try:
                # Compte fournisseurs
                compte_fournisseurs = PlanComptableOHADA.objects.get(
                    numero='401',  # Fournisseurs
                    entreprise=self.entreprise
                )
                logger.info(f"Compte fournisseurs trouvé: {compte_fournisseurs.numero}")
                
                # Déterminer le compte de trésorerie en fonction du mode de paiement
                if self.mode_paiement == 'virement':
                    compte_numero = '521'  # Banque
                elif self.mode_paiement == 'cheque':
                    compte_numero = '511'  # Chèques à encaisser
                elif self.mode_paiement == 'espece':
                    compte_numero = '531'  # Caisse
                else:
                    compte_numero = '531'  # Caisse par défaut
                
                compte_tresorerie = PlanComptableOHADA.objects.get(
                    numero=compte_numero,
                    entreprise=self.entreprise
                )
                logger.info(f"Compte trésorerie trouvé: {compte_tresorerie.numero}")
                
                # Journal de trésorerie - VÉRIFICATION CRITIQUE
                try:
                    journal_tresorerie = JournalComptable.objects.get(
                        code='TRS',  # Journal de trésorerie
                        entreprise=self.entreprise
                    )
                except JournalComptable.DoesNotExist:
                    # Fallback: utiliser le journal de banque ou créer un journal TRS
                    try:
                        journal_tresorerie = JournalComptable.objects.get(
                            code='BQ',  # Journal de banque
                            entreprise=self.entreprise
                        )
                    except JournalComptable.DoesNotExist:
                        # Créer le journal TRS si nécessaire
                        journal_tresorerie = JournalComptable.objects.create(
                            code='TRS',
                            intitule='Journal de Trésorerie',
                            type_journal='banque',
                            entreprise=self.entreprise,
                            actif=True
                        )
                
                logger.info(f"Journal trouvé: {journal_tresorerie.code}")
                
            except (PlanComptableOHADA.DoesNotExist, JournalComptable.DoesNotExist) as e:
                logger.error(f"Compte ou journal introuvable: {e}")
                # Créer les comptes manquants automatiquement
                try:
                    PlanComptableOHADA.initialiser_plan_comptable(self.entreprise)
                    JournalComptable.initialiser_journaux(self.entreprise)
                    logger.info("Plan comptable initialisé automatiquement")
                    # Réessayer après initialisation
                    return self.creer_ecriture_comptable()
                except Exception as init_error:
                    logger.error(f"Erreur initialisation plan comptable: {init_error}")
                    return None
            
            # Créer l'écriture comptable avec le montant du paiement
            ecriture = EcritureComptable(
                journal=journal_tresorerie,
                date_ecriture=timezone.now(),
                date_comptable=self.date_paiement,
                libelle=f"Paiement {self.reference} - {self.facture.fournisseur.nom}",
                piece_justificative=self.reference,
                montant_devise=self.montant,
                entreprise=self.entreprise,
                created_by=self.created_by,
                paiement_fournisseur_lie=self
            )
            
            # CORRECTION: Sauvegarder d'abord l'écriture
            ecriture.save()
            logger.info(f"Écriture créée: {ecriture.numero}")
            
            # Ligne 1: Crédit des fournisseurs (diminution de la dette)
            LigneEcriture.objects.create(
                ecriture=ecriture,
                compte=compte_fournisseurs,
                libelle=f"Paiement fournisseur - {self.facture.fournisseur.nom}",
                debit=Decimal('0.00'),
                credit=self.montant,
                entreprise=self.entreprise
            )
            
            # Ligne 2: Débit de la trésorerie (diminution des disponibilités)
            LigneEcriture.objects.create(
                ecriture=ecriture,
                compte=compte_tresorerie,
                libelle=f"Paiement {self.get_mode_paiement_display()} - {self.facture.fournisseur.nom}",
                debit=self.montant,
                credit=Decimal('0.00'),
                entreprise=self.entreprise
            )
            
            # CORRECTION: Recalculer et équilibrer
            ecriture.recalculer_montant_devise()
            
            if not ecriture.est_equilibree:
                ecriture.equilibrer_ecriture()
            
            ecriture.save()
            
            logger.info(f"Écriture comptable créée avec succès pour le paiement {self.reference}")
            return ecriture
            
        except Exception as e:
            logger.error(f"ERREUR CRITIQUE création écriture comptable: {str(e)}", exc_info=True)
            # En cas d'erreur, supprimer l'écriture incomplète
            if 'ecriture' in locals() and hasattr(ecriture, 'pk') and ecriture.pk:
                ecriture.delete()
            return None