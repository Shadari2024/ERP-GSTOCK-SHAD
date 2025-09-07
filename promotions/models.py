from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from parametres.mixins import EntrepriseAccessMixin

class Promotion(EntrepriseAccessMixin, models.Model):
    TYPE_PROMOTION = (
        ('pourcentage', _('Pourcentage')),
        ('montant_fixe', _('Montant fixe')),
        ('prix_specifique', _('Prix spécifique')),
        ('acheter_x_obtenir_y', _('Acheter X obtenir Y gratuit')),
        ('lot', _('Lot (X pour le prix de Y)')),
    )
    
    STATUT_PROMOTION = (
        ('active', _('Active')),
        ('inactive', _('Inactive')),
        ('planifiee', _('Planifiée')),
        ('expiree', _('Expirée')),
    )
    
    entreprise = models.ForeignKey('parametres.Entreprise', on_delete=models.CASCADE, verbose_name=_('Entreprise'))
    nom = models.CharField(max_length=100, verbose_name=_('Nom de la promotion'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    type_promotion = models.CharField(max_length=20, choices=TYPE_PROMOTION, verbose_name=_('Type de promotion'))
    valeur = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_('Valeur'))
    date_debut = models.DateTimeField(verbose_name=_('Date de début'))
    date_fin = models.DateTimeField(verbose_name=_('Date de fin'))
    statut = models.CharField(max_length=10, choices=STATUT_PROMOTION, default='planifiee', verbose_name=_('Statut'))
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name=_('Date de création'))
    date_modification = models.DateTimeField(auto_now=True, verbose_name=_('Date de modification'))
    
    class Meta:
        verbose_name = _('Promotion')
        verbose_name_plural = _('Promotions')
    
    def __str__(self):
        return f"{self.nom} - {self.get_type_promotion_display()}"
    
    def get_devise_principale(self):
        try:
            from parametres.models import ConfigurationSAAS
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.entreprise)
            return config_saas.devise_principale
        except:
            return None
    
    def calculer_prix_promotionnel(self, produit, quantite=1):
        from STOCK.models import Produit
        
        if not isinstance(produit, Produit):
            try:
                produit = Produit.objects.get(pk=produit)
            except Produit.DoesNotExist:
                return 0
                
        prix_original = produit.prix_vente
        
        if self.type_promotion == 'pourcentage':
            return prix_original * (1 - self.valeur / 100)
        elif self.type_promotion == 'montant_fixe':
            return max(0, prix_original - self.valeur)
        elif self.type_promotion == 'prix_specifique':
            return self.valeur
        elif self.type_promotion == 'acheter_x_obtenir_y':
            x = self.valeur
            y = self.promotionligne_set.first().valeur_secondaire if self.promotionligne_set.exists() else 1
            if quantite >= x:
                lots_complets = quantite // (x + y)
                restant = quantite % (x + y)
                return (lots_complets * x + min(restant, x)) * prix_original / quantite
            return prix_original
        elif self.type_promotion == 'lot':
            x = self.valeur
            y = self.promotionligne_set.first().valeur_secondaire if self.promotionligne_set.exists() else x - 1
            if quantite >= x:
                lots_complets = quantite // x
                restant = quantite % x
                return (lots_complets * y * prix_original + restant * prix_original) / quantite
            return prix_original
        
        return prix_original
    
    def est_active(self):
        now = timezone.now()
        return self.statut == 'active' and self.date_debut <= now <= self.date_fin
    
    def save(self, *args, **kwargs):
        now = timezone.now()
        if self.date_debut and self.date_fin:
            if self.date_debut <= now <= self.date_fin:
                self.statut = 'active'
            elif now > self.date_fin:
                self.statut = 'expiree'
            elif now < self.date_debut:
                self.statut = 'planifiee'
            
        super().save(*args, **kwargs)

class PromotionLigne(models.Model):
    promotion = models.ForeignKey(Promotion, on_delete=models.CASCADE, verbose_name=_('Promotion'))
    produit = models.ForeignKey('STOCK.Produit', on_delete=models.CASCADE, verbose_name=_('Produit'))
    valeur_secondaire = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_('Valeur secondaire'))
    quantite_min = models.PositiveIntegerField(default=1, verbose_name=_('Quantité minimum'))
    
    class Meta:
        verbose_name = _('Ligne de promotion')
        verbose_name_plural = _('Lignes de promotion')
        unique_together = ('promotion', 'produit')
    
    def __str__(self):
        return f"{self.promotion.nom} - {self.produit.nom}"