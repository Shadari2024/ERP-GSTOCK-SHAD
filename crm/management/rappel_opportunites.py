# crm/management/commands/rappel_opportunites.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from crm.models import Opportunite
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

class Command(BaseCommand):
    help = 'Envoie des rappels pour les opportunités dont la date de clôture approche (au commercial ET au client)'

    def handle(self, *args, **options):
        aujourd_hui = timezone.now().date()
        date_limite = aujourd_hui + timedelta(days=3)  # Rappel 3 jours avant

        opportunites_a_rappeler = Opportunite.objects.filter(
            date_fermeture_prevue=date_limite,
            est_terminee=False,
            assigne_a__isnull=False
        )

        count_commerciaux = 0
        count_clients = 0

        for opp in opportunites_a_rappeler:
            # 1. ✅ Envoyer au commercial assigné
            if opp.assigne_a and opp.assigne_a.email:
                try:
                    send_mail(
                        subject=f"[RAPPEL] Opportunité à clôturer bientôt : {opp.nom}",
                        message=f"""Bonjour {opp.assigne_a.get_full_name() or opp.assigne_a.username},

L'opportunité "{opp.nom}" (client : {opp.client.nom}) doit être clôturée le {opp.date_fermeture_prevue.strftime('%d/%m/%Y')}.

Montant estimé : {opp.montant_estime} €
Probabilité : {opp.probabilite}%

Accédez ici : {settings.BASE_URL}{opp.get_absolute_url()}

Merci de finaliser ou de mettre à jour le statut.

Cordialement,
CRM System""",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[opp.assigne_a.email],
                        fail_silently=False,
                    )
                    count_commerciaux += 1
                except Exception as e:
                    logger.error(f"Erreur envoi rappel commercial pour {opp.id}: {e}")

            # 2. ✅ NOUVEAU : Envoyer AU CLIENT si email disponible
            if hasattr(opp, 'client') and opp.client and hasattr(opp.client, 'email') and opp.client.email:
                try:
                    send_mail(
                        subject=f"[RAPPEL] Votre opportunité '{opp.nom}' arrive à échéance",
                        message=f"""Bonjour {opp.client.nom},

Votre opportunité "{opp.nom}" chez {settings.SITE_NAME or 'notre entreprise'} arrive à échéance le {opp.date_fermeture_prevue.strftime('%d/%m/%Y')}.

Montant estimé : {opp.montant_estime} €

Merci de nous contacter si vous avez des questions ou souhaitez prolonger ce dossier.

Cordialement,
L'équipe {settings.SITE_NAME or 'CRM'}""",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[opp.client.email],
                        fail_silently=False,
                    )
                    count_clients += 1
                except Exception as e:
                    logger.error(f"Erreur envoi rappel client pour {opp.id}: {e}")

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ {count_commerciaux} rappels envoyés aux commerciaux, '
                f'{count_clients} rappels envoyés aux clients.'
            )
        )