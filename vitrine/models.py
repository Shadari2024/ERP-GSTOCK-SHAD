from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinLengthValidator

class DemandeDemo(models.Model):
    nom = models.CharField(
        max_length=100,
        verbose_name=_("Nom complet"),
        validators=[MinLengthValidator(2)]
    )
    entreprise = models.CharField(
        max_length=100,
        verbose_name=_("Nom de l'entreprise"),
        validators=[MinLengthValidator(2)]
    )
    email = models.EmailField(verbose_name=_("Adresse email"))
    telephone = models.CharField(
        max_length=20,
        verbose_name=_("Numéro de téléphone")
    )
    message = models.TextField(
        blank=True,
        verbose_name=_("Message additionnel"),
        help_text=_("Décrivez vos besoins spécifiques")
    )
    date_soumission = models.DateTimeField(auto_now_add=True)
    traite = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _("Demande de démonstration")
        verbose_name_plural = _("Demandes de démonstration")
        ordering = ['-date_soumission']
    
    def __str__(self):
        return f"{self.nom} - {self.entreprise}"
    
    def envoyer_notification_admin(self):
        """Envoie une notification email à l'admin"""
        from django.core.mail import send_mail
        from django.conf import settings
        
        sujet = f"Nouvelle demande de démo - {self.entreprise}"
        message = f"""
        Nouvelle demande de démonstration :
        
        Nom: {self.nom}
        Entreprise: {self.entreprise}
        Email: {self.email}
        Téléphone: {self.telephone}
        Message: {self.message}
        
        Date: {self.date_soumission.strftime('%d/%m/%Y %H:%M')}
        """
        
        send_mail(
            sujet,
            message,
            settings.DEFAULT_FROM_EMAIL,
            ['shadarijerome13@gmail.com'],  # Votre email
            fail_silently=False,
        )