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
        """Initialise le plan comptable OHADA pour une entreprise"""
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
            
            # Classe 4: Comptes de tiers
            {'classe': '4', 'numero': '401', 'intitule': 'Fournisseurs', 'type_compte': 'passif'},
            {'classe': '4', 'numero': '411', 'intitule': 'Clients', 'type_compte': 'actif'},
            
            # Classe 5: Comptes financiers
            {'classe': '5', 'numero': '51', 'intitule': 'Banques', 'type_compte': 'actif'},
            {'classe': '5', 'numero': '53', 'intitule': 'Caisse', 'type_compte': 'actif'},
            
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

class EcritureComptable(models.Model):
    """Modèle pour les écritures comptables"""
    journal = models.ForeignKey(JournalComptable, on_delete=models.PROTECT, verbose_name=_("Journal"))
    numero = models.CharField(max_length=20, verbose_name=_("Numéro d'écriture"))
    date_ecriture = models.DateTimeField(verbose_name=_("Date d'écriture"))  # Changé en DateTimeField
    date_comptable = models.DateField(verbose_name=_("Date comptable"))
    libelle = models.CharField(max_length=200, verbose_name=_("Libellé"))
    piece_justificative = models.CharField(max_length=100, blank=True, verbose_name=_("Pièce justificative"))
    montant_devise = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_("Montant en devise"))  # Ajout default=0
    montant_devise_etrangere = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True, verbose_name=_("Montant en devise étrangère"))
    code_devise_etrangere = models.CharField(max_length=3, blank=True, verbose_name=_("Code devise étrangère"))
    taux_change = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True, verbose_name=_("Taux de change"))
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='ecritures_crees', verbose_name=_("Créé par"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Relations avec les autres apps - CORRECTION DES RELATIONS
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
    
    def save(self, *args, **kwargs):
        # Si pas de numéro, en générer un
        if not self.numero:
            self.numero = f"{self.journal.code}-{self.date_ecriture.strftime('%Y%m%d')}-0001"
        
        # Calculer le montant total automatiquement à partir des lignes
        if self.pk and hasattr(self, 'lignes'):
            total_debit = sum(float(ligne.debit) for ligne in self.lignes.all())
            self.montant_devise = total_debit
        
        super().save(*args, **kwargs)

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