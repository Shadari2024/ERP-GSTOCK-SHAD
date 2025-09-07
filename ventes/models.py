# ventes/models.py
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
import decimal
import random
import string
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
import decimal
import decimal
import random
import string
import logging # Import logging
from django.urls import reverse
from django.forms import inlineformset_factory
from parametres.models import Entreprise # <-- Keep this import
from STOCK.models import Produit, Client # <-- Keep these imports
import datetime
from comptabilite.models import *
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError


logger = logging.getLogger(__name__)

class Devis(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('envoye', 'Envoyé'),
        ('accepte', 'Accepté'),  # Doit correspondre à 'accepte'
        ('refuse', 'Refusé'),
        ('annule', 'Annulé')
    ]

    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    numero = models.CharField(max_length=50, unique=True, blank=True)
    date = models.DateField()
    echeance = models.DateField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    remise = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_devis_number(self):
        """Génère un numéro de devis unique sous la forme DEV-AAAA-MM-JJ-XXXXX"""
        date_part = self.date.strftime('%Y-%m-%d') if self.date else datetime.now().strftime('%Y-%m-%d')
        random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
        return f"DEV-{date_part}-{random_part}"

    def save(self, *args, **kwargs):
        if not self.numero:
            # On génère un nouveau numéro jusqu'à en trouver un qui n'existe pas
            max_attempts = 10
            for _ in range(max_attempts):
                new_numero = self.generate_devis_number()
                if not Devis.objects.filter(numero=new_numero).exists():
                    self.numero = new_numero
                    break
            else:
                # Si on n'a pas trouvé de numéro unique après 10 essais
                raise ValueError("Impossible de générer un numéro de devis unique")
        super().save(*args, **kwargs)

    @property
    def total_ht(self):
        return sum((item.montant_ht for item in self.items.all() if item.montant_ht is not None), decimal.Decimal('0.00'))

    @property
    def total_tva(self):
        return sum((item.montant_tva for item in self.items.all() if item.montant_tva is not None), decimal.Decimal('0.00'))

    @property
    def total_avant_remise(self):
        return self.total_ht + self.total_tva

    @property
    def montant_remise_calcule(self):
        if self.remise and self.remise > 0:
            return self.total_avant_remise * (self.remise / decimal.Decimal('100.00'))
        return decimal.Decimal('0.00')

    @property
    def total_ttc(self):
        return self.total_avant_remise - self.montant_remise_calcule

    def __str__(self):
        return f"Devis {self.numero} - {self.client.nom}"
    

class LigneDevis(models.Model):
    devis = models.ForeignKey(Devis, related_name='items', on_delete=models.CASCADE)
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT)
    quantite = models.DecimalField(max_digits=10, decimal_places=2)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2)
    montant_ht = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.00'))
    montant_tva = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.00'))

    def save(self, *args, **kwargs):
        self.quantite = decimal.Decimal(str(self.quantite or '0'))
        self.prix_unitaire = decimal.Decimal(str(self.prix_unitaire or '0.00'))
        self.taux_tva = decimal.Decimal(str(self.taux_tva or '0.00'))

        self.montant_ht = self.quantite * self.prix_unitaire
        self.montant_tva = self.montant_ht * (self.taux_tva / decimal.Decimal('100.00'))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.produit.libelle} - {self.quantite} x {self.prix_unitaire}"
    

# --- NOUVEAUX MODÈLES OU MISES À JOUR ---

class DevisStatutHistory(models.Model):
    """
    Modèle pour enregistrer l'historique des changements de statut d'un Devis.
    """
    devis = models.ForeignKey(Devis, on_delete=models.CASCADE, related_name='status_history')
    
    # Noms des champs corrigés pour correspondre à ceux utilisés dans la vue
    ancien_statut = models.CharField(max_length=20, null=True, blank=True) # Statut précédent
    nouveau_statut = models.CharField(max_length=20) # Nouveau statut
    
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    commentaire = models.TextField(blank=True, null=True) # Commentaire sur le changement (ex: "Envoyé par email")

    class Meta:
        verbose_name = "Historique Statut Devis"
        verbose_name_plural = "Historiques Statuts Devis"
        ordering = ['-changed_at'] # Tri par le plus récent en premier

    def __str__(self):
        return f"Devis {self.devis.numero}: {self.ancien_statut or 'N/A'} -> {self.nouveau_statut} par {self.changed_by} à {self.changed_at.strftime('%Y-%m-%d %H:%M')}"

class DevisAuditLog(models.Model):
    """
    Modèle pour un journal d'audit général des actions importantes sur les Devis.
    """
    ACTION_CHOICES = [
        ('creation', 'Création'),
        ('modification', 'Modification'),
        ('suppression', 'Suppression'),
        ('envoi_email', 'Envoi Email'),
        ('changement_statut', 'Changement de Statut'),
        ('impression_pdf', 'Impression PDF'),
        # Ajoutez d'autres types d'actions si nécessaire
    ]

    devis = models.ForeignKey(Devis, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    # Permet de logguer une action même si le devis est supprimé (devis=None)
    
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField(blank=True, null=True)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='devis_audit_actions')
    performed_at = models.DateTimeField(auto_now_add=True)
    
    # Champ pour stocker des données additionnelles en JSON si besoin
    # from django.contrib.postgres.fields import JSONField # Pour PostgreSQL
    # details = JSONField(blank=True, null=True) # Pour d'autres DB, utilisez JSONField si disponible, sinon models.JSONField pour Django >= 3.1
    details = models.JSONField(blank=True, null=True) # Django 3.1+

    class Meta:
        verbose_name = "Journal d'Audit Devis"
        verbose_name_plural = "Journaux d'Audit Devis"
        ordering = ['-performed_at']

    def __str__(self):
        return f"[{self.performed_at.strftime('%Y-%m-%d %H:%M')}] {self.action} sur Devis #{self.devis.numero if self.devis else 'N/A'} par {self.performed_by}"
    
import decimal
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.db.models import Sum

# Assurez-vous que tous vos modèles et imports nécessaires sont présents
# from .models import Devis, LigneDevis, DevisStatutHistory, DevisAuditLog # Pour Devis
# from parametres.models import Entreprise, Devise # Pour Entreprise et Devise

# Votre modèle Commande
class Commande(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('Confirmee', 'Confirmée'),  # 'Confirmee' avec majuscule
        ('expedie', 'Expédié'),
        ('livre', 'Livré'),
        ('annule', 'Annulé'),
    ]

    entreprise = models.ForeignKey('parametres.Entreprise', on_delete=models.CASCADE)
    client = models.ForeignKey('STOCK.Client', on_delete=models.CASCADE)
    devis = models.ForeignKey('Devis', on_delete=models.SET_NULL, null=True, blank=True)
    numero = models.CharField(max_length=50, unique=True, blank=True, null=True)
    date = models.DateField(default=timezone.now)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='commandes_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    total_ht = models.DecimalField(max_digits=10, decimal_places=2, default=decimal.Decimal('0.00'))
    total_tva = models.DecimalField(max_digits=10, decimal_places=2, default=decimal.Decimal('0.00'))
    total_ttc = models.DecimalField(max_digits=10, decimal_places=2, default=decimal.Decimal('0.00'))

    def save(self, *args, **kwargs):
        # Générer le numéro de commande si c'est une nouvelle commande
        if not self.numero:
            prefix = f"CMD-{self.entreprise.code}-"
            last_commande = Commande.objects.filter(entreprise=self.entreprise, numero__startswith=prefix).order_by('-numero').first()
            if last_commande and last_commande.numero:
                try:
                    last_num = int(last_commande.numero.split('-')[-1])
                    new_num = last_num + 1
                except ValueError:
                    new_num = 1
            else:
                new_num = 1
            self.numero = f"{prefix}{new_num:05d}" # Formatage: CMD-ABC-00001
            
        super().save(*args, **kwargs)

    @property
    def is_cancelled(self):
        return self.statut == 'annule'

    @property
    def is_final(self):
        return self.statut in ['livre', 'annule', 'rembourse']

    def __str__(self):
        # Assurez-vous que self.client existe et a un attribut nom
        client_name = self.client.nom if self.client else "Client inconnu"
        return f"Commande {self.numero or 'N/A'} - {client_name}"

    def update_status(self, new_status, changed_by, comment=""):
        """
        Met à jour le statut de la commande, enregistre l'historique et l'action.
        Inclut des validations de base pour les transitions de statut basées sur la logique métier.
        """
        # 1. Validation du statut : le nouveau statut doit être valide
        if new_status not in [choice[0] for choice in self.STATUT_CHOICES]:
            raise ValueError(f"Statut '{new_status}' invalide pour la commande.")

        old_status = self.statut

        # 2. Règle générale : Empêcher les changements si déjà dans un état final (sauf pour remboursement depuis livré)
        # Permet de passer de 'livre' à 'rembourse'
        if old_status == 'livre' and new_status not in ['rembourse', 'annule', 'expedie']:
            raise ValueError(f"Depuis 'Livrée', le statut ne peut être que 'Remboursée', 'Annulée' ou 'Expédiée'.")
        # 3. Règles de transition spécifiques :
        # Brouillon -> En attente de paiement / Confirmée / Annulée
        if old_status == 'brouillon' and new_status not in ['en_attente_paiement', 'confirme', 'annule']:
            raise ValueError(f"Depuis 'Brouillon', le statut ne peut être que 'En attente de paiement', 'Confirmée' ou 'Annulée'.")

        # En attente de paiement -> Confirmée / Annulée
        if old_status == 'en_attente_paiement' and new_status not in ['confirme', 'annule']:
            raise ValueError(f"Depuis 'En attente de paiement', le statut ne peut être que 'Confirmée' ou 'Annulée'.")

        # Confirmée -> En préparation / Expédiée (directement) / Annulée
        if old_status == 'confirme' and new_status not in ['en_preparation', 'expedie', 'annule']:
             raise ValueError(f"Depuis 'Confirmée', le statut ne peut être que 'En préparation', 'Expédiée' ou 'Annulée'.")

        # En préparation -> Expédiée / Annulée
        if old_status == 'en_preparation' and new_status not in ['expedie', 'annule']:
            raise ValueError(f"Depuis 'En préparation', le statut ne peut être que 'Expédiée' ou 'Annulée'.")

        # Expédiée -> Livrée / Annulée
        if old_status == 'expedie' and new_status not in ['livre', 'annule']:
            raise ValueError(f"Depuis 'Expédiée', le statut ne peut être que 'Livrée' ou 'Annulée'.")
            
        # *** LA LIGNE MODIFIÉE ICI POUR AUTORISER 'ANNULE' DEPUIS 'LIVRE' ***
        if old_status == 'livre' and new_status not in ['rembourse', 'annule']: # AJOUT DE 'annule'
            raise ValueError(f"Depuis 'Livrée', le statut ne peut être que 'Remboursée' ou 'Annulée'.")

        # Annulée / Remboursée -> Aucun changement (règle finale déjà gérée ci-dessus, mais peut être explicité)
        # Exception : 'livre' peut passer à 'rembourse'
        if old_status in ['annule', 'rembourse'] and new_status != old_status:
             if not (old_status == 'livre' and new_status == 'rembourse'):
                raise ValueError(f"Une commande '{self.get_statut_display()}' ne peut plus changer de statut.")

        # Si le statut ne change pas, ne rien faire
        if old_status == new_status:
            return False 

        # Si toutes les validations passent, mettez à jour le statut
        self.statut = new_status
        self.save(update_fields=['statut', 'updated_at']) # Sauvegarder uniquement les champs modifiés pour l'efficacité

        # 4. Enregistrement de l'historique de statut
        # Assurez-vous que CommandeStatutHistory est importé
        CommandeStatutHistory.objects.create(
            commande=self,
            ancien_statut=old_status,
            nouveau_statut=new_status,
            changed_by=changed_by,
            commentaire=comment
        )

        # 5. Création du log d'audit
        # Assurez-vous que CommandeAuditLog est importé
        CommandeAuditLog.objects.create(
            commande=self,
            action='changement_statut',
            description=f"Statut de Commande #{self.numero} changé de '{old_status}' à '{new_status}'.",
            performed_by=changed_by,
            details={'old_status': old_status, 'new_status': new_status, 'comment': comment}
        )
        return True # Le statut a été modifié avec succès

    def calculer_totaux(self):
        """
        Calcule les totaux HT, TVA et TTC de la commande à partir des lignes de commande.
        """
        items = self.items.all() # assuming related_name='items' for LigneCommande
        total_ht = items.aggregate(sum_ht=Sum('montant_ht'))['sum_ht'] or decimal.Decimal('0.00')
        total_tva = items.aggregate(sum_tva=Sum('montant_tva'))['sum_tva'] or decimal.Decimal('0.00')

        self.total_ht = total_ht
        self.total_tva = total_tva
        self.total_ttc = total_ht + total_tva
        self.save(update_fields=['total_ht', 'total_tva', 'total_ttc', 'updated_at'])

# ... (Vos autres modèles LigneCommande, CommandeStatutHistory, CommandeAuditLog) ...
# Assurez-vous que LigneCommande a un save() et delete() qui appellent commande.calculer_totaux()
# et que CommandeAuditLog existe comme défini précédemment.

# --- Votre modèle LigneCommande (inchangé, mais j'ajoute un appel au recalcul des totaux) ---
class LigneCommande(models.Model):
    commande = models.ForeignKey(Commande, related_name='items', on_delete=models.CASCADE)
    produit = models.ForeignKey('STOCK.Produit', on_delete=models.PROTECT)
    quantite = models.DecimalField(max_digits=10, decimal_places=2)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2)
    montant_ht = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.00'))
    montant_tva = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.00'))

    def save(self, *args, **kwargs):
        self.quantite = decimal.Decimal(str(self.quantite or '0'))
        self.prix_unitaire = decimal.Decimal(str(self.prix_unitaire or '0.00'))
        self.taux_tva = decimal.Decimal(str(self.taux_tva or '0.00'))

        self.montant_ht = self.quantite * self.prix_unitaire
        self.montant_tva = self.montant_ht * (self.taux_tva / decimal.Decimal('100.00'))
        super().save(*args, **kwargs)
        # Après la sauvegarde d'une ligne, recalculer les totaux de la commande parente
        self.commande.calculer_totaux()

    def delete(self, *args, **kwargs):
        commande = self.commande
        super().delete(*args, **kwargs)
        # Après la suppression d'une ligne, recalculer les totaux de la commande parente
        commande.calculer_totaux()

    def __str__(self):
        return f"{self.produit.nom} - {self.quantite} x {self.prix_unitaire}"

# --- Votre modèle CommandeStatutHistory (inchangé) ---
class CommandeStatutHistory(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='status_history')
    ancien_statut = models.CharField(max_length=20, null=True, blank=True)
    nouveau_statut = models.CharField(max_length=20)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    commentaire = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Historique Statut Commande"
        verbose_name_plural = "Historiques Statuts Commande"
        ordering = ['-changed_at']

    def __str__(self):
        return f"Commande {self.commande.numero}: {self.ancien_statut or 'N/A'} -> {self.nouveau_statut} par {self.changed_by} à {self.changed_at.strftime('%Y-%m-%d %H:%M')}"

# --- Votre modèle CommandeAuditLog (Assurez-vous qu'il existe ou créez-le) ---
# Vous n'avez pas fourni ce modèle, mais il est appelé dans update_status.
# Voici un exemple de ce à quoi il pourrait ressembler :
class CommandeAuditLog(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=100) # e.g., 'changement_statut', 'creation', 'modification'
    description = models.TextField()
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(default=dict, blank=True, null=True) # Pour stocker des infos supplémentaires

    class Meta:
        verbose_name = "Log d'Audit Commande"
        verbose_name_plural = "Logs d'Audit Commande"
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {self.action} sur Commande {self.commande.numero} par {self.performed_by}: {self.description}"


# --- Your existing CommandeAuditLog Model ---
class CommandeAuditLog(models.Model):
    ACTION_CHOICES = [
        ('creation', 'Création'),
        ('modification', 'Modification'),
        ('suppression', 'Suppression'),
        ('changement_statut', 'Changement de Statut'),
        ('paiement_enregistre', 'Paiement Enregistré'),
        ('conversion_devis', 'Conversion depuis Devis'),
        ('alert_fraude', 'Alerte Fraude'), # Added from previous discussion
        # Add other actions as needed
    ]

    commande = models.ForeignKey(Commande, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField(blank=True, null=True)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='commande_audit_actions')
    performed_at = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(blank=True, null=True)

    class Meta:
        verbose_name = "Journal d'Audit Commande"
        verbose_name_plural = "Journaux d'Audit Commande"
        ordering = ['-performed_at']

    def __str__(self):
        return f"[{self.performed_at.strftime('%Y-%m-%d %H:%M')}] {self.action} sur Commande #{self.commande.numero if self.commande else 'N/A'} par {self.performed_by}"

from django.db import models, transaction, IntegrityError
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class BonLivraison(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('prepare', 'Préparé'),
        ('expedie', 'Expédié'),
        ('livre', 'Livré'),
        ('annule', 'Annulé'),
    ]

    entreprise = models.ForeignKey('parametres.Entreprise', on_delete=models.CASCADE)
    commande = models.ForeignKey('ventes.Commande', on_delete=models.CASCADE, related_name='livraisons')
    numero = models.CharField(max_length=50, blank=True)
    date = models.DateField(default=timezone.now)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='prepare')
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    total_ht = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_tva = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_ttc = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        unique_together = ['entreprise', 'numero']  # Numéro unique par entreprise

    def generate_bl_number(self):
        """
        Génère un numéro de BL unique pour l'entreprise
        """
        today = timezone.now().date()
        prefix = f"BL-{today.year}-"
        
        # Trouver le dernier numéro utilisé pour cette entreprise
        last_bl = BonLivraison.objects.filter(
            entreprise=self.entreprise,
            numero__startswith=prefix
        ).order_by('-numero').first()
        
        if last_bl and last_bl.numero:
            try:
                num_part = int(last_bl.numero.split('-')[-1])
                next_num = num_part + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1
        
        return f"{prefix}{next_num:04d}"

    def update_totals(self):
        """
        Met à jour les totaux à partir des lignes
        """
        total_ht_sum = sum(
            (item.montant_ht for item in self.items.all() if item.montant_ht is not None),
            Decimal('0.00')
        )
        total_tva_sum = sum(
            (item.montant_tva for item in self.items.all() if item.montant_tva is not None),
            Decimal('0.00')
        )
        
        self.total_ht = total_ht_sum
        self.total_tva = total_tva_sum
        self.total_ttc = total_ht_sum + total_tva_sum

    def save(self, *args, **kwargs):
        """
        Sauvegarde avec gestion des numéros uniques
        """
        if not self.numero:
            # Générer le numéro avant de sauvegarder
            self.numero = self.generate_bl_number()
        
        # Essayer de sauvegarder avec gestion des conflits
        max_attempts = 5
        for attempt in range(max_attempts):
            try:
                super().save(*args, **kwargs)
                return
            except IntegrityError as e:
                if 'numero' in str(e) and attempt < max_attempts - 1:
                    # Regénérer un nouveau numéro en cas de conflit
                    today = timezone.now().date()
                    prefix = f"BL-{today.year}-"
                    timestamp = int(time.time() % 1000)
                    self.numero = f"{prefix}{timestamp:04d}"
                    continue
                else:
                    raise

    @property
    def total_ht_calc(self):
        return sum(
            (item.montant_ht for item in self.items.all() if item.montant_ht is not None),
            Decimal('0.00')
        )
    
    @property
    def total_tva_calc(self):
        return sum(
            (item.montant_tva for item in self.items.all() if item.montant_tva is not None),
            Decimal('0.00')
        )
    
    @property
    def total_ttc_calc(self):
        return self.total_ht_calc + self.total_tva_calc
    
    def __str__(self):
        return f"BL {self.numero} - {self.commande.client.nom}"

    def update_status(self, new_status, changed_by, comment=""):
        """
        Met à jour le statut du bon de livraison
        """
        if new_status not in [choice[0] for choice in self.STATUT_CHOICES]:
            raise ValueError(f"Statut '{new_status}' invalide pour le bon de livraison.")

        old_status = self.statut

        if old_status != new_status:
            self.statut = new_status
            self.save(update_fields=['statut', 'updated_at'])

            # Historique du statut
            BonLivraisonStatutHistory.objects.create(
                bon_livraison=self,
                ancien_statut=old_status,
                nouveau_statut=new_status,
                changed_by=changed_by,
                commentaire=comment
            )
            

class LigneBonLivraison(models.Model):
    bon_livraison = models.ForeignKey(BonLivraison, related_name='items', on_delete=models.CASCADE)
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT) # Consistent with 'produit'
    quantite = models.DecimalField(max_digits=10, decimal_places=2)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2)
    montant_ht = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.00')) # Default added
    montant_tva = models.DecimalField(max_digits=12, decimal_places=2, default=decimal.Decimal('0.00')) # Default added

    def save(self, *args, **kwargs):
        # Ensure values are Decimal before calculation
        self.quantite = decimal.Decimal(str(self.quantite or '0'))
        self.prix_unitaire = decimal.Decimal(str(self.prix_unitaire or '0.00'))
        self.taux_tva = decimal.Decimal(str(self.taux_tva or '0.00')) # Ensure this is in Decimal format

        self.montant_ht = self.quantite * self.prix_unitaire
        self.montant_tva = self.montant_ht * (self.taux_tva / decimal.Decimal('100.00'))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.produit.designation} - {self.quantite} x {self.prix_unitaire}" # Use produit.designation


# --- NEW HISTORY AND AUDIT LOG MODELS FOR BONLIVRAISON ---

class BonLivraisonStatutHistory(models.Model):
    """
    Modèle pour enregistrer l'historique des changements de statut d'un BonLivraison.
    """
    bon_livraison = models.ForeignKey(BonLivraison, on_delete=models.CASCADE, related_name='status_history')
    ancien_statut = models.CharField(max_length=20, null=True, blank=True)
    nouveau_statut = models.CharField(max_length=20)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    commentaire = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Historique Statut Bon de Livraison"
        verbose_name_plural = "Historiques Statuts Bon de Livraison"
        ordering = ['-changed_at']

    def __str__(self):
        return f"BL {self.bon_livraison.numero}: {self.ancien_statut or 'N/A'} -> {self.nouveau_statut} par {self.changed_by} à {self.changed_at.strftime('%Y-%m-%d %H:%M')}"

class BonLivraisonAuditLog(models.Model):
    """
    Modèle pour un journal d'audit général des actions importantes sur les Bons de Livraison.
    """
    ACTION_CHOICES = [
        ('creation', 'Création'),
        ('modification', 'Modification'),
        ('suppression', 'Suppression'),
        ('changement_statut', 'Changement de Statut'),
        ('impression_pdf', 'Impression PDF'),
        ('envoi_email', 'Envoi Email'),
        ('generation_auto', 'Génération Automatique'), # For generation from Commande
        # Ajoutez d'autres types d'actions si nécessaire
    ]

    bon_livraison = models.ForeignKey(BonLivraison, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField(blank=True, null=True)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='bonlivraison_audit_actions')
    performed_at = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(blank=True, null=True) # For Django 3.1+

    class Meta:
        verbose_name = "Journal d'Audit Bon de Livraison"
        verbose_name_plural = "Journaux d'Audit Bon de Livraison"
        ordering = ['-performed_at']

    def __str__(self):
        return f"[{self.performed_at.strftime('%Y-%m-%d %H:%M')}] {self.action} sur BL #{self.bon_livraison.numero if self.bon_livraison else 'N/A'} par {self.performed_by}"

# ventes/models.py
from django.db import models, transaction
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
import logging
from django.urls import reverse

# Assurez-vous d'importer les autres modèles nécessaires
from parametres.models import Entreprise
from STOCK.models import Client

logger = logging.getLogger(__name__)

class Facture(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('validee', 'Validée'),
        ('paye_partiel', 'Payé partiellement'),
        ('paye', 'Payé'),
        ('annulee', 'Annulée'),
    ]

    MODE_PAIEMENT_CHOICES = [
        ('espece', 'Espèce'),
        ('cheque', 'Chèque'),
        ('virement', 'Virement'),
        ('carte', 'Carte bancaire'),
        ('mobile', 'Paiement mobile'),
        ('crypto', 'Cryptomonnaie'),
        ('autre', 'Autre'),
    ]

    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.PROTECT)
    
    devis = models.ForeignKey('Devis', on_delete=models.SET_NULL, null=True, blank=True)
    commande = models.ForeignKey('Commande', on_delete=models.SET_NULL, null=True, blank=True)
    bon_livraison = models.ForeignKey(
        'BonLivraison', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='factures'
    )
    
    numero = models.CharField(max_length=50, blank=True)
    date_facture = models.DateField(default=timezone.now)
    date_echeance = models.DateField()
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    mode_paiement = models.CharField(max_length=20, choices=MODE_PAIEMENT_CHOICES, blank=True, null=True)
    
    date_validation = models.DateTimeField(null=True, blank=True)
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='factures_validees'
    )
    
    remise = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_ht = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_tva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_ttc = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    montant_restant = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    notes = models.TextField(blank=True, null=True)
    conditions_paiement = models.TextField(blank=True, null=True)
    reference_client = models.CharField(max_length=100, blank=True, null=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='factures_crees'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='factures_modifiees'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    devise = models.CharField(max_length=3, default='EUR')
    langue = models.CharField(max_length=10, default='fr')
    
    @property
    def montant_paye(self):
        return (self.total_ttc or 0) - (self.montant_restant or 0)

    @property
    def pourcentage_paye(self):
        if self.total_ttc == 0:
            return 0
        return (self.montant_paye / self.total_ttc) * 100

    @property
    def reste_a_payer(self):
        return self.montant_restant or 0

    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
        ordering = ['-date_facture', '-created_at']
        permissions = [
            ('exporter_facture', 'Peut exporter les factures'),
            ('envoyer_facture', 'Peut envoyer les factures par email'),
        ]
        # CORRECTION: Utilisez unique_together pour garantir l'unicité par entreprise
        unique_together = ['entreprise', 'numero']

    def generate_facture_number_atomic(self):
        """
        Génère un numéro de facture unique par entreprise de manière sécurisée.
        """
        today = timezone.now().date()
        prefix = f"FAC-{today.year}-{today.month:02d}-"
        
        # Le verrouillage est crucial pour éviter les conflits dans un système multi-utilisateurs
        with transaction.atomic():
            last_facture = Facture.objects.filter(
                entreprise=self.entreprise,
                numero__startswith=prefix
            ).select_for_update().order_by('-numero').first()

            sequence = 1
            if last_facture:
                try:
                    num_part = int(last_facture.numero.split('-')[-1])
                    sequence = num_part + 1
                except (ValueError, IndexError):
                    pass
            
            return f"{prefix}{sequence:04d}"

    def save(self, *args, **kwargs):
        """
        Surcharge la méthode save pour générer un numéro unique si nécessaire.
        """
        if not self.numero:
            self.numero = self.generate_facture_number_atomic()
        
        # Le calcul des totaux doit se faire avant la sauvegarde initiale
        # pour éviter un appel 'save' récursif.
        self.calculate_totals()
        
        super().save(*args, **kwargs)

    def calculate_totals(self):
        """
        Calcule et met à jour les totaux de la facture.
        Cette méthode ne sauvegarde pas, elle met simplement à jour les attributs.
        """
        if not self.pk:
            return
        
        items = self.items.all()
        
        total_ht = sum(item.montant_ht for item in items if item.montant_ht is not None)
        total_tva = sum(item.montant_tva for item in items if item.montant_tva is not None)
        
        montant_avant_remise = total_ht + total_tva
        montant_remise = montant_avant_remise * (self.remise / Decimal('100.00')) if self.remise else Decimal('0.00')
        total_ttc = montant_avant_remise - montant_remise
        
        total_paiements = sum(p.montant for p in self.paiements.all() if p.montant is not None)
        montant_restant = max(total_ttc - total_paiements, Decimal('0.00'))

        self.total_ht = total_ht
        self.total_tva = total_tva
        self.total_ttc = total_ttc
        self.montant_restant = montant_restant

    def update_statut(self):
        """Met à jour le statut en fonction des paiements et sauvegarde."""
        if self.statut == 'annulee':
            return
        
        self.calculate_totals()
        
        if self.montant_restant <= Decimal('0.00'):
            self.statut = 'paye'
        elif self.montant_restant < self.total_ttc:
            self.statut = 'paye_partiel'
        elif self.total_ttc > 0 and self.statut == 'brouillon':
            self.statut = 'validee'
        
        self.save(update_fields=['statut', 'montant_restant', 'updated_at'])

    def get_absolute_url(self):
        return reverse('ventes:facture_detail', kwargs={'pk': self.pk})
    
    def __str__(self):
        return f"Facture {self.numero} - {self.client} - {self.total_ttc} {self.devise}"
class LigneFacture(models.Model):
    facture = models.ForeignKey(Facture, related_name='items', on_delete=models.CASCADE)
    produit = models.ForeignKey('STOCK.Produit', on_delete=models.PROTECT)  # Changé de 'article' à 'produit'
    description = models.TextField(blank=True, null=True)
    quantite = models.DecimalField(max_digits=10, decimal_places=2)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2)
    remise = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    montant_ht = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    montant_tva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    
    @property
    def montant_ttc(self):
        """Calcule le montant TTC pour cette ligne"""
        return (self.montant_ht or 0) + (self.montant_tva or 0)

    class Meta:
        verbose_name = "Ligne de Facture"
        verbose_name_plural = "Lignes de Facture"
        ordering = ['id']

    def save(self, *args, **kwargs):
        # Conversion en Decimal pour les calculs
        self.quantite = decimal.Decimal(str(self.quantite or '0'))
        self.prix_unitaire = decimal.Decimal(str(self.prix_unitaire or '0'))
        self.taux_tva = decimal.Decimal(str(self.taux_tva or '0'))
        self.remise = decimal.Decimal(str(self.remise or '0'))

        # Calcul des montants
        montant_avant_remise = self.quantite * self.prix_unitaire
        montant_remise = montant_avant_remise * (self.remise / decimal.Decimal('100.00'))
        
        self.montant_ht = montant_avant_remise - montant_remise
        self.montant_tva = self.montant_ht * (self.taux_tva / decimal.Decimal('100.00'))
        
        super().save(*args, **kwargs)
        
        # Mettre à jour les totaux de la facture seulement si elle existe
        if self.facture_id:
            self.facture.calculate_totals()
            self.facture.save(update_fields=['total_ht', 'total_tva', 'total_ttc', 'montant_restant', 'updated_at'])

    def __str__(self):
        # CORRECTION: Utiliser self.produit.nom au lieu de self.article.designation
        return f"{self.produit.nom} - {self.quantite} x {self.prix_unitaire}"


class FactureStatutHistory(models.Model):
    """Historique des changements de statut des factures"""
    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='status_history')
    ancien_statut = models.CharField(max_length=20, null=True, blank=True)
    nouveau_statut = models.CharField(max_length=20)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    commentaire = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Historique Statut Facture"
        verbose_name_plural = "Historiques Statuts Facture"
        ordering = ['-changed_at']

    def __str__(self):
        return f"Facture {self.facture.numero}: {self.ancien_statut or 'N/A'} -> {self.nouveau_statut}"


class FactureAuditLog(models.Model):
    """Journal d'audit des actions sur les factures"""
    ACTION_CHOICES = [
        ('creation', 'Création'),
        ('modification', 'Modification'),
        ('suppression', 'Suppression'),
        ('changement_statut', 'Changement de Statut'),
        ('envoi_email', 'Envoi Email'),
        ('impression_pdf', 'Impression PDF'),
        ('paiement_enregistre', 'Paiement Enregistré'),
    ]

    facture = models.ForeignKey(Facture, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField(blank=True, null=True)
    performed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    performed_at = models.DateTimeField(auto_now_add=True)
    details = models.JSONField(blank=True, null=True)

    class Meta:
        verbose_name = "Journal d'Audit Facture"
        verbose_name_plural = "Journaux d'Audit Facture"
        ordering = ['-performed_at']

    def __str__(self):
        return f"[{self.performed_at}] {self.action} sur Facture {self.facture.numero if self.facture else 'supprimée'}"

# You might also need a FactureStatutHistory and FactureAuditLog if you want to track changes like BonLivraison
# (Similar structure to BonLivraisonStatutHistory/AuditLog, adjusting foreign keys)
class Paiement(models.Model):
    MODE_PAIEMENT_CHOICES = [
        ('espece', 'Espèce'),
        ('cheque', 'Chèque'),
        ('virement', 'Virement'),
        ('carte', 'Carte bancaire'),
        ('autre', 'Autre'),
    ]

    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    facture = models.ForeignKey(Facture, related_name='paiements', on_delete=models.CASCADE)
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    mode_paiement = models.CharField(max_length=20, choices=MODE_PAIEMENT_CHOICES)
    reference = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Paiement de {self.montant} pour {self.facture.numero}"
# ventes/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class PointDeVente(models.Model):
    entreprise = models.ForeignKey('parametres.Entreprise', on_delete=models.CASCADE)
    code = models.CharField(max_length=20)
    nom = models.CharField(max_length=100)
    adresse = models.TextField(blank=True)
    responsable = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pos_responsable'
    )
    caissiers = models.ManyToManyField(
        User,
        related_name='pos_caissiers',
        blank=True
    )
    actif = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['entreprise', 'code']
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.code})"

    def clean(self):
        """Validation seulement si l'entreprise est déjà définie"""
        if hasattr(self, 'entreprise') and self.entreprise:
            if self.responsable and self.responsable.role != 'CAISSIER':
                raise ValidationError("Le responsable doit avoir le rôle CAISSIER")
            
            if self.responsable and self.responsable.entreprise != self.entreprise:
                raise ValidationError("Le responsable doit appartenir à la même entreprise")

    def save(self, *args, **kwargs):
        """Sauvegarde sans validation pour éviter les erreurs"""
        # Sauvegarde directe sans validation pour éviter les problèmes
        super().save(*args, **kwargs)

class SessionPOS(models.Model):
    point_de_vente = models.ForeignKey(PointDeVente, on_delete=models.CASCADE)
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date_ouverture = models.DateTimeField(auto_now_add=True)
    date_fermeture = models.DateTimeField(null=True, blank=True)
    fonds_ouverture = models.DecimalField(max_digits=12, decimal_places=2)
    fonds_fermeture = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    statut = models.CharField(max_length=20, choices=[('ouverte', 'Ouverte'), ('fermee', 'Fermée')], default='ouverte')

    @property
    def total_ventes(self):
        return sum(v.total_ttc for v in self.ventes.all())
    def __str__(self):
        return f"Session {self.id} - {self.point_de_vente.nom}"
    @property
    def total_especes(self):
        return sum(p.montant for p in self.paiements.filter(mode_paiement='espece'))
    
    @property
    def fonds_theorique(self):
        return self.fonds_ouverture + self.total_especes
    
    @property
    def ecart_caisse(self):
        if self.fonds_fermeture is not None:
            return self.fonds_fermeture - self.fonds_theorique
        return None
    
    @property
    def has_ecart(self):
        return self.ecart_caisse is not None and self.ecart_caisse != 0
    
    @property
    def type_ecart(self):
        if self.ecart_caisse is None:
            return None
        return 'excedent' if self.ecart_caisse > 0 else 'manquant' if self.ecart_caisse < 0 else 'none'
    

class VentePOS(models.Model):
    session = models.ForeignKey(SessionPOS, related_name='ventes', on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)
    numero = models.CharField(max_length=50, unique=True)
    date = models.DateTimeField(auto_now_add=True)
    remise = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)

    @property
    def total_ht(self):
        return sum(item.montant_ht for item in self.items.all())

    @property
    def total_tva(self):
        return sum(item.montant_tva for item in self.items.all())

    @property
    def total_ttc(self):
        return self.total_ht + self.total_tva - self.remise

    def __str__(self):
        return f"Vente POS {self.numero}"
    
class LigneVentePOS(models.Model):
    vente = models.ForeignKey(VentePOS, related_name='items', on_delete=models.CASCADE)
    produit = models.ForeignKey(Produit, on_delete=models.PROTECT)
    quantite = models.DecimalField(max_digits=10, decimal_places=2)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # TVA à 0 par défaut
    montant_ht = models.DecimalField(max_digits=12, decimal_places=2)
    montant_tva = models.DecimalField(max_digits=12, decimal_places=2, default=0)  # Montant TVA à 0

    def save(self, *args, **kwargs):
        self.montant_ht = self.quantite * self.prix_unitaire
        self.montant_tva = 0  # Forcer le montant TVA à 0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.produit.nom} - {self.quantite} x {self.prix_unitaire}"

    
class PaiementPOS(models.Model):
    MODE_PAIEMENT_CHOICES = [
        ('espece', 'Espèce'),
        ('cheque', 'Chèque'),
        ('virement', 'Virement'),
        ('carte', 'Carte bancaire'),
        ('autre', 'Autre'),
    ]

    session = models.ForeignKey(SessionPOS, related_name='paiements', on_delete=models.CASCADE)
    vente = models.ForeignKey(VentePOS, on_delete=models.CASCADE)
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    mode_paiement = models.CharField(max_length=20, choices=MODE_PAIEMENT_CHOICES)
    reference = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Paiement POS de {self.montant}"

    def enregistrer_ecriture_comptable(self):
        """Enregistre le paiement dans la comptabilité"""
        from comptabilite.models import JournalComptable, EcritureComptable, LigneEcriture, PlanComptableOHADA
        from django.contrib.auth import get_user_model
        from django.utils import timezone
        import logging
        
        logger = logging.getLogger(__name__)
        User = get_user_model()
        
        try:
            logger.info(f"=== DÉBUT création écriture comptable pour paiement POS {self.id} ===")
            
            entreprise = self.session.point_de_vente.entreprise
            utilisateur = self.session.utilisateur
            
            logger.info(f"Entreprise: {entreprise.nom}, Utilisateur: {utilisateur.username}")
            
            # Déterminer le journal comptable en fonction du mode de paiement
            if self.mode_paiement == 'espece':
                journal_code = 'CA'  # Journal de caisse
                compte_numero = '53'
            elif self.mode_paiement == 'carte':
                journal_code = 'BQ'  # Journal de banque
                compte_numero = '51'
            else:
                journal_code = 'OD'  # Journal des opérations diverses
                compte_numero = '53'
            
            logger.info(f"Mode paiement: {self.mode_paiement}, Journal: {journal_code}, Compte: {compte_numero}")
            
            # Vérifier l'existence des comptes et journaux
            try:
                compte_caisse = PlanComptableOHADA.objects.get(numero=compte_numero, entreprise=entreprise)
                logger.info(f"Compte {compte_numero} trouvé: {compte_caisse.intitule}")
            except PlanComptableOHADA.DoesNotExist:
                logger.error(f"❌ Compte {compte_numero} non trouvé pour l'entreprise {entreprise.nom}")
                return None
            except Exception as e:
                logger.error(f"❌ Erreur recherche compte {compte_numero}: {e}")
                return None
            
            try:
                journal = JournalComptable.objects.get(code=journal_code, entreprise=entreprise)
                logger.info(f"Journal {journal_code} trouvé: {journal.intitule}")
            except JournalComptable.DoesNotExist:
                logger.error(f"❌ Journal {journal_code} non trouvé pour l'entreprise {entreprise.nom}")
                return None
            except Exception as e:
                logger.error(f"❌ Erreur recherche journal {journal_code}: {e}")
                return None
            
            try:
                compte_ventes = PlanComptableOHADA.objects.get(numero='70', entreprise=entreprise)
                logger.info(f"Compte 70 trouvé: {compte_ventes.intitule}")
            except PlanComptableOHADA.DoesNotExist:
                logger.error(f"❌ Compte 70 non trouvé pour l'entreprise {entreprise.nom}")
                return None
            except Exception as e:
                logger.error(f"❌ Erreur recherche compte 70: {e}")
                return None
            
            # Créer l'écriture comptable
            ecriture_data = {
                'journal': journal,
                'numero': f"PAY-POS-{self.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                'date_ecriture': timezone.now(),
                'date_comptable': timezone.now().date(),
                'libelle': f"Paiement POS vente {self.vente.numero}",
                'piece_justificative': f"PV-POS-{self.id}",
                'montant_devise': self.montant,
                'entreprise': entreprise,
                'created_by': utilisateur,
                'vente_liee': self.vente,
                'paiement_pos': self
            }
            
            logger.info(f"Données écriture: {ecriture_data}")
            
            ecriture = EcritureComptable.objects.create(**ecriture_data)
            logger.info(f"✅ Écriture comptable créée: {ecriture.numero}")
            
            # Créer les lignes d'écriture
            ligne1 = LigneEcriture.objects.create(
                ecriture=ecriture,
                compte=compte_caisse,
                libelle=f"Encaissement POS vente {self.vente.numero}",
                debit=self.montant,
                credit=0,
                entreprise=entreprise
            )
            logger.info(f"✅ Ligne débit créée: {ligne1.id}")
            
            ligne2 = LigneEcriture.objects.create(
                ecriture=ecriture,
                compte=compte_ventes,
                libelle=f"Vente POS {self.vente.numero}",
                debit=0,
                credit=self.montant,
                entreprise=entreprise
            )
            logger.info(f"✅ Ligne crédit créée: {ligne2.id}")
            
            logger.info(f"=== FIN création écriture comptable réussie ===")
            return ecriture
            
        except Exception as e:
            logger.error(f"❌ ERREUR CRITIQUE lors de l'enregistrement comptable: {str(e)}")
            logger.exception("Détails de l'erreur:")
            return None
    
# ventes/models.py
class EcartCaisse(models.Model):
    TYPE_ECART_CHOICES = [
        ('excedent', 'Excédent'),
        ('manquant', 'Manquant'),
        ('regularisation', 'Regularisation'),
    ]
    
    session = models.ForeignKey(SessionPOS, on_delete=models.CASCADE, related_name='ecarts_caisse')
    caissier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ecarts_caisse')
    type_ecart = models.CharField(max_length=20, choices=TYPE_ECART_CHOICES)
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    motif = models.TextField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='ecarts_crees')
    
    class Meta:
        ordering = ['-date_creation']
        verbose_name = "Écart de caisse"
        verbose_name_plural = "Écarts de caisse"
    
    def __str__(self):
        return f"{self.get_type_ecart_display()} - {self.montant}€ - {self.caissier.get_full_name()}"