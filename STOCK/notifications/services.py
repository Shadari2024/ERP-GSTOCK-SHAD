# notifications/services.py
from django.conf import settings
from django.contrib.auth.models import User
from STOCK.models import *

class NotificationService:
    @staticmethod
    def create_notification(user, type_notification, level, title, message, url=None, send_email=False):
        """
        Crée une notification et optionnellement envoie un email
        """
        notification = Notification.objects.create(
            user=user,
            type_notification=type_notification,
            level=level,
            title=title,
            message=message,
            url=url
        )
        
        if send_email and user.email:
            NotificationService.send_notification_email(notification)
        
        return notification

    @staticmethod
    def send_notification_email(notification):
        subject = f"[{notification.get_level_display()}] {notification.title}"
        message = f"{notification.message}\n\n"
        
        if notification.url:
            message += f"Accéder: {settings.BASE_URL}{notification.url}"
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [notification.user.email],
            fail_silently=True,
        )
        notification.sent_by_email = True
        notification.save()

    @staticmethod
    def notify_low_stock(produit):
        """
        Notifie quand un produit est en stock faible
        """
        admins = User.objects.filter(is_staff=True)
        message = (f"Le produit {produit.nom} a un stock faible ({produit.stock}). "
                   f"Seuil d'alerte: {produit.seuil_alerte}")
        
        for admin in admins:
            NotificationService.create_notification(
                user=admin,
                type_notification='stock',
                level='warning',
                title=f"Stock faible - {produit.nom}",
                message=message,
                url=f"/admin/stock/produit/{produit.id}/change/",
                send_email=True
            )

    @staticmethod
    def notify_unpaid_invoice(facture):
        """
        Notifie pour les factures impayées
        """
        message = (f"La facture {facture.numero} du {facture.date} "
                   f"d'un montant de {facture.montant_total} est impayée.")
        
        NotificationService.create_notification(
            user=facture.commande.vendeur,
            type_notification='facture',
            level='danger',
            title=f"Facture impayée - {facture.numero}",
            message=message,
            url=f"/factures/{facture.id}/",
            send_email=True
        )