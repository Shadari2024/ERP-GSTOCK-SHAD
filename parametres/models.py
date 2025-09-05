from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone # Importez timezone ici_
from django.core.exceptions import ValidationError
from datetime import datetime
from decimal import Decimal # Assurez-vous que Decimal est importé





class Module(models.Model):
    """
    Modèle représentant un module fonctionnel de l'application
    """
    class CategoriesModule(models.TextChoices):
        STOCK = 'STOCK', _('Gestion de stock')
        VENTE = 'VENTE', _('Vente')
        COMPTABILITE = 'COMPTA', _('Comptabilité')
        RH = 'RH', _('Ressources humaines')
        CRM = 'CRM', _('CRM')
        REPORTING = 'REPORT', _('Reporting')
        PARAMETRAGE = 'CONFIG', _('Paramétrage')

    code = models.CharField(
        _("Code du module"), 
        max_length=20, 
        unique=True,
        help_text=_("Code unique identifiant le module")
    )
    nom = models.CharField(
        _("Nom du module"), 
        max_length=100,
        help_text=_("Nom complet du module")
    )
    categorie = models.CharField(
        _("Catégorie"), 
        max_length=10,
        choices=CategoriesModule.choices,
        help_text=_("Catégorie fonctionnelle du module")
    )
    description = models.TextField(
        _("Description"), 
        blank=True,
        help_text=_("Description détaillée des fonctionnalités du module")
    )
    icone = models.CharField(
        _("Icône"), 
        max_length=50, 
        default='settings',
        help_text=_("Nom de l'icône Material Icons ou Font Awesome")
    )
    actif_par_defaut = models.BooleanField(
        _("Actif par défaut"), 
        default=False,
        help_text=_("Si le module est activé par défaut pour les nouveaux abonnements")
    )
    ordre_affichage = models.PositiveIntegerField(
        _("Ordre d'affichage"), 
        default=0,
        help_text=_("Ordre d'affichage dans l'interface")
    )
    date_creation = models.DateTimeField(
        _("Date de création"), 
        auto_now_add=True
    )
    date_mise_a_jour = models.DateTimeField(
        _("Date de mise à jour"), 
        auto_now=True
    )

    class Meta:
        verbose_name = _("Module")
        verbose_name_plural = _("Modules")
        ordering = ['ordre_affichage', 'nom']

    def __str__(self):
        return f"{self.nom} ({self.get_categorie_display()})"
    
    def save(self, *args, **kwargs):
        # Vérification que le code correspond à une app installée
        installed_apps = [app.split('.')[0] for app in settings.INSTALLED_APPS]
        if self.code not in installed_apps:
            raise ValueError(
                f"Le code module doit correspondre à une application installée. "
                f"Applications disponibles: {', '.join(installed_apps)}"
            )
        super().save(*args, **kwargs)

class ModuleEntreprise(models.Model):
    """
    Association entre un module et une entreprise avec statut d'activation
    """
    entreprise = models.ForeignKey(
        'Entreprise',
        verbose_name=_("Entreprise"),
        on_delete=models.CASCADE,
        related_name='modules_entreprise'
    )
    module = models.ForeignKey(
        Module,
        verbose_name=_("Module"),
        on_delete=models.CASCADE,
        related_name='entreprises_modules'
    )
    est_actif = models.BooleanField(
        _("Est actif"), 
        default=True,
        help_text=_("Indique si le module est activé pour cette entreprise")
    )
    date_activation = models.DateTimeField(
        _("Date d'activation"), 
        null=True, 
        blank=True
    )
    date_desactivation = models.DateTimeField(
        _("Date de désactivation"), 
        null=True, 
        blank=True
    )

    class Meta:
        verbose_name = _("Module entreprise")
        verbose_name_plural = _("Modules entreprise")
        unique_together = ('entreprise', 'module')
        ordering = ['module__ordre_affichage']

    def __str__(self):
        return f"{self.entreprise} - {self.module} ({'Actif' if self.est_actif else 'Inactif'})"

    def save(self, *args, **kwargs):
        # Mise à jour des dates d'activation/désactivation
        if self.est_actif and not self.date_activation:
            self.date_activation = timezone.now()
            self.date_desactivation = None
        elif not self.est_actif and not self.date_desactivation:
            self.date_desactivation = timezone.now()
        
        super().save(*args, **kwargs)

class DependanceModule(models.Model):
    """
    Dépendances entre modules (pré-requis)
    """
    module_principal = models.ForeignKey(
        Module,
        verbose_name=_("Module principal"),
        on_delete=models.CASCADE,
        related_name='dependances_principales'
    )
    module_dependance = models.ForeignKey(
        Module,
        verbose_name=_("Module dépendance"),
        on_delete=models.CASCADE,
        related_name='dependances_secondaires'
    )
    obligatoire = models.BooleanField(
        _("Obligatoire"), 
        default=True,
        help_text=_("Si la dépendance est obligatoire pour l'activation du module principal")
    )

    class Meta:
        verbose_name = _("Dépendance de module")
        verbose_name_plural = _("Dépendances de modules")
        unique_together = ('module_principal', 'module_dependance')

    def __str__(self):
        return f"{self.module_principal} → {self.module_dependance} ({'obligatoire' if self.obligatoire else 'optionnel'})"




User = get_user_model()

class PlanTarification(models.Model):
    """
    Plans de tarification avec fonctionnalités spécifiques
    """
    class NiveauPlan(models.TextChoices):
        STARTER = 'ST', _('Starter')
        PROFESSIONAL = 'PRO', _('Professional')
        ENTERPRISE = 'ENT', _('Enterprise')
        CUSTOM = 'CUS', _('Custom')

    nom = models.CharField(_("Nom du plan"), max_length=50)
    niveau = models.CharField(
        _("Niveau"), 
        max_length=3,
        choices=NiveauPlan.choices,
        default=NiveauPlan.STARTER
    )
    prix_mensuel = models.DecimalField(_("Prix mensuel"), max_digits=10, decimal_places=2)
    utilisateurs_inclus = models.PositiveIntegerField(_("Utilisateurs inclus"))
    stockage_go = models.PositiveIntegerField(_("Stockage inclus (Go)"))
    
    modules_inclus = models.ManyToManyField(
        Module,
        related_name='plans_inclus',
        verbose_name=_("Modules inclus"),
        blank=True,
        help_text=_("Modules automatiquement inclus dans ce plan")
    )
    modules_optionnels = models.ManyToManyField(
        Module,
        verbose_name=_("Modules optionnels"),
        related_name='plans_optionnels',
        blank=True,
        help_text=_("Modules disponibles en option pour ce plan")
    )
    limites = models.JSONField(_("Limites d'usage"), default=dict)
    
    # Fonctionnalités premium
    support_24h = models.BooleanField(_("Support 24/7"), default=False)
    api_acces = models.BooleanField(_("Accès API"), default=False)
    rapports_avances = models.BooleanField(_("Rapports avancés"), default=False)
    est_actif = models.BooleanField(default=True)  # Ajoutez ce champ si manquant
    # ... autres champs existants ...
    
    def __str__(self):
        return self.nom

    class Meta:
        verbose_name = _("Plan de tarification")
        verbose_name_plural = _("Plans de tarification")
        ordering = ['prix_mensuel']

    def __str__(self):
        return f"{self.nom} ({self.get_niveau_display()})"
class Entreprise(models.Model):
    """
    Modèle principal tenant-aware pour l'architecture SAAS
    """
    class StatutEntreprise(models.TextChoices):
        ACTIVE = 'AC', _('Active')
        ESSAI = 'ES', _("Période d'essai")
        SUSPENDUE = 'SU', _('Suspendue')
        ARCHIVE = 'AR', _('Archivée')

    nom = models.CharField(_("Nom"), max_length=100)
    slogan = models.CharField(_("Slogan"), max_length=255, blank=True, null=True)
    adresse = models.TextField(_("Adresse"), blank=True, null=True)
    telephone = models.CharField(_("Téléphone"), max_length=20, blank=True, null=True)
    email = models.EmailField(_("Email"), blank=True, null=True)
    site_web = models.URLField(_("Site web"), blank=True, null=True)
    domaine = models.CharField(_("Domaine"), max_length=255, unique=True)
    logo = models.ImageField(_("Logo"), upload_to='logos/', blank=True, null=True)
    active = models.BooleanField(_("Active"), default=True)
    numero_fiscal = models.CharField(_("Numéro Fiscal"), max_length=50, blank=True, null=True)

    # NOUVEAU CHAMP : Taux de TVA par défaut pour cette entreprise
    taux_tva_defaut = models.DecimalField(
        _("Taux de TVA par défaut (%)"),
        max_digits=5, # Ex: 99.999
        decimal_places=2, # Ex: 19.50 pour 19.5%
        default=0.00,
        help_text=_("Taux de TVA par défaut à appliquer pour cette entreprise (en pourcentage, ex: 20.00)")
    )

    plan_tarification = models.ForeignKey(
        'PlanTarification', # Utilisez une chaîne si PlanTarification est défini plus bas ou dans un autre fichier non importé
        verbose_name=_("Plan tarification"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    date_debut_abonnement = models.DateField(_("Date début abonnement"), blank=True, null=True)
    date_fin_abonnement = models.DateField(_("Date fin abonnement"), blank=True, null=True)
    slug = models.SlugField(_("Slug"), unique=True, blank=True, null=True)
    statut = models.CharField(
        _("Statut"),
        max_length=2,
        choices=StatutEntreprise.choices,
        default=StatutEntreprise.ESSAI
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nom)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _("Entreprise")
        verbose_name_plural = _("Entreprises")
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['statut']),
        ]

    def __str__(self):
        return self.nom

    @property
    def est_active(self):
        return self.statut == self.StatutEntreprise.ACTIVE
    
    # NOUVELLE MÉTHODE : Calcul de la TVA
    def calculer_tva(self, montant_ht):
        """
        Calcule le montant de la TVA pour un montant Hors Taxe (HT) donné,
        en utilisant le taux de TVA par défaut de l'entreprise.

        Args:
            montant_ht (Decimal): Le montant Hors Taxe (HT).

        Returns:
            Decimal: Le montant de la TVA.
        """
        if not isinstance(montant_ht, (int, float, models.Decimal)):
            try:
                montant_ht = models.Decimal(str(montant_ht))
            except (ValueError, TypeError):
                raise TypeError("montant_ht doit être un nombre ou convertible en Decimal.")
        
        # S'assurer que montant_ht est un Decimal pour des calculs précis
        montant_ht = models.Decimal(str(montant_ht)) 
        
        # Le taux de TVA est stocké en pourcentage (ex: 20.00 pour 20%)
        # Pour le calcul, nous le convertissons en facteur (ex: 0.20)
        taux_tva_facteur = self.taux_tva_defaut / models.Decimal('100.00')
        
        montant_tva = montant_ht * taux_tva_facteur
        
        # Arrondir à deux décimales pour la monnaie, si nécessaire (Decimal gère bien la précision)
        # Utiliser quantize pour un arrondi précis des décimales
        from decimal import Decimal, ROUND_HALF_UP
        return montant_tva.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def calculer_montant_ttc(self, montant_ht):
        """
        Calcule le montant Toutes Taxes Comprises (TTC) pour un montant Hors Taxe (HT) donné.

        Args:
            montant_ht (Decimal): Le montant Hors Taxe (HT).

        Returns:
            Decimal: Le montant Toutes Taxes Comprises (TTC).
        """
        montant_tva = self.calculer_tva(montant_ht)
        return montant_ht + montant_tva


# parametres/models.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

class Abonnement(models.Model):
    """
    Modèle d'abonnement optimisé pour une vérification fiable dans le middleware
    """
    entreprise = models.ForeignKey(
        'parametres.Entreprise',
        on_delete=models.CASCADE,
        related_name='abonnements',
        verbose_name=_("Entreprise associée")
    )
    
    plan_actuel = models.ForeignKey(
        'parametres.PlanTarification',
        verbose_name=_("Plan actuel"),
        on_delete=models.PROTECT
    )
    
    date_debut = models.DateTimeField(
        _("Date début"),
        default=timezone.now,  # Défaut à maintenant
        help_text=_("Date de début effective de l'abonnement")
    )
    
    date_fin = models.DateTimeField(
        _("Date fin"), 
        null=True, 
        blank=True,
        help_text=_("Laissez vide pour un abonnement illimité")
    )
    
    prochain_paiement = models.DateTimeField(
        _("Prochain paiement"), 
        null=True, 
        blank=True
    )
    
    montant_paye = models.DecimalField(
        _("Montant payé"), 
        max_digits=10, 
        decimal_places=2, 
        default=0.00
    )
    
    est_actif = models.BooleanField(
        _("Est actif"), 
        default=True,
        db_index=True  # Index pour des recherches plus rapides
    )

    class MethodesPaiement(models.TextChoices):
        STRIPE = 'STRIPE', 'Stripe'
        PAYPAL = 'PAYPAL', 'PayPal'
        BANK = 'BANK', _("Virement bancaire")
        CASH = 'CASH', _("Espèces")
    
    methode_paiement = models.CharField(
        _("Méthode de paiement"),
        max_length=10,
        choices=MethodesPaiement.choices,
        blank=True, 
        null=True
    )
    
    id_abonnement_paiement = models.CharField(
        _("ID abonnement fournisseur"),
        max_length=100,
        blank=True, 
        null=True,
        db_index=True
    )

    # Champs de suivi
    date_creation = models.DateTimeField(
        _("Date de création"), 
        auto_now_add=True
    )
    
    date_mise_a_jour = models.DateTimeField(
        _("Date de dernière mise à jour"), 
        auto_now=True
    )
    class StatutPaiement(models.TextChoices):
        REQUIS = 'REQUIS', _('Paiement requis')
        EN_ATTENTE = 'EN_ATTENTE', _('Paiement en attente')
        COMPLETE = 'COMPLETE', _('Paiement complété')
        ECHEC = 'ECHEC', _('Paiement échoué')
        REMBOURSE = 'REMBOURSE', _('Remboursé')
    
    statut_paiement = models.CharField(
        _("Statut du paiement"),
        max_length=20,
        choices=StatutPaiement.choices,
        default=StatutPaiement.REQUIS
    )
    
    id_session_paiement = models.CharField(
        _("ID de session de paiement"),
        max_length=255,
        blank=True,
        null=True
    )
    
    donnees_paiement = models.JSONField(
        _("Données de paiement"),
        default=dict,
        blank=True
    )
    
    frais_transaction = models.DecimalField(
        _("Frais de transaction"),
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    
    net_percu = models.DecimalField(
        _("Montant net perçu"),
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    class Meta:
        verbose_name = _("Abonnement")
        verbose_name_plural = _("Abonnements")
        ordering = ['-date_debut']
        indexes = [
            models.Index(fields=['entreprise', 'est_actif']),
            models.Index(fields=['date_fin']),
        ]

    def __str__(self):
        entreprise_nom = getattr(self.entreprise, 'nom', _("Aucune entreprise"))
        plan_nom = getattr(self.plan_actuel, 'nom_plan', _("Aucun plan"))
        date_fin_str = self.date_fin.strftime('%Y-%m-%d %H:%M') if self.date_fin else _('illimité')
        return f"{_('Abonnement')} {plan_nom} pour {entreprise_nom} ({_('Du')} {self.date_debut.strftime('%Y-%m-%d %H:%M')} {_('au')} {date_fin_str})"

    @property
    def statut(self):
        """Retourne le statut textuel de l'abonnement"""
        if not self.est_actif:
            return _("Inactif")
        if self.is_expired():
            return _("Expiré")
        return _("Actif")

    def is_active(self, with_grace_period=True):
        """
        Vérifie si l'abonnement est actuellement actif.
        - `with_grace_period`: Si True, ajoute une période de grâce de 24h après expiration
        """
        if not self.est_actif:
            return False
        
        now = timezone.now()
        
        # Abonnement illimité
        if self.date_fin is None:
            return True
            
        # Période de grâce de 24h pour éviter les coupures brusques
        if with_grace_period:
            return self.date_fin + timedelta(hours=24) >= now
        
        return self.date_fin >= now

    def is_expired(self):
        """Vérifie si l'abonnement est expiré (sans période de grâce)"""
        return self.date_fin and self.date_fin < timezone.now()

    def save(self, *args, **kwargs):
        """Logique pré-sauvegarde"""
        # Si date_debut n'est pas définie, utiliser maintenant
        if not self.date_debut:
            self.date_debut = timezone.now()
            
        # Mise à jour automatique du statut actif
        if self.date_fin and self.date_fin < timezone.now():
            self.est_actif = False
        elif not self.est_actif and self.date_fin and self.date_fin >= timezone.now():
            self.est_actif = True
            
        super().save(*args, **kwargs)
    @property
    def acces_autorise(self):
        """Détermine si l'accès doit être accordé"""
        return (
            self.est_actif and 
            self.statut_paiement == self.StatutPaiement.COMPLETE and
            (self.date_fin is None or self.date_fin >= timezone.now())
        )

    def calculer_frais(self):
        """Calcule les frais de transaction selon la méthode de paiement"""
        from django.conf import settings
        
        config = settings.PAYMENT_METHODS.get(self.methode_paiement, {})
        if not config:
            return Decimal('0.00')
        
        frais = (self.montant_paye * Decimal(config['fee_percentage'] / 100) + Decimal(config['fee_fixed']))
        return frais.quantize(Decimal('0.01'))
    def activate(self):
        """Active explicitement l'abonnement"""
        self.est_actif = True
        self.save(update_fields=['est_actif', 'date_mise_a_jour'])

    def deactivate(self):
        """Désactive explicitement l'abonnement"""
        self.est_actif = False
        self.save(update_fields=['est_actif', 'date_mise_a_jour'])
# models.py
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Entreprise)
def create_saas_config(sender, instance, created, **kwargs):
    if created:
        ConfigurationSAAS.objects.create(
            entreprise=instance,
            fuseau_horaire='UTC',
            langue='fr',
            expiration_session=30,
            complexite_mdp=ConfigurationSAAS.ComplexiteMDP.MOYEN
        )
        
        
class ConfigurationSAAS(models.Model):
    """
    Configuration spécifique SAAS pour chaque entreprise
    """
    entreprise = models.OneToOneField(
        Entreprise,
        verbose_name=_("Entreprise"),
        on_delete=models.CASCADE,
        related_name='config_saas'
    )
    
    # Modules
    # modules_actifs = models.JSONField(_("Modules activés"), default=list)
    
    # Paramètres système
    fuseau_horaire = models.CharField(_("Fuseau horaire"), max_length=50, default='UTC')
    langue = models.CharField(_("Langue"), max_length=10, default='fr')
    
    # Sécurité
    expiration_session = models.PositiveIntegerField(
        _("Expiration session (minutes)"), 
        default=30,
        validators=[MinValueValidator(5), MaxValueValidator(1440)]
    )
    
    
    taux_tva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('16.00'), # Default TVA rate, e.g., 16%
        help_text="Taux de TVA par défaut en pourcentage (e.g., 16.00 pour 16%)"
    )
    
    class ComplexiteMDP(models.IntegerChoices):
        FAIBLE = 1, _("Faible")
        MOYEN = 2, _("Moyen")
        FORT = 3, _("Fort")
    
    complexite_mdp = models.IntegerField(
        _("Complexité mot de passe"),
        choices=ComplexiteMDP.choices,
        default=ComplexiteMDP.MOYEN
    )
    
    # Devise
    devise_principale = models.ForeignKey(
        'Devise',
        verbose_name=_("Devise principale"),
        on_delete=models.PROTECT,
        null=True
    )

    class Meta:
        verbose_name = _("Configuration SAAS")
        verbose_name_plural = _("Configurations SAAS")
        

class Devise(models.Model):
    """
    Gestion multi-devises avec taux automatiques
    """
    code = models.CharField(_("Code ISO"), max_length=3, unique=True)
    nom = models.CharField(_("Nom"), max_length=50)
    symbole = models.CharField(_("Symbole"), max_length=5)
    active = models.BooleanField(_("Active"), default=True)
    # Très important: ce taux doit être le taux de CETTE devise par rapport à la devise principale de votre SAAS.
    # Si la devise principale de SAAS est EUR, et cette devise est USD, alors taux_par_defaut = 1.08 (si 1 EUR = 1.08 USD)
    taux_par_defaut = models.DecimalField(
        _("Taux par défaut (par rapport à la devise principale du SAAS)"),
        max_digits=12,
        decimal_places=6,
        default=Decimal('1.0'), # La devise principale du SAAS doit avoir 1.0 comme taux_par_defaut
        validators=[MinValueValidator(Decimal('0'))]
    )
    
    symbole_avant = models.BooleanField(_("Symbole avant montant"), default=False)
    decimales = models.PositiveIntegerField(
        _("Nombre de décimales"),
        default=2,
        validators=[MinValueValidator(0), MaxValueValidator(6)]
    )
    
    class Meta:
        verbose_name = _("Devise")
        verbose_name_plural = _("Devises")
        ordering = ['code']
        
    def __str__(self):
        return f"{self.code} ({self.symbole})"
        
    def clean(self):
        if self.code == self.symbole:
            raise ValidationError(
                _("Le code et le symbole ne peuvent pas être identiques")
            )
            
    # La méthode convertir_montant est supprimée ou profondément modifiée
    # car la logique de conversion directe par taux_par_defaut sera gérée dans la vue.
    # Conservez uniquement formater_montant si elle est utilisée.

    def formater_montant(self, montant):
        """
        Formate un montant selon les règles de la devise (symbole, décimales).
        """
        if not isinstance(montant, Decimal):
            try:
                montant = Decimal(str(montant))
            except Exception:
                montant = Decimal('0.00')

        if self.symbole_avant:
            return f"{self.symbole}{montant:.{self.decimales}f}"
        else:
            return f"{montant:.{self.decimales}f}{self.symbole}"
    
    
class TauxChange(models.Model):
    """
    Historique des taux de change avec source de données
    """
    devise_source = models.ForeignKey(
        Devise,
        verbose_name=_("Devise source"),
        on_delete=models.CASCADE,
        related_name='taux_sources'
    )
    devise_cible = models.ForeignKey(
        Devise,
        verbose_name=_("Devise cible"),
        on_delete=models.CASCADE,
        related_name='taux_cibles'
    )
    taux = models.DecimalField(
        _("Taux"),
        max_digits=12,
        decimal_places=6,
        validators=[MinValueValidator(0)]
    )
    date_application = models.DateField(_("Date d'application"))
    
    # Source du taux
    class SourceTaux(models.TextChoices):
        API = 'API', 'API'
        MANUEL = 'MAN', _("Manuel")
        BANQUE = 'BANK', _("Banque centrale")
    
    source = models.CharField(
        _("Source"),
        max_length=10,
        choices=SourceTaux.choices,
        default=SourceTaux.API
    )
    est_actif = models.BooleanField(_("Actif"), default=True)
    
    class Meta:
        verbose_name = _("Taux de change")
        verbose_name_plural = _("Taux de change")
        unique_together = ('devise_source', 'devise_cible', 'date_application')
        ordering = ['-date_application']
        
    def __str__(self):
        return f"{self.devise_source} → {self.devise_cible} ({self.date_application})"
        
    def clean(self):
        """Validation supplémentaire"""
        if self.devise_source == self.devise_cible:
            raise ValidationError(
                _("La devise source et la devise cible ne peuvent pas être identiques")
            )
            
    def activer(self):
        """Active ce taux et désactive les anciens"""
        TauxChange.objects.filter(
            devise_source=self.devise_source,
            devise_cible=self.devise_cible,
            est_actif=True
        ).update(est_actif=False)
        self.est_actif = True
        self.save()

class ParametreDocument(models.Model):
    """
    Numérotation automatique des documents
    """
    class TypeDocument(models.TextChoices):
        FACTURE = 'FACTURE', _('Facture')
        DEVIS = 'DEVIS', _('Devis')
        BON_LIVRAISON = 'BON_LIV', _('Bon de livraison')
        COMMANDE = 'CMD', _('Commande')
    
    entreprise = models.ForeignKey(
        Entreprise,
        verbose_name=_("Entreprise"),
        on_delete=models.CASCADE,
        related_name='parametres_docs'
    )
    type_document = models.CharField(
        _("Type de document"),
        max_length=10,
        choices=TypeDocument.choices
    )
    prefixe = models.CharField(_("Préfixe"), max_length=10)
    suffixe = models.CharField(_("Suffixe"), max_length=10, blank=True)
    compteur = models.PositiveIntegerField(_("Compteur actuel"), default=1)
    format_compteur = models.CharField(_("Format compteur"), max_length=10, default='0000')
    
    class Reinitialisation(models.TextChoices):
        NEVER = 'NEVER', _('Jamais')
        YEARLY = 'YEARLY', _('Annuelle')
        MONTHLY = 'MONTHLY', _('Mensuelle')
    
    reinitialisation = models.CharField(
        _("Réinitialisation"),
        max_length=10,
        choices=Reinitialisation.choices,
        default=Reinitialisation.NEVER
    )

    class Meta:
        verbose_name = _("Paramètre document")
        verbose_name_plural = _("Paramètres documents")
        unique_together = ('entreprise', 'type_document')

    def __str__(self):
        return f"{self.get_type_document_display()} - {self.entreprise}"

class AuditConfiguration(models.Model):
    """
    Journal des modifications de configuration
    """
    entreprise = models.ForeignKey(
        Entreprise,
        verbose_name=_("Entreprise"),
        on_delete=models.CASCADE
    )
    utilisateur = models.ForeignKey(
        User, # C'est correct, car User est déjà résolu via get_user_model()
        verbose_name=_("Utilisateur"),
        on_delete=models.SET_NULL,
        null=True
    )
    action = models.CharField(_("Action"), max_length=50)
    modele = models.CharField(_("Modèle affecté"), max_length=50)
    ancienne_valeur = models.JSONField(_("Ancienne valeur"), null=True)
    nouvelle_valeur = models.JSONField(_("Nouvelle valeur"), null=True)
    timestamp = models.DateTimeField(_("Horodatage"), auto_now_add=True)

    class Meta:
        verbose_name = _("Audit configuration")
        verbose_name_plural = _("Audits configurations")
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['entreprise', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.timestamp} - {self.action}"
    
    
    
class HistoriqueAbonnement(models.Model):
    """Journal des modifications d'abonnement"""
    abonnement = models.ForeignKey(
        Abonnement,
        on_delete=models.CASCADE,
        related_name='historique'
    )
    utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Correct, car c'est une chaîne de caractères
        on_delete=models.SET_NULL,
        null=True
    )
    action = models.CharField(max_length=50)
    ancienne_valeur = models.JSONField(null=True)
    nouvelle_valeur = models.JSONField(null=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']