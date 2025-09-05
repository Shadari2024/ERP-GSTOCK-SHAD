from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Commande, Facture
import datetime

@receiver(post_save, sender=Commande)
def creer_facture(sender, instance, created, **kwargs):
    if created and instance.vente_confirmee:
        Facture.objects.create(
            commande=instance,
            numero=f"FACT-{datetime.date.today().year}-{instance.id}",
            montant_total=instance.montant_total
        )
        
        
from django.db.models.signals import post_save
from django.dispatch import receiver
from STOCK.models import *

@receiver(post_save, sender=Paiement)
def creer_transaction_paiement(sender, instance, created, **kwargs):
    if created:
        # Logique pour déterminer le compte (ex: ESP pour espèces)
        compte = Compte.objects.filter(type_compte='ESP').first()
        if compte:
            Transaction.objects.create(
                compte=compte,
                type_transaction='ENTREE',
                montant=instance.montant,
                mode_paiement=instance.methode[:3].upper(),
                description=f"Paiement facture {instance.facture.numero}",
                commande=instance.facture.commande,
                utilisateur=instance.facture.commande.vendeur
            )

@receiver(post_save, sender=Achat)
def creer_transaction_achat(sender, instance, created, **kwargs):
    if created:
        # Logique pour déterminer le compte (ex: BQ pour banque)
        compte = Compte.objects.filter(type_compte='BQ').first()
        if compte:
            Transaction.objects.create(
                compte=compte,
                type_transaction='SORTIE',
                montant=instance.total_achat,
                mode_paiement='VIR',
                description=f"Achat {instance.produit.nom} chez {instance.fournisseur.nom}",
                achat=instance,
                utilisateur=instance.created_by
            )