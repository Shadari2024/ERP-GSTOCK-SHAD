from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
import barcode
from django.core.files.base import ContentFile
from barcode.writer import ImageWriter
from io import BytesIO
from django.core.files import File
from io import BytesIO
from django.core.files.base import ContentFile
from django.db.models import Avg, F
from django.db.models import Sum
from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction
from decimal import InvalidOperation
from django.db.models import Max
from parametres.models import Entreprise
import string
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
User = get_user_model()
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import timedelta
from django.db.models import Sum, F, ExpressionWrapper, DecimalField



#Notification 

from django.db import models
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import secrets
import string
from datetime import timedelta

        
class Notification(models.Model):
    destinataire = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    est_lu = models.BooleanField(default=False)
    type = models.CharField(max_length=50, choices=[
        ('stock', 'Stock faible'),
        ('commande', 'Nouvelle commande'),
        ('facture', 'Facture impayée')
    ])
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification ({self.type}) pour {self.destinataire.username}"



# -------------------- PARAMÈTRES --------------------
from django.contrib.auth.models import User

class Parametre(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='parametre')
    nom_societe = models.CharField(max_length=100)
    adresse = models.TextField()
    telephone = models.CharField(max_length=20)
    email = models.EmailField()
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    devise_principale = models.CharField(max_length=10, default="USD", verbose_name="Devise principale", blank=True)
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2, default=16.0)
    taux_change_auto = models.BooleanField(default=False, help_text="Mettre à jour automatiquement les taux de change")

    # Champs à ajouter :
    openexchangerates_app_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="05d712c4f2ec421b831c73ca25285688"
    )
    openexchangerates_base_devise = models.CharField(
        max_length=10,
        default="FC",
        help_text="Devise de base pour les taux OpenExchangeRates"
    )

    def __str__(self):
        return self.nom_societe

    def format_devise(self, montant, devise=None):
        devise = devise or self.devise_principale
        symboles = {
            'USD': '$',
            'EUR': '€', 
            'CDF': 'FC',
            'FC': 'FC'
        }
        symbole = symboles.get(devise, devise)
        
        try:
            montant = Decimal(str(montant))
            return f"{symbole} {montant:,.2f}".replace(",", " ").replace(".", ",")
        except:
            return f"{symbole} {montant}"
    
    # Nouveaux champs pour la gestion des devises
    devises_acceptees = models.JSONField(
        default=list,
        help_text="Liste des devises acceptées (ex: ['USD', 'EUR', 'CDF'])"
    )
    taux_change_auto = models.BooleanField(
        default=False,
        help_text="Mettre à jour automatiquement les taux de change"
    )
    
    def __str__(self):
        return self.nom_societe
    

    
    def convertir_en_devise_principale(self, montant, devise_origine):
        """
        Convertit un montant depuis une devise d'origine vers la devise principale.
        """
        if not devise_origine or devise_origine == self.devise_principale:
            return montant  # Pas de conversion nécessaire
        
        taux = TauxChange.get_taux(devise_origine, self.devise_principale)
        if taux is None:
            raise ValidationError(f"Aucun taux de change disponible pour convertir {devise_origine} en {self.devise_principale}")
        
        return Decimal(montant) * taux
    
    def convertir_vers_devise_affichee(self, montant, devise_cible):
        """Convertit un montant depuis la devise principale vers la devise cible."""
        if devise_cible == self.devise_principale:
            return montant

        try:
            taux = TauxChange.get_taux(self.devise_principale, devise_cible)
            return Decimal(montant) * Decimal(str(taux))
        except (TauxChange.DoesNotExist, InvalidOperation):
            return montant


class TauxChange(models.Model):
    devise_source = models.CharField(max_length=3)  # Ex: USD
    devise_cible = models.CharField(max_length=3)   # Ex: CDF
    taux = models.DecimalField(max_digits=12, decimal_places=6)
    date_mise_a_jour = models.DateTimeField(auto_now=True)
    est_manuel = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('devise_source', 'devise_cible')
        verbose_name = "Taux de change"
        verbose_name_plural = "Taux de change"
    
    def __str__(self):
        return f"1 {self.devise_source} = {self.taux} {self.devise_cible}"
    @classmethod
    def convertir(cls, montant, source, cible):
        taux = cls.get_taux(source, cible)
        if taux is None:
            raise ValidationError(f"Aucun taux de change défini entre {source} et {cible}")
        return montant * taux

    
    @classmethod
    def get_taux(cls, source, cible):
        try:
            if source == cible:
                return Decimal('1.0')
            
            # Chercher le taux direct
            taux = cls.objects.get(devise_source=source, devise_cible=cible).taux
            return taux
        except cls.DoesNotExist:
            # Essayer de trouver un taux inverse
            try:
                taux_inverse = cls.objects.get(devise_source=cible, devise_cible=source).taux
                return Decimal('1.0') / taux_inverse
            except (cls.DoesNotExist, ZeroDivisionError):
                return None
            
    




from django.contrib.auth import get_user_model

User = get_user_model()
# -------------------- CATÉGORIE --------------------
class Categorie(models.Model):
    nom = models.CharField(max_length=100)
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='media/', blank=True, null=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    cree_par = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='categories_crees'
    )

    class Meta:
        unique_together = ('entreprise', 'nom')  # Nom unique par entreprise
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        ordering = ['nom']

    def __str__(self):
        return f"{self.nom} ({self.entreprise.nom})"



# -------------------- PRODUIT --------------------
class Produit(models.Model):
    entreprise = models.ForeignKey(
        'parametres.Entreprise', # Assurez-vous que 'Entreprise' est correctement lié
        on_delete=models.CASCADE,
        related_name='produits'
    )
    categorie = models.ForeignKey('Categorie', on_delete=models.SET_NULL, null=True, blank=True)
    actif = models.BooleanField(default=True)
    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    prix_achat = models.DecimalField(max_digits=10, decimal_places=2)
    prix_vente = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0) # Votre champ de stock existant
    seuil_alerte = models.IntegerField(default=10)
    photo = models.ImageField(upload_to='media/produits/', blank=True, null=True)
    code_barre = models.ImageField(upload_to='media/barcodes/', blank=True, null=True)
    code_barre_numero = models.CharField(max_length=13, blank=True, null=True, editable=False)
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    libelle = models.CharField(max_length=100, blank=True)
    cree_par  = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Créé par"
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        unique_together = ('entreprise', 'nom') # Exemple : un nom de produit unique par entreprise

    def __str__(self):
        return f"{self.nom} ({self.code_barre_numero or 'N/A'})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs) # Sauvegarde initiale pour obtenir un ID

        if is_new and not self.code_barre_numero: # Générer le code-barres seulement si nouveau et non déjà généré
            self.generate_barcode()
            # Utilise update_fields pour ne sauvegarder que les champs modifiés
            super().save(update_fields=['code_barre', 'code_barre_numero'])

    def generate_barcode(self):
        # Utilise l'ID du produit pour garantir l'unicité
        product_code_base = f"{self.pk:012d}"
        # S'assurer que le code de base ne dépasse pas 12 chiffres
        product_code = product_code_base[:12].ljust(12, '0') 
        checksum = self.calculate_ean13_checksum(product_code)
        ean13_code = f"{product_code}{checksum}"
        self.code_barre_numero = ean13_code

        ean = barcode.get_barcode_class('ean13')
        barcode_data = ean(ean13_code, writer=ImageWriter())

        buffer = BytesIO()
        barcode_data.write(buffer)
        filename = f"barcode_{self.pk}.png" # Utilise self.pk
        self.code_barre.save(filename, ContentFile(buffer.getvalue()), save=False)
        buffer.close()

    @staticmethod
    def calculate_ean13_checksum(code):
        if len(code) != 12:
            raise ValueError("Le code doit avoir 12 chiffres")
        
        sum_odd = sum(int(code[i]) for i in range(0, 12, 2))
        sum_even = sum(int(code[i]) for i in range(1, 12, 2))
        total = sum_odd + sum_even * 3
        checksum = (10 - (total % 10)) % 10
        return str(checksum)

   # In your models.py file, within the Produit model

    # --- NOUVELLES MÉTHODES POUR LA GESTION DU STOCK ---
    def ajouter_stock(self, quantite_a_ajouter):
        if not isinstance(quantite_a_ajouter, Decimal):
            quantite_a_ajouter = Decimal(str(quantite_a_ajouter))

        if quantite_a_ajouter <= Decimal('0'):
            return False 

        # Atomically update the stock in the database
        # This is the line that needs correction
        Produit.objects.filter(pk=self.pk).update(stock=F('stock') + quantite_a_ajouter)
        
        # Refresh the current instance from the database to reflect the change
        self.refresh_from_db() 
        return True

 # --- NOUVELLES MÉTHODES POUR LA GESTION DU STOCK ---
    def ajouter_stock(self, quantite_a_ajouter):
        if not isinstance(quantite_a_ajouter, Decimal):
            quantite_a_ajouter = Decimal(str(quantite_a_ajouter))

        if quantite_a_ajouter <= Decimal('0'):
            return False 

        # Atomically update the stock in the database
        # CHANGE HERE: Use 'stock' instead of 'quantite_en_stock'
        Produit.objects.filter(pk=self.pk).update(stock=F('stock') + quantite_a_ajouter)
        
        # Refresh the current instance from the database to reflect the change
        self.refresh_from_db() 
        return True
    
    def prix_vente_suggere(self):
        """
        Suggestion de prix basé sur la marge moyenne de la catégorie
        ou un coefficient par défaut si aucune donnée.
        """
        if self.categorie:
            produits_categorie = Produit.objects.filter(categorie=self.categorie).exclude(id=self.id)
            moyenne_marge = produits_categorie.annotate(
                marge=F('prix_vente') - F('prix_achat')
            ).aggregate(marge_moy=Avg('marge'))['marge_moy']
        else:
            moyenne_marge = None

        if moyenne_marge and moyenne_marge > 0:
            return round(float(self.prix_achat) + float(moyenne_marge), 2)
        else:
            coefficient_par_defaut = 1.25  # 25% de marge par défaut
            return round(float(self.prix_achat) * coefficient_par_defaut, 2)
# STOCK/Client.py
from django.db import models
from django.core.validators import validate_email, RegexValidator
from django.utils.translation import gettext_lazy as _
from parametres.models import Entreprise, Devise
from django_countries.fields import CountryField
import uuid
from django.conf import settings  # Import settings

# Importations corrigées pour les modèles Entreprise et Devise
from parametres.models import Entreprise, Devise
from django.db.models import Max # Import Max pour la fonction d'agrégation

class Client(models.Model):
    class TypeClient(models.TextChoices):
        PARTICULIER = 'PART', _('Particulier')
        ENTREPRISE = 'ENT', _('Entreprise')
        ADMINISTRATION = 'ADM', _('Administration')
        REVENDEUR = 'REV', _('Revendeur')

    class StatutClient(models.TextChoices):
        ACTIF = 'ACT', _('Actif')
        INACTIF = 'INA', _('Inactif')
        EN_ATTENTE = 'ATT', _('En attente')
        BLOQUE = 'BLO', _('Bloqué')

    # Identifiant unique
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Relation avec l'entreprise SaaS (importé de parametres.models)
    entreprise = models.ForeignKey(
        Entreprise,
        on_delete=models.CASCADE,
        related_name='clients',
        verbose_name=_("Entreprise propriétaire")
    )

    # Informations de base
    type_client = models.CharField(
        max_length=4,
        choices=TypeClient.choices,
        default=TypeClient.PARTICULIER,
        verbose_name=_("Type de client")
    )
    statut = models.CharField(
        max_length=3,
        choices=StatutClient.choices,
        default=StatutClient.ACTIF,
        verbose_name=_("Statut")
    )
    code_client = models.CharField(
        max_length=20,
        # unique=True, # NE PAS DÉCOMMENTER OU AJOUTER CELA ! C'est géré par UniqueConstraint ci-dessous.
        blank=True,
        null=True,
        verbose_name=_("Code client")
    )
    nom = models.CharField(
        max_length=100,
        verbose_name=_("Nom complet/Raison sociale")
    )

    # Coordonnées
    telephone = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r'^\+?[\d\s-]{10,20}$',
                message=_("Format de téléphone invalide")
            )
        ],
        verbose_name=_("Téléphone")
    )
    telephone_secondaire = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_("Téléphone secondaire")
    )
    email = models.EmailField(
        validators=[validate_email],
        blank=True,
        null=True,
        verbose_name=_("Email")
    )
    website = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("Site web")
    )

    # Adresse
    adresse = models.TextField(
        verbose_name=_("Adresse complète"),
        blank=True,
        null=True
    )
    ville = models.CharField(
        max_length=100,
        verbose_name=_("Ville"),
        blank=True,
        null=True
    )
    code_postal = models.CharField(
        max_length=20,
        verbose_name=_("Code postal"),
        blank=True,
        null=True
    )
    pays = CountryField(
        blank=True,
        null=True,
        verbose_name=_("Pays")
    )

    # Informations commerciales
    devise_preferee = models.ForeignKey(
        Devise, # Importé de parametres.models
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Devise préférée")
    )
    limite_credit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name=_("Limite de crédit")
    )
    delai_paiement = models.PositiveIntegerField(
        default=30,
        verbose_name=_("Délai de paiement (jours)")
    )
    taux_remise = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        verbose_name=_("Taux de remise (%)")
    )

    # Informations fiscales
    numero_tva = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_("Numéro de TVA")
    )
    numero_fiscal = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_("Numéro fiscal")
    )
    exonere_tva = models.BooleanField(
        default=False,
        verbose_name=_("Exonéré de TVA")
    )

    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes internes"))
    cree_le = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date de création")
    )
    modifie_le = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Dernière modification")
    )
    cree_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='clients_crees',
        verbose_name=_("Créé par")
    )

    class Meta:
        verbose_name = _("Client")
        verbose_name_plural = _("Clients")
        ordering = ['nom']
        constraints = [
            models.UniqueConstraint(
                fields=['entreprise', 'code_client'],
                name='code_client_unique_par_entreprise',
                # La condition ci-dessous permet d'avoir plusieurs code_client=NULL si vous le souhaitez.
                # Si chaque client doit *toujours* avoir un code, même temporairement avant la génération,
                # et que vous ne voulez pas de NULLs, alors vous pouvez enlever null=True du champ et cette condition.
                # Mais si la génération automatique est la principale source, null=True et cette condition sont bien.
                condition=~models.Q(code_client__isnull=True),
            ),
            models.UniqueConstraint(
                fields=['entreprise', 'email'],
                condition=models.Q(email__isnull=False) & ~models.Q(email=''), # Unique si email n'est pas NULL et n'est pas vide
                name='email_unique_par_entreprise'
            )
        ]

    def __str__(self):
        return f"{self.nom} ({self.get_type_client_display()})"

    def save(self, *args, **kwargs):
        # 1. Validation cohérence type client/raison sociale
        if self.type_client == self.TypeClient.ENTREPRISE and not self.nom:
            raise ValueError(_("Les clients entreprise doivent avoir une raison sociale"))

        # 2. Génération automatique du code client si vide
        if not self.code_client:
            with transaction.atomic():
                prefix = self.type_client[:2].upper()
                
                # Cherche le dernier code client pour cette entreprise et ce préfixe
                # Cela agrège le maximum de 'code_client' qui commence par le préfixe donné,
                # pour l'entreprise en question.
                max_code_obj = Client.objects.filter(
                    entreprise=self.entreprise,
                    code_client__startswith=f'{prefix}-'
                ).aggregate(max_val=Max('code_client'))
                
                max_code = max_code_obj['max_val']
                
                next_num = 1
                if max_code:
                    try:
                        # Extrait la partie numérique du code (ex: 'PART-0012' -> '0012' -> 12)
                        num_part = max_code.split('-')[-1]
                        next_num = int(num_part) + 1
                    except (ValueError, IndexError):
                        # Gérer les cas où le format n'est pas comme prévu ou si split échoue
                        next_num = 1 # Fallback sécurisé en cas de format invalide
                
                self.code_client = f"{prefix}-{next_num:04d}" # Formatage avec 4 chiffres (ex: 0001)

        # 3. Appel à la méthode save() parente pour enregistrer l'instance
        super().save(*args, **kwargs)

    @property
    def adresse_complete(self):
        elements = []
        if self.adresse:
            elements.append(self.adresse)
        if self.code_postal:
            elements.append(self.code_postal)
        if self.ville:
            elements.append(self.ville)
        if self.pays:
            elements.append(str(self.pays))
        return ", ".join(elements)


    #Historique

class MouvementStock(models.Model):
    TYPE_MOUVEMENT = [
        ('entree', 'Entrée'),
        ('sortie', 'Sortie'),
        ('inventaire', 'Inventaire'),
        ('ajustement', 'Ajustement'),
    ]

    produit = models.ForeignKey('Produit', on_delete=models.CASCADE)
    type_mouvement = models.CharField(max_length=20, choices=TYPE_MOUVEMENT)
    quantite = models.DecimalField(max_digits=10, decimal_places=2)
    date_mouvement = models.DateTimeField(auto_now_add=True)
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    commentaire = models.TextField(blank=True, null=True)
    entreprise = models.ForeignKey('parametres.Entreprise', on_delete=models.CASCADE)
    reference = models.CharField(max_length=100, blank=True, null=True, verbose_name="Référence (BL, Facture, etc.)")
    # Prix unitaire au moment du mouvement pour la valorisation
    prix_unitaire_moment = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        verbose_name="Prix unitaire au moment du mouvement"
    )

    class Meta:
        verbose_name = "Mouvement de Stock"
        verbose_name_plural = "Mouvements de Stock"
        ordering = ['-date_mouvement']

    def __str__(self):
        return f"{self.get_type_mouvement_display()} - {self.produit.nom} - {self.quantite}"

    def save(self, *args, **kwargs):
        # CORRECTION: Utiliser prix_achat au lieu de prix_unitaire
        if not self.prix_unitaire_moment and self.produit:
            self.prix_unitaire_moment = self.produit.prix_achat  # ← CORRECTION ICI
        
        super().save(*args, **kwargs)

    @property
    def valeur_mouvement(self):
        """Retourne la valeur monétaire du mouvement"""
        return self.quantite * self.prix_unitaire_moment

# STOCK/models.py
from django.db import models, transaction
from django.utils import timezone
from django.conf import settings
from decimal import Decimal

# Import des modèles externes
from parametres.models import Entreprise
from STOCK.models import Produit, MouvementStock
from comptabilite.models import EcritureComptable, PlanComptableOHADA, JournalComptable, LigneEcriture

# Votre modèle InventairePhysique
class InventairePhysique(models.Model):
    STATUT_CHOICES = [
        ('brouillon', 'Brouillon'),
        ('en_cours', 'En cours'),
        ('valide', 'Validé'),
        ('comptabilise', 'Comptabilisé'),
    ]

    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE)
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE)
    stock_theorique = models.IntegerField()
    stock_physique = models.IntegerField()
    ecart = models.IntegerField()
    valeur_ecart = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(auto_now_add=True)
    valide = models.BooleanField(default=False)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='brouillon')
    ecriture_comptable = models.ForeignKey('comptabilite.EcritureComptable', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Inventaire Physique"
        verbose_name_plural = "Inventaires Physiques"
        ordering = ['-date']

    def save(self, *args, **kwargs):
        self.ecart = self.calculer_ecart()
        
        if self.produit:
            # Assurez-vous que le prix d'achat est un Decimal pour le calcul
            prix_achat = Decimal(str(self.produit.prix_achat))
            self.valeur_ecart = abs(Decimal(str(self.ecart))) * prix_achat
        
        super().save(*args, **kwargs)

    def calculer_ecart(self):
        return self.stock_physique - self.stock_theorique

    @property
    def type_ecart(self):
        if self.ecart > 0:
            return "excédent"
        elif self.ecart < 0:
            return "déficit"
        return "neutre"

    def marquer_comptabilise(self, ecriture):
        self.statut = 'comptabilise'
        self.ecriture_comptable = ecriture
        self.save(update_fields=['statut', 'ecriture_comptable', 'updated_at'])

    def __str__(self):
        return f"{self.produit.nom} - Ecart: {self.ecart}"
    
#remise et promotions
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.crypto import get_random_string
from decimal import Decimal
from django.core.validators import MinValueValidator

#IA Et PREDICTION
class SuggestionReapprovisionnement(models.Model):
    produit = models.ForeignKey('Produit', on_delete=models.CASCADE)
    date_suggestion = models.DateField(auto_now_add=True)
    quantite_predite = models.PositiveIntegerField()
    quantite_suggeree = models.PositiveIntegerField()

    class Meta:
        ordering = ['-date_suggestion']
        verbose_name = "Suggestion de réapprovisionnement"
        verbose_name_plural = "Suggestions de réapprovisionnement"

    def __str__(self):
        return f"{self.produit.nom} - {self.date_suggestion} : {self.quantite_suggeree}"
    
    
# STOCK/models.py
class ChatbotConversation(models.Model):
    """Conversations chatbot avec isolation SaaS"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chatbot_conversations'
    )
    entreprise = models.ForeignKey(
        'parametres.Entreprise',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    query = models.TextField(verbose_name=_("Requête"))
    response = models.JSONField(verbose_name=_("Réponse"))
    metadata = models.JSONField(
        default=dict,
        verbose_name=_("Métadonnées techniques")
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Horodatage")
    )

    class Meta:
        verbose_name = _('Conversation Chatbot')
        verbose_name_plural = _('Conversations Chatbot')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['entreprise']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"Chatbot - {self.user.username} - {self.timestamp}"

class ChatbotKnowledge(models.Model):
    QUESTION_TYPE_CHOICES = [
        ('stock', 'Stock'),
        ('vente', 'Ventes'),
        ('client', 'Clients'),
        ('produit', 'Produits'),
    ]
    
    question_pattern = models.CharField(max_length=255)
    response_template = models.TextField()
    query_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    required_permissions = models.CharField(max_length=100, blank=True)
    
    
    
class BaseConnaissance(models.Model):
    question = models.TextField(unique=True)
    reponse = models.TextField()
    
    def __str__(self):
        return self.question[:50]
    
    

