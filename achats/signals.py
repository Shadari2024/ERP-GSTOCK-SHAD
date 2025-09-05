from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import CommandeAchat, BonReception
import datetime

@receiver(pre_save, sender=CommandeAchat)
def set_numero_commande(sender, instance, **kwargs):
    if not instance.numero_commande:
        now = datetime.datetime.now()
        prefix = "CA"
        year = now.strftime('%Y')
        month = now.strftime('%m')
        last_num = CommandeAchat.objects.filter(
            numero_commande__startswith=f"{prefix}{year}{month}"
        ).count()
        instance.numero_commande = f"{prefix}{year}{month}{last_num + 1:04d}"

@receiver(pre_save, sender=BonReception)
def set_numero_bon(sender, instance, **kwargs):
    if not instance.numero_bon:
        now = datetime.datetime.now()
        prefix = "BR"
        year = now.strftime('%Y')
        month = now.strftime('%m')
        last_num = BonReception.objects.filter(
            numero_bon__startswith=f"{prefix}{year}{month}"
        ).count()
        instance.numero_bon = f"{prefix}{year}{month}{last_num + 1:04d}"