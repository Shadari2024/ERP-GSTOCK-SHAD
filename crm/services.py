from django.core.mail import send_mail
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.template import Template, Context
import logging
from datetime import timedelta

from .models import RegleAutomatisation, TemplateEmail, Activite, Notification

logger = logging.getLogger(__name__)

class AutomationService:
    def __init__(self, entreprise):
        self.entreprise = entreprise
    
    def executer_regles(self, type_declencheur, **kwargs):
        """Exécute les règles d'automatisation pour un type de déclencheur"""
        regles = RegleAutomatisation.objects.filter(
            entreprise=self.entreprise,
            type_declencheur=type_declencheur,
            actif=True
        )
        
        for regle in regles:
            try:
                self.executer_regle(regle, **kwargs)
            except Exception as e:
                logger.error(f"Erreur lors de l'exécution de la règle {regle.nom}: {str(e)}")
    
    def executer_regle(self, regle, **kwargs):
        """Exécute une règle spécifique"""
        if regle.type_action == 'notification':
            self.creer_notification(regle, **kwargs)
        elif regle.type_action == 'email':
            self.envoyer_email(regle, **kwargs)
        elif regle.type_action == 'changement_statut':
            self.changer_statut(regle, **kwargs)
        elif regle.type_action == 'creation_activite':
            self.creer_activite(regle, **kwargs)
        elif regle.type_action == 'assignation':
            self.assigner_utilisateur(regle, **kwargs)
    
    def creer_notification(self, regle, **kwargs):
        """Crée une notification basée sur la règle"""
        opportunite = kwargs.get('opportunite')
        activite = kwargs.get('activite')
        
        if not opportunite:
            return
        
        # 1. Notification au commercial assigné (existant)
        if opportunite.assigne_a:
            titre = self.render_template(regle.parametres.get('titre', ''), **kwargs)
            message = self.render_template(regle.parametres.get('message', ''), **kwargs)
            
            Notification.objects.create(
                utilisateur=opportunite.assigne_a,
                type_notification='systeme',
                titre=titre,
                message=message,
                lien=f"/crm/opportunites/{opportunite.pk}/"
            )
        
        # 2. ✅ NOUVEAU : Notification au client si la règle le demande
        if regle.parametres.get('notifier_client') and hasattr(opportunite, 'client') and opportunite.client:
            titre_client = self.render_template(
                regle.parametres.get('titre_client', 'Mise à jour concernant votre opportunité'),
                **kwargs
            )
            message_client = self.render_template(
                regle.parametres.get('message_client', 'Votre opportunité "{{ opportunite.nom }}" a été mise à jour.'),
                **kwargs
            )
            
            Notification.objects.create(
                utilisateur=opportunite.client,  # ← client est un User
                type_notification='systeme',
                titre=titre_client,
                message=message_client,
                lien=f"/client/opportunites/{opportunite.pk}/"  # ← lien côté client si différent
            )
    
    def envoyer_email(self, regle, **kwargs):
        """Envoie un email basé sur la règle"""
        try:
            template_id = regle.parametres.get('template_id')
            if not template_id:
                return

            template = TemplateEmail.objects.get(id=template_id, entreprise=self.entreprise)
            opportunite = kwargs.get('opportunite')

            if not opportunite:
                return

            # 1. Email au commercial (existant)
            if opportunite.assigne_a and opportunite.assigne_a.email:
                sujet = self.render_template(template.sujet, **kwargs)
                corps = self.render_template(template.corps, **kwargs)
                send_mail(
                    sujet,
                    corps,
                    settings.DEFAULT_FROM_EMAIL,
                    [opportunite.assigne_a.email],
                    fail_silently=False,
                )

            # 2. ✅ NOUVEAU : Email au client si demandé
            if regle.parametres.get('envoyer_au_client') and hasattr(opportunite, 'client') and opportunite.client and opportunite.client.email:
                sujet_client = self.render_template(
                    regle.parametres.get('sujet_client', template.sujet),
                    **kwargs
                )
                corps_client = self.render_template(
                    regle.parametres.get('corps_client', template.corps),
                    **kwargs
                )
                send_mail(
                    sujet_client,
                    corps_client,
                    settings.DEFAULT_FROM_EMAIL,
                    [opportunite.client.email],
                    fail_silently=False,
                )

        except Exception as e:
            logger.error(f"Erreur lors de l'envoi d'email: {str(e)}")
    
    
    def render_template(self, template_text, **kwargs):
        """Rend un template avec les variables disponibles"""
        from django.template import Template, Context
        
        variables = {
            'opportunite': kwargs.get('opportunite'),
            'activite': kwargs.get('activite'),
            'jours_restants': kwargs.get('jours_restants', 0),
            'entreprise': self.entreprise,
        }
        
        template = Template(template_text)
        context = Context(variables)
        return template.render(context)
    
    def creer_activite_rappel(self, opportunite, jours_avant):
        """Crée une activité de rappel automatique"""
        if opportunite.assigne_a:
            date_rappel = opportunite.date_fermeture_prevue - timedelta(days=jours_avant)
            
            Activite.objects.create(
                entreprise=self.entreprise,
                type_activite_id=1,  # À configurer selon vos types
                sujet=f"Rappel: {opportunite.nom}",
                description=f"Rappel automatique pour l'opportunité {opportunite.nom} qui arrive à échéance",
                date_debut=date_rappel,
                date_echeance=date_rappel,
                statut='planifie',
                priorite='elevee',
                assigne_a=opportunite.assigne_a,
                cree_par=opportunite.assigne_a,
                rappel=True,
                date_rappel=date_rappel
            )
            
            
            
# crm/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Opportunite

@receiver(post_save, sender=Opportunite)
def envoyer_email_a_la_creation(sender, instance, created, **kwargs):
    if not created:
        return  # On ne fait rien si ce n'est pas une création

    # 2. ✅ NOUVEAU : Envoyer AU CLIENT
    if hasattr(instance, 'client') and instance.client and hasattr(instance.client, 'email') and instance.client.email:
        sujet_client = f"[{settings.SITE_NAME}] Votre opportunité '{instance.nom}' a été enregistrée"
        message_client = render_to_string('crm/emails/nouvelle_opportunite_client.txt', {
            'opportunite': instance,
            'client': instance.client,
            'site_url': settings.BASE_URL,
        })
        try:
            send_mail(
                sujet_client,
                message_client,
                settings.DEFAULT_FROM_EMAIL,
                [instance.client.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Erreur envoi email client : {e}")