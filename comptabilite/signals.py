# comptabilite/signals.py
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)

@receiver(post_save, sender='ventes.PaiementPOS')
def creer_ecriture_comptable_paiement_pos(sender, instance, created, **kwargs):
    """Signal pour les paiements POS"""
    if created:
        try:
            logger.info(f"Signal déclenché pour PaiementPOS {instance.id}")
            from ventes.models import PaiementPOS
            if isinstance(instance, PaiementPOS):
                result = instance.enregistrer_ecriture_comptable()
                if result:
                    logger.info(f"Écriture comptable créée via signal: {result.numero}")
                else:
                    logger.warning("Écriture comptable non créée via signal")
        except Exception as e:
            logger.error(f"Erreur dans le signal PaiementPOS: {e}")