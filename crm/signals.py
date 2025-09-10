from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .models import Opportunite, Activite, ObjectifCommercial, ClientCRM

User = get_user_model()

@receiver(post_save, sender=Opportunite)
def opportunite_post_save(sender, instance, created, **kwargs):
    """
    Signal pour les actions après sauvegarde d'une opportunité
    """
    if created:
        # Nouvelle opportunité créée
        print(f"Nouvelle opportunité créée: {instance.nom}")
        
        # Envoyer une notification si assignée à quelqu'un
        if instance.assigne_a and instance.assigne_a != instance.cree_par:
            try:
                send_mail(
                    _("Nouvelle opportunité assignée"),
                    _("Une nouvelle opportunité '{nom}' vous a été assignée.").format(nom=instance.nom),
                    settings.DEFAULT_FROM_EMAIL,
                    [instance.assigne_a.email],
                    fail_silently=True,
                )
            except Exception as e:
                print(f"Erreur envoi email: {e}")
    
    # Vérifier si le statut a changé vers un statut terminé
    if not created and instance.est_terminee and not instance.date_fermeture_reelle:
        instance.date_fermeture_reelle = timezone.now().date()
        instance.save(update_fields=['date_fermeture_reelle'])

@receiver(pre_save, sender=Activite)
def activite_pre_save(sender, instance, **kwargs):
    """
    Signal pour les actions avant sauvegarde d'une activité
    """
    # Vérifier les dates cohérentes
    if instance.date_echeance and instance.date_debut and instance.date_echeance < instance.date_debut:
        from django.core.exceptions import ValidationError
        raise ValidationError(_("La date d'échéance ne peut pas être antérieure à la date de début"))

@receiver(post_save, sender=Activite)
def activite_post_save(sender, instance, created, **kwargs):
    """
    Signal pour les actions après sauvegarde d'une activité
    """
    if created and instance.assigne_a and instance.assigne_a != instance.cree_par:
        # Envoyer une notification pour nouvelle activité assignée
        try:
            send_mail(
                _("Nouvelle activité assignée"),
                _("Une nouvelle activité '{sujet}' vous a été assignée. Date d'échéance: {date}").format(
                    sujet=instance.sujet, 
                    date=instance.date_echeance.strftime('%d/%m/%Y %H:%M')
                ),
                settings.DEFAULT_FROM_EMAIL,
                [instance.assigne_a.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Erreur envoi email: {e}")

@receiver(post_save, sender=ObjectifCommercial)
def objectif_post_save(sender, instance, created, **kwargs):
    """
    Signal pour les actions après sauvegarde d'un objectif
    """
    if created and instance.assigne_a:
        # Notification pour nouvel objectif assigné
        try:
            send_mail(
                _("Nouvel objectif commercial"),
                _("Un nouvel objectif '{nom}' vous a été assigné. Valeur cible: {valeur} {devise}").format(
                    nom=instance.nom,
                    valeur=instance.valeur_cible,
                    devise="€"  # Vous pouvez adapter cela avec la devise de l'entreprise
                ),
                settings.DEFAULT_FROM_EMAIL,
                [instance.assigne_a.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Erreur envoi email: {e}")

@receiver(post_save, sender=ClientCRM)
def client_post_save(sender, instance, created, **kwargs):
    """
    Signal pour les actions après sauvegarde d'un client
    """
    if created:
        # Log de création d'un nouveau client
        print(f"Nouveau client CRM créé: {instance.nom}")

# Vous pouvez ajouter d'autres signaux selon vos besoins