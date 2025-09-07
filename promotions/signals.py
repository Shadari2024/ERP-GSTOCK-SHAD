from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Promotion

@receiver([post_save, post_delete], sender=Promotion)
def update_product_prices(sender, instance, **kwargs):
    """Mettre à jour les prix promotionnels des produits concernés"""
    # Import différé pour éviter les circulaires
    from STOCK.models import Produit
    
    for ligne in instance.promotionligne_set.all():
        produit = ligne.produit
        produit.prix_promotionnel = instance.calculer_prix_promotionnel(produit)
        produit.save(update_fields=['prix_promotionnel'])