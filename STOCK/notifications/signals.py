from django.db.models.signals import post_save
from django.dispatch import receiver
from STOCK.models import *  # ou le bon chemin selon ton projet
from django.contrib.auth.models import User


@receiver(post_save, sender=Produit)
def verifier_stock_faible(sender, instance, **kwargs):
    if instance.stock < 5:  # seuil d'alerte
        admins = User.objects.filter(is_staff=True)
        for admin in admins:
            Notification.objects.create(
                destinataire=admin,
                message=f"Stock faible pour le produit : {instance.nom} ({instance.stock})",
                type="stock"
            )


def notifier_nouvelle_commande(commande):
    for utilisateur in User.objects.filter(is_staff=True):
        Notification.objects.create(
            utilisateur=utilisateur,
            message=f"Nouvelle commande #{commande.id} créée par {commande.client.nom}.",
            url=f"/commandes/{commande.id}/"
        )