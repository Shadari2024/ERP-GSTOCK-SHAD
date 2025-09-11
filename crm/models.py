from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import decimal
import logging
from datetime import timedelta
from parametres.models import Entreprise, ConfigurationSAAS
from STOCK.models import Client as StockClient
from ventes.models import Devis, Commande, Facture
from django.db import transaction
from ventes.models import Devis, LigneDevis
from STOCK.models import Produit
from model_utils import FieldTracker

# Initialiser le logger
logger = logging.getLogger(__name__)
User = get_user_model()

class ClientCRM(StockClient):
    """Extension du modèle Client existant avec des champs spécifiques au CRM"""
    
    class Meta:
        proxy = True
        verbose_name = _("Client CRM")
        verbose_name_plural = _("Clients CRM")
    
    def get_absolute_url(self):
        return reverse('crm:client_detail', kwargs={'pk': self.pk})
    
    @property
    def valeur_commerciale(self):
        """Calcule la valeur commerciale totale du client"""
        total = Decimal('0.00')
        
        # Somme des factures payées
        factures_payees = Facture.objects.filter(
            client=self, 
            statut='paye',
            entreprise=self.entreprise
        )
        for facture in factures_payees:
            total += facture.total_ttc
        
        return total
    
    @property
    def opportunites_actives(self):
        """Retourne les opportunités actives du client"""
        return self.opportunites.filter(statut__in=['nouvelle', 'en_cours', 'negociation'])
    
    @property
    def derniere_activite(self):
        """Retourne la dernière activité avec ce client"""
        return self.activites_assignees.order_by('-date_echeance').first()

class SourceLead(models.Model):
    """Sources de prospects/leads"""
    nom = models.CharField(max_length=100, verbose_name=_("Nom"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    actif = models.BooleanField(default=True, verbose_name=_("Actif"))
    
    class Meta:
        verbose_name = _("Source de lead")
        verbose_name_plural = _("Sources de leads")
        unique_together = ['nom', 'entreprise']
    
    def __str__(self):
        return self.nom

class StatutOpportunite(models.Model):
    """Statuts personnalisables pour les opportunités"""
    nom = models.CharField(max_length=50, verbose_name=_("Nom"))
    ordre = models.PositiveIntegerField(default=0, verbose_name=_("Ordre"))
    couleur = models.CharField(max_length=7, default="#007bff", verbose_name=_("Couleur"))
    est_gagnant = models.BooleanField(default=False, verbose_name=_("Statut gagnant"))
    est_perdant = models.BooleanField(default=False, verbose_name=_("Statut perdant"))
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    
    class Meta:
        verbose_name = _("Statut d'opportunité")
        verbose_name_plural = _("Statuts d'opportunité")
        unique_together = ['nom', 'entreprise']
        ordering = ['ordre']
    
    def __str__(self):
        return self.nom
    
    def clean(self):
        if self.est_gagnant and self.est_perdant:
            raise ValidationError(_("Un statut ne peut pas être à la fois gagnant et perdant"))


User = get_user_model()

class Opportunite(models.Model):
    """Opportunités commerciales"""
    PRIORITE_CHOICES = [
        ('faible', _('Faible')),
        ('moyenne', _('Moyenne')),
        ('elevee', _('Élevée')),
        ('critique', _('Critique')),
    ]
    
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    client = models.ForeignKey(StockClient, on_delete=models.CASCADE, related_name='opportunites', verbose_name=_("Client"))
    nom = models.CharField(max_length=200, verbose_name=_("Nom de l'opportunité"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    montant_estime = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, 
        verbose_name=_("Montant estimé")
    )
    probabilite = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0,
        verbose_name=_("Probabilité (%)")
    )
    statut = models.ForeignKey('StatutOpportunite', on_delete=models.PROTECT, verbose_name=_("Statut"))
    priorite = models.CharField(max_length=10, choices=PRIORITE_CHOICES, default='moyenne', verbose_name=_("Priorité"))
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_("Date de modification"))
    date_fermeture_prevue = models.DateField(verbose_name=_("Date de fermeture prévue"))
    date_fermeture_reelle = models.DateField(null=True, blank=True, verbose_name=_("Date de fermeture réelle"))
    assigne_a = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Assigné à"))
     # Ajouter le tracker pour suivre les changements
    tracker = FieldTracker()
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='opportunites_crees', verbose_name=_("Créé par"))
    devis_lie = models.ForeignKey(
    'ventes.Devis',  # Utilisez le nom de l'app et du modèle comme string
    on_delete=models.SET_NULL, 
    null=True, 
    blank=True, 
    verbose_name=_("Devis lié")
)
    # SUPPRIMEZ ces champs :
    # devis_lie = models.ForeignKey(Devis, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Devis lié"))
    # commande_liee = models.ForeignKey(Commande, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Commande liée"))
    # bon_livraison_lie = models.ForeignKey('STOCK.BonLivraison', on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Bon de livraison lié"))
    
    class Meta:
        verbose_name = _("Opportunité")
        verbose_name_plural = _("Opportunités")
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.nom} - {self.client.nom}"
    
    def get_absolute_url(self):
        return reverse('crm:opportunite_detail', kwargs={'pk': self.pk})
    
    @property
    def valeur_attendue(self):
        """Calcule la valeur attendue de l'opportunité"""
        return (self.montant_estime * Decimal(self.probabilite)) / Decimal('100.00')
    
    @property
    def est_terminee(self):
        """Vérifie si l'opportunité est terminée"""
        return self.statut.est_gagnant or self.statut.est_perdant
    
    def convertir_en_devis(self, request):
        """Convertit l'opportunité en devis"""
        try:
            with transaction.atomic():
                # Créer le devis
                devis = Devis.objects.create(
                    entreprise=self.entreprise,
                    client=self.client,
                    date=timezone.now().date(),
                    echeance=timezone.now().date() + timedelta(days=30),
                    statut='brouillon',
                    notes=f"Devis créé à partir de l'opportunité: {self.nom}",
                    created_by=request.user,
                    opportunite=self
                )
                
                # Tenter de trouver le produit générique
                try:
                    produit_generique = Produit.objects.get(nom="Service générique", entreprise=self.entreprise)
                    
                    # Si le produit est trouvé, créer la ligne de devis
                    LigneDevis.objects.create(
                        devis=devis,
                        produit=produit_generique,
                        quantite=1,
                        prix_unitaire=self.montant_estime,
                        taux_tva=produit_generique.taux_tva if hasattr(produit_generique, 'taux_tva') else decimal.Decimal('20.00'),
                    )
                except Produit.DoesNotExist:
                    # Si le produit générique n'existe pas,
                    # ne rien faire et laisser le devis sans ligne d'article.
                    # Cela permet au processus de conversion de réussir même si le produit n'est pas créé.
                    pass
                
                # Lier l'opportunité au devis créé
                self.devis_lie = devis
                self.save()
                
                return devis
                
        except Exception as e:
            # En cas d'erreur, annuler la transaction
            raise Exception(f"Erreur lors de la conversion: {str(e)}")
    
    def save(self, *args, **kwargs):
        # Si l'opportunité passe à un statut terminé, enregistrer la date de fermeture
        if self.est_terminee and not self.date_fermeture_reelle:
            self.date_fermeture_reelle = timezone.now().date()
        elif not self.est_terminee and self.date_fermeture_reelle:
            self.date_fermeture_reelle = None
        
        super().save(*args, **kwargs)
        
class TypeActivite(models.Model):
    """Types d'activités commerciales"""
    nom = models.CharField(max_length=100, verbose_name=_("Nom"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    duree_par_defaut = models.DurationField(null=True, blank=True, verbose_name=_("Durée par défaut"))
    couleur = models.CharField(max_length=7, default="#007bff", verbose_name=_("Couleur"))
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    
    class Meta:
        verbose_name = _("Type d'activité")
        verbose_name_plural = _("Types d'activité")
        unique_together = ['nom', 'entreprise']
    
    def __str__(self):
        return self.nom

class Activite(models.Model):
    """Activités commerciales (tâches, rendez-vous, appels, etc.)"""
    STATUT_CHOICES = [
        ('planifie', _('Planifié')),
        ('en_cours', _('En cours')),
        ('termine', _('Terminé')),
        ('annule', _('Annulé')),
    ]
    
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    type_activite = models.ForeignKey(TypeActivite, on_delete=models.PROTECT, verbose_name=_("Type d'activité"))
    sujet = models.CharField(max_length=200, verbose_name=_("Sujet"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    date_debut = models.DateTimeField(verbose_name=_("Date de début"))
    date_echeance = models.DateTimeField(verbose_name=_("Date d'échéance"))
    statut = models.CharField(max_length=10, choices=STATUT_CHOICES, default='planifie', verbose_name=_("Statut"))
    priorite = models.CharField(max_length=10, choices=Opportunite.PRIORITE_CHOICES, default='moyenne', verbose_name=_("Priorité"))
    assigne_a = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Assigné à"))
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='activites_crees', verbose_name=_("Créé par"))
    clients = models.ManyToManyField(ClientCRM, blank=True, related_name='activites', verbose_name=_("Clients"))
    opportunites = models.ManyToManyField(Opportunite, blank=True, related_name='activites', verbose_name=_("Opportunités"))
    rappel = models.BooleanField(default=False, verbose_name=_("Rappel"))
    date_rappel = models.DateTimeField(null=True, blank=True, verbose_name=_("Date de rappel"))
    resultat = models.TextField(blank=True, verbose_name=_("Résultat"))
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_("Date de modification"))
    
    class Meta:
        verbose_name = _("Activité")
        verbose_name_plural = _("Activités")
        ordering = ['-date_debut']
    
    def __str__(self):
        return f"{self.type_activite.nom}: {self.sujet}"
    
    def get_absolute_url(self):
        return reverse('crm:activite_detail', kwargs={'pk': self.pk})
    
    @property
    def est_en_retard(self):
        """Vérifie si l'activité est en retard"""
        return self.date_echeance < timezone.now() and self.statut not in ['termine', 'annule']
    
    def clean(self):
        if self.date_echeance and self.date_debut and self.date_echeance < self.date_debut:
            raise ValidationError(_("La date d'échéance ne peut pas être antérieure à la date de début"))

class NoteClient(models.Model):
    """Notes sur les clients"""
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    client = models.ForeignKey(ClientCRM, on_delete=models.CASCADE, related_name='crm_notes', verbose_name=_("Client"))  # Changé related_name
    titre = models.CharField(max_length=200, verbose_name=_("Titre"))
    contenu = models.TextField(verbose_name=_("Contenu"))
    est_important = models.BooleanField(default=False, verbose_name=_("Important"))
    cree_par = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, verbose_name=_("Créé par"))
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_("Date de modification"))
    
    class Meta:
        verbose_name = _("Note client")
        verbose_name_plural = _("Notes client")
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"Note: {self.titre} - {self.client.nom}"

class PipelineVente(models.Model):
    """Pipeline de vente personnalisable"""
    nom = models.CharField(max_length=100, verbose_name=_("Nom"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    statuts = models.ManyToManyField(StatutOpportunite, through='EtapePipeline', verbose_name=_("Statuts"))
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    actif = models.BooleanField(default=True, verbose_name=_("Actif"))
    
    class Meta:
        verbose_name = _("Pipeline de vente")
        verbose_name_plural = _("Pipelines de vente")
        unique_together = ['nom', 'entreprise']
    
    def __str__(self):
        return self.nom

class EtapePipeline(models.Model):
    """Étapes dans un pipeline de vente"""
    pipeline = models.ForeignKey(PipelineVente, on_delete=models.CASCADE, verbose_name=_("Pipeline"))
    statut = models.ForeignKey(StatutOpportunite, on_delete=models.CASCADE, verbose_name=_("Statut"))
    ordre = models.PositiveIntegerField(default=0, verbose_name=_("Ordre"))
    probabilite_par_defaut = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        default=0,
        verbose_name=_("Probabilité par défaut (%)")
    )
    
    class Meta:
        verbose_name = _("Étape de pipeline")
        verbose_name_plural = _("Étapes de pipeline")
        unique_together = ['pipeline', 'statut']
        ordering = ['ordre']
    
    def __str__(self):
        return f"{self.pipeline.nom} - {self.statut.nom}"

class ObjectifCommercial(models.Model):
    """Objectifs commerciaux"""
    PERIODICITE_CHOICES = [
        ('quotidien', _('Quotidien')),
        ('hebdomadaire', _('Hebdomadaire')),
        ('mensuel', _('Mensuel')),
        ('trimestriel', _('Trimestriel')),
        ('annuel', _('Annuel')),
    ]
    
    TYPE_OBJECTIF_CHOICES = [
        ('chiffre_affaires', _('Chiffre d\'affaires')),
        ('nombre_ventes', _('Nombre de ventes')),
        ('taux_conversion', _('Taux de conversion')),
        ('nouveaux_clients', _('Nouveaux clients')),
    ]
    
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    nom = models.CharField(max_length=200, verbose_name=_("Nom"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    type_objectif = models.CharField(max_length=20, choices=TYPE_OBJECTIF_CHOICES, verbose_name=_("Type d'objectif"))
    valeur_cible = models.DecimalField(max_digits=15, decimal_places=2, verbose_name=_("Valeur cible"))
    valeur_actuelle = models.DecimalField(max_digits=15, decimal_places=2, default=0, verbose_name=_("Valeur actuelle"))
    periodicite = models.CharField(max_length=15, choices=PERIODICITE_CHOICES, verbose_name=_("Périodicité"))
    date_debut = models.DateField(verbose_name=_("Date de début"))
    date_fin = models.DateField(verbose_name=_("Date de fin"))
    assigne_a = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("Assigné à"))
    equipe = models.ManyToManyField(User, blank=True, related_name='objectifs_equipe', verbose_name=_("Équipe"))
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de création"))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_("Date de modification"))
    
    class Meta:
        verbose_name = _("Objectif commercial")
        verbose_name_plural = _("Objectifs commerciaux")
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.nom} - {self.get_type_objectif_display()}"
    
    @property
    def pourcentage_realisation(self):
        """Calcule le pourcentage de réalisation de l'objectif"""
        if self.valeur_cible == 0:
            return 0
        return (self.valeur_actuelle / self.valeur_cible) * 100
    
    @property
    def est_atteint(self):
        """Vérifie si l'objectif est atteint"""
        return self.valeur_actuelle >= self.valeur_cible
    
    @property
    def jours_restants(self):
        """Calcule le nombre de jours restants pour atteindre l'objectif"""
        today = timezone.now().date()
        if today > self.date_fin:
            return 0
        return (self.date_fin - today).days
    
    
class Notification(models.Model):
    """Modèle pour les notifications système"""
    TYPE_CHOICES = [
        ('assignation', _('Assignation d\'opportunité')),
        ('rappel', _('Rappel de date')),
        ('changement_statut', _('Changement de statut')),
        ('activite', _('Activité planifiée')),
        ('systeme', _('Notification système')),
    ]
    
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type_notification = models.CharField(max_length=20, choices=TYPE_CHOICES)
    titre = models.CharField(max_length=200)
    message = models.TextField()
    lien = models.CharField(max_length=200, blank=True, null=True)
    est_lue = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_lue = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-date_creation']
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
    
    def __str__(self):
        return f"{self.titre} - {self.utilisateur}"

class RegleAutomatisation(models.Model):
    """Règles d'automatisation pour le CRM"""
    TYPE_DECLENCHEUR_CHOICES = [
        ('creation_opportunite', _('Création d\'opportunité')),
        ('changement_statut', _('Changement de statut')),
        ('assignation', _('Assignation à un commercial')),
        ('date_approchant', _('Date approchant')),
        ('activite_terminee', _('Activité terminée')),
    ]
    
    TYPE_ACTION_CHOICES = [
        ('notification', _('Notification')),
        ('email', _('Email')),
        ('changement_statut', _('Changer le statut')),
        ('creation_activite', _('Créer une activité')),
        ('assignation', _('Assigner à un utilisateur')),
    ]
    
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    nom = models.CharField(max_length=100)
    type_declencheur = models.CharField(max_length=50, choices=TYPE_DECLENCHEUR_CHOICES)
    type_action = models.CharField(max_length=50, choices=TYPE_ACTION_CHOICES)
    parametres = models.JSONField(default=dict)  # Stocke les paramètres spécifiques
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _("Règle d'automatisation")
        verbose_name_plural = _("Règles d'automatisation")
    
    def __str__(self):
        return self.nom

class TemplateEmail(models.Model):
    """Templates d'emails pour l'automatisation"""
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    nom = models.CharField(max_length=100)
    sujet = models.CharField(max_length=200)
    corps = models.TextField()
    variables_disponibles = models.TextField(help_text=_("Liste des variables disponibles séparées par des virgules"))
    actif = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = _("Template email")
        verbose_name_plural = _("Templates email")
    
    def __str__(self):
        return self.nom
    
    
