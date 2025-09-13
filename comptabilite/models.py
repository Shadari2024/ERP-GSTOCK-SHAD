from django.db import models
from django.utils.translation import gettext_lazy as _
from parametres.models import Entreprise
from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)
User = get_user_model()
class PlanComptableOHADA(models.Model):
    """Modèle pour le plan comptable OHADA"""
    classe = models.CharField(max_length=1, verbose_name=_("Classe"))
    numero = models.CharField(max_length=10, verbose_name=_("Numéro de compte"))
    intitule = models.CharField(max_length=200, verbose_name=_("Intitulé"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    type_compte = models.CharField(
        max_length=10,
        choices=[('actif', _('Actif')), ('passif', _('Passif')), ('charge', _('Charge')), ('produit', _('Produit'))],
        verbose_name=_("Type de compte")
    )
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Plan Comptable OHADA")
        verbose_name_plural = _("Plans Comptables OHADA")
        unique_together = ['numero', 'entreprise']
        ordering = ['numero']

    def __str__(self):
        return f"{self.numero} - {self.intitule}"

    @classmethod
    def initialiser_plan_comptable(cls, entreprise):
        """Initialise le plan comptable OHADA pour une entreprise - VERSION COMPLÈTE"""
        plan_comptable_ohada = [
            # Classe 1: Comptes de capitaux
            {'classe': '1', 'numero': '101', 'intitule': 'Capital social', 'type_compte': 'passif'},
            {'classe': '1', 'numero': '106', 'intitule': 'Réserves', 'type_compte': 'passif'},
            {'classe': '1', 'numero': '12', 'intitule': 'Résultat de l\'exercice', 'type_compte': 'passif'},
            
            # Classe 2: Comptes d'immobilisations
            {'classe': '2', 'numero': '21', 'intitule': 'Immobilisations incorporelles', 'type_compte': 'actif'},
            {'classe': '2', 'numero': '22', 'intitule': 'Immobilisations corporelles', 'type_compte': 'actif'},
            {'classe': '2', 'numero': '23', 'intitule': 'Immobilisations financières', 'type_compte': 'actif'},
            
            # Classe 3: Comptes de stocks
            {'classe': '3', 'numero': '31', 'intitule': 'Stocks', 'type_compte': 'actif'},
            {'classe': '3', 'numero': '37', 'intitule': 'Stocks de marchandises', 'type_compte': 'actif'},
            
            # Classe 4: Comptes de tiers - COMPTES ESSENTIELS POUR LES ACHATS
            # Classe 4: Comptes de tiers - COMPTES ESSENTIELS POUR LES ACHATS
            {'classe': '4', 'numero': '401', 'intitule': 'Fournisseurs', 'type_compte': 'passif'},
            {'classe': '4', 'numero': '4011', 'intitule': 'Fournisseurs nationaux', 'type_compte': 'passif'},
            {'classe': '4', 'numero': '4012', 'intitule': 'Fournisseurs internationaux', 'type_compte': 'passif'},
            {'classe': '4', 'numero': '411', 'intitule': 'Clients', 'type_compte': 'actif'},
            {'classe': '4', 'numero': '4455', 'intitule': 'TVA à décaisser', 'type_compte': 'passif'},
            {'classe': '4', 'numero': '4456', 'intitule': 'TVA déductible', 'type_compte': 'actif'},
            {'classe': '4', 'numero': '44566', 'intitule': 'TVA à décaisser (détail)', 'type_compte': 'passif'},
            {'classe': '4', 'numero': '471', 'intitule': 'Compte de régularisation', 'type_compte': 'passif'},  # AJOUT IMPORTANT
            # Classe 5: Comptes financiers - COMPTES DE TRÉSORERIE ESSENTIELS
            {'classe': '5', 'numero': '511', 'intitule': 'Chèques à encaisser', 'type_compte': 'actif'},
            {'classe': '5', 'numero': '512', 'intitule': 'Banques', 'type_compte': 'actif'},
            {'classe': '5', 'numero': '5121', 'intitule': 'Compte courant principal', 'type_compte': 'actif'},
            {'classe': '5', 'numero': '53', 'intitule': 'Caisse', 'type_compte': 'actif'},
            {'classe': '5', 'numero': '531', 'intitule': 'Caisse principale', 'type_compte': 'actif'},
            {'classe': '5', 'numero': '58', 'intitule': 'Autres moyens de paiement', 'type_compte': 'actif'},
            
            # Classe 6: Comptes de charges
            {'classe': '6', 'numero': '603', 'intitule': 'Variation des stocks', 'type_compte': 'charge'},
            {'classe': '6', 'numero': '6037', 'intitule': 'Variation des stocks (inventaires)', 'type_compte': 'charge'},
            {'classe': '6', 'numero': '607', 'intitule': 'Achats de marchandises', 'type_compte': 'charge'},
            {'classe': '6', 'numero': '61', 'intitule': 'Services extérieurs', 'type_compte': 'charge'},
            {'classe': '6', 'numero': '64', 'intitule': 'Charges de personnel', 'type_compte': 'charge'},
            {'classe': '6', 'numero': '65', 'intitule': 'Autres charges de gestion courante', 'type_compte': 'charge'},
            {'classe': '6', 'numero': '66', 'intitule': 'Charges financières', 'type_compte': 'charge'},
            {'classe': '6', 'numero': '67', 'intitule': 'Charges exceptionnelles', 'type_compte': 'charge'},
            {'classe': '6', 'numero': '68', 'intitule': 'Dotations aux amortissements et provisions', 'type_compte': 'charge'},
            
            # Classe 7: Comptes de produits
            {'classe': '7', 'numero': '70', 'intitule': 'Ventes', 'type_compte': 'produit'},
            {'classe': '7', 'numero': '71', 'intitule': 'Production stockée', 'type_compte': 'produit'},
            {'classe': '7', 'numero': '75', 'intitule': 'Autres produits de gestion courante', 'type_compte': 'produit'},
            {'classe': '7', 'numero': '76', 'intitule': 'Produits financiers', 'type_compte': 'produit'},
            {'classe': '7', 'numero': '77', 'intitule': 'Produits exceptionnels', 'type_compte': 'produit'},
          
        ]
        
        comptes_crees = []
        for compte_data in plan_comptable_ohada:
            try:
                compte, created = cls.objects.get_or_create(
                    numero=compte_data['numero'],
                    entreprise=entreprise,
                    defaults={
                        'classe': compte_data['classe'],
                        'intitule': compte_data['intitule'],
                        'type_compte': compte_data['type_compte'],
                        'description': f"Compte {compte_data['numero']} - {compte_data['intitule']}"
                    }
                )
                if created:
                    comptes_crees.append(compte)
            except Exception as e:
                logger.error(f"Erreur création compte {compte_data['numero']}: {e}")
        
        return comptes_crees

class JournalComptable(models.Model):
    """Modèle pour les journaux comptables"""
    code = models.CharField(max_length=10, verbose_name=_("Code journal"))
    intitule = models.CharField(max_length=100, verbose_name=_("Intitulé"))
    type_journal = models.CharField(
        max_length=20,
        choices=[
            ('achat', _('Achats')),
            ('vente', _('Ventes')),
            ('banque', _('Banque')),
            ('caisse', _('Caisse')),
            ('divers', _('Divers'))
        ],
        verbose_name=_("Type de journal")
    )
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    actif = models.BooleanField(default=True, verbose_name=_("Journal actif"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Journal Comptable")
        verbose_name_plural = _("Journaux Comptables")
        unique_together = ['code', 'entreprise']
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.intitule}"

    @classmethod
    def initialiser_journaux(cls, entreprise):
        """Initialise les journaux comptables pour une entreprise"""
        journaux = [
            {'code': 'ACH', 'intitule': 'Journal des Achats', 'type_journal': 'achat'},
            {'code': 'VT', 'intitule': 'Journal des Ventes', 'type_journal': 'vente'},
            {'code': 'BQ', 'intitule': 'Journal de Banque', 'type_journal': 'banque'},
            {'code': 'CA', 'intitule': 'Journal de Caisse', 'type_journal': 'caisse'},
            {'code': 'OD', 'intitule': 'Journal des Opérations Diverses', 'type_journal': 'divers'},
            {'code': 'STK', 'intitule': 'Journal des Stocks', 'type_journal': 'divers'},  # AJOUT IMPORTANT
        ]
        
        journaux_crees = []
        for journal_data in journaux:
            try:
                journal, created = cls.objects.get_or_create(
                    code=journal_data['code'],
                    entreprise=entreprise,
                    defaults={
                        'intitule': journal_data['intitule'],
                        'type_journal': journal_data['type_journal']
                    }
                )
                if created:
                    journaux_crees.append(journal)
            except Exception as e:
                logger.error(f"Erreur création journal {journal_data['code']}: {e}")
        
        return journaux_crees
# comptabilite/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from parametres.models import Entreprise
from django.contrib.auth import get_user_model
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from decimal import Decimal
import logging
import time
import uuid

logger = logging.getLogger(__name__)
User = get_user_model()

class EcritureComptable(models.Model):
    """Modèle pour les écritures comptables"""
    journal = models.ForeignKey('JournalComptable', on_delete=models.PROTECT, verbose_name=_("Journal"))
    numero = models.CharField(max_length=20, verbose_name=_("Numéro d'écriture"))
    date_ecriture = models.DateTimeField(verbose_name=_("Date d'écriture"))
    date_comptable = models.DateField(verbose_name=_("Date comptable"))
    libelle = models.CharField(max_length=200, verbose_name=_("Libellé"))
    piece_justificative = models.CharField(max_length=100, blank=True, verbose_name=_("Pièce justificative"))
    montant_devise = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_("Montant en devise"))
    montant_devise_etrangere = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, verbose_name=_("Montant en devise étrangère"))
    code_devise_etrangere = models.CharField(max_length=3, blank=True, verbose_name=_("Code devise étrangère"))
    taux_change = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True, verbose_name=_("Taux de change"))
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='ecritures_crees', verbose_name=_("Créé par"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Relations avec les autres apps
    bon_reception_lie = models.ForeignKey(
        'achats.BonReception',
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_("Bon de réception lié")
    )
    facture_fournisseur_liee = models.ForeignKey(
        'achats.FactureFournisseur',
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_("Facture fournisseur liée")
    )
    vente_liee = models.ForeignKey(
        'ventes.VentePOS',
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_("Vente liée")
    )
    paiement_lie = models.ForeignKey(
        'ventes.Paiement',
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_("Paiement lié")
    )
    # Dans le modèle EcritureComptable, ajouter ce champ :
    paiement_fournisseur_lie = models.ForeignKey(
        'achats.PaiementFournisseur',
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_("Paiement fournisseur lié")
    )
    
    paiement_pos = models.ForeignKey(
        'ventes.PaiementPOS',
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_("Paiement lié (POS)")
    )
    mouvement_stock_lie = models.ForeignKey(
        'STOCK.MouvementStock',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Mouvement de stock lié")
    )

    class Meta:
        verbose_name = _("Écriture Comptable")
        verbose_name_plural = _("Écritures Comptables")
        unique_together = ['numero', 'entreprise']
        ordering = ['-date_ecriture', '-numero']

    def __str__(self):
        return f"{self.numero} - {self.libelle}"
    
    def clean(self):
        """Validation des données avant sauvegarde"""
        from django.core.exceptions import ValidationError
        
        # Vérifier la cohérence du montant avec les lignes
        total_debit = Decimal('0.00')
        total_credit = Decimal('0.00')
        
        # Calculer les totaux à partir des lignes existantes
        if self.pk:
            for ligne in self.lignes.all():
                total_debit += ligne.debit
                total_credit += ligne.credit
        
        # Vérifier l'équilibre débit/crédit
        if total_debit != total_credit:
            raise ValidationError(
                f"Le total débit ({total_debit}) doit égaler le total crédit ({total_credit})"
            )
        
        # Vérifier la cohérence du montant devise
        if self.montant_devise != total_debit:
            raise ValidationError(
                f"Le montant devise ({self.montant_devise}) doit correspondre au total débit ({total_debit})"
            )
    
    def save(self, *args, **kwargs):
        # Générer un numéro unique si nécessaire
        if not self.numero:
            self.numero = self.generate_numero_unique()
        
        # CORRECTION DÉFINITIVE : Sauvegarder d'abord sans validation
        super().save(*args, **kwargs)
        
        # CORRECTION DÉFINITIVE : Toujours recalculer après sauvegarde
        self.recalculer_montant_devise()
        
    def recalculer_montant_devise(self):
        """Recalcule et met à jour le montant_devise basé sur les lignes - VERSION DÉFINITIVE"""
        total_debit = Decimal('0.00')
        
        for ligne in self.lignes.all():
            total_debit += ligne.debit
        
        # CORRECTION DÉFINITIVE : Mettre à jour seulement si différent ET valide
        if total_debit > Decimal('0.00') and self.montant_devise != total_debit:
            self.montant_devise = total_debit
            # Sauvegarder sans déclencher les validations pour éviter les boucles
            super(EcritureComptable, self).save(update_fields=['montant_devise'])
            logger.info(f"Montant devise recalculé pour écriture {self.numero}: {total_debit}")
    
    def equilibrer_ecriture(self):
        """Équilibre automatiquement l'écriture si nécessaire"""
        total_debit = Decimal('0.00')
        total_credit = Decimal('0.00')
        
        for ligne in self.lignes.all():
            total_debit += ligne.debit
            total_credit += ligne.credit
        
        difference = total_debit - total_credit
        
        if difference != Decimal('0.00'):
            # Trouver un compte pour équilibrer (compte de régularisation)
            try:
                compte_regularisation = PlanComptableOHADA.objects.get(
                    numero='471',  # Compte de régularisation
                    entreprise=self.entreprise
                )
                
                # Créer une ligne d'équilibrage
                if difference > 0:
                    # Trop de débit, ajouter du crédit
                    LigneEcriture.objects.create(
                        ecriture=self,
                        compte=compte_regularisation,
                        libelle="Ajustement d'équilibre",
                        debit=Decimal('0.00'),
                        credit=difference,
                        entreprise=self.entreprise
                    )
                else:
                    # Trop de crédit, ajouter du débit
                    LigneEcriture.objects.create(
                        ecriture=self,
                        compte=compte_regularisation,
                        libelle="Ajustement d'équilibre",
                        debit=abs(difference),
                        credit=Decimal('0.00'),
                        entreprise=self.entreprise
                    )
                
                logger.info(f"Écriture {self.numero} équilibrée: différence {difference}")
                
            except PlanComptableOHADA.DoesNotExist:
                logger.error("Compte de régularisation 471 introuvable")
                # Créer le compte de régularisation automatiquement
                compte_regularisation = PlanComptableOHADA.objects.create(
                    classe='4',
                    numero='471',
                    intitule='Compte de régularisation',
                    type_compte='passif',
                    entreprise=self.entreprise,
                    description='Compte utilisé pour équilibrer les écritures comptables'
                )
                # Réessayer l'équilibrage
                self.equilibrer_ecriture()

    @property
    def est_equilibree(self):
        """Vérifie si l'écriture est équilibrée"""
        total_debit = Decimal('0.00')
        total_credit = Decimal('0.00')
        
        for ligne in self.lignes.all():
            total_debit += ligne.debit
            total_credit += ligne.credit
        
        return total_debit == total_credit

    @property
    def total_debit(self):
        """Retourne le total débit de l'écriture"""
        return sum(ligne.debit for ligne in self.lignes.all())

    @property
    def total_credit(self):
        """Retourne le total crédit de l'écriture"""
        return sum(ligne.credit for ligne in self.lignes.all())
    
    def generate_numero_unique(self):
        """Génère un numéro unique par entreprise, journal et date"""
        from django.db.models import Max
        
        date_str = self.date_ecriture.strftime('%Y%m%d')
        journal_code = self.journal.code
        
        # Trouver le dernier numéro pour cette entreprise, ce journal et cette date
        last_ecriture = EcritureComptable.objects.filter(
            entreprise=self.entreprise,
            journal=self.journal,
            date_ecriture__date=self.date_ecriture.date()
        ).order_by('-numero').first()
        
        sequence = 1
        if last_ecriture and last_ecriture.numero:
            try:
                # Extraire la séquence du dernier numéro
                parts = last_ecriture.numero.split('-')
                if len(parts) >= 3:
                    sequence_str = parts[-1]
                    sequence = int(sequence_str) + 1
            except (ValueError, IndexError):
                # En cas d'erreur, utiliser le count
                count = EcritureComptable.objects.filter(
                    entreprise=self.entreprise,
                    journal=self.journal,
                    date_ecriture__date=self.date_ecriture.date()
                ).count()
                sequence = count + 1
        
        return f"{journal_code}-{date_str}-{sequence:04d}"

    

class LigneEcriture(models.Model):
    """Modèle pour les lignes d'écriture comptable"""
    ecriture = models.ForeignKey(EcritureComptable, on_delete=models.CASCADE, related_name='lignes', verbose_name=_("Écriture"))
    compte = models.ForeignKey(PlanComptableOHADA, on_delete=models.PROTECT, verbose_name=_("Compte"))
    libelle = models.CharField(max_length=200, verbose_name=_("Libellé"))
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_("Débit"))
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_("Crédit"))
    contrepartie = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_("Contrepartie"))
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("Ligne d'écriture")
        verbose_name_plural = _("Lignes d'écriture")
        ordering = ['ecriture', 'id']

    def __str__(self):
        return f"{self.ecriture.numero} - {self.compte.numero}"

    def save(self, *args, **kwargs):
        # S'assurer que l'entreprise est définie
        if not self.entreprise_id and self.ecriture:
            self.entreprise = self.ecriture.entreprise
        super().save(*args, **kwargs)

class CompteAuxiliaire(models.Model):
    """Modèle pour les comptes auxiliaires (clients, fournisseurs)"""
    TYPE_COMPTE = (
        ('client', _('Client')),
        ('fournisseur', _('Fournisseur')),
        ('autre', _('Autre')),
    )
    
    code = models.CharField(max_length=20, verbose_name=_("Code"))
    intitule = models.CharField(max_length=200, verbose_name=_("Intitulé"))
    type_compte = models.CharField(max_length=20, choices=TYPE_COMPTE, verbose_name=_("Type de compte"))
    compte_general = models.ForeignKey(PlanComptableOHADA, on_delete=models.PROTECT, verbose_name=_("Compte général"))
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    actif = models.BooleanField(default=True, verbose_name=_("Compte actif"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Compte Auxiliary")
        verbose_name_plural = _("Comptes Auxiliaires")
        unique_together = ['code', 'entreprise']
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.intitule}"

# Signal pour initialiser automatiquement le plan comptable après la migration
@receiver(post_migrate)
def initialiser_plan_comptable_par_defaut(sender, **kwargs):
    if sender.name == 'comptabilite':
        try:
            from parametres.models import Entreprise
            # Initialiser pour toutes les entreprises existantes
            for entreprise in Entreprise.objects.all():
                PlanComptableOHADA.initialiser_plan_comptable(entreprise)
                JournalComptable.initialiser_journaux(entreprise)
                logger.info(f"Plan comptable initialisé pour {entreprise.nom}")
        except Exception as e:
            logger.error(f"Erreur initialisation plan comptable: {e}")