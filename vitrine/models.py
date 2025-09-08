from django.db import models
from django.utils.translation import gettext_lazy as _
from parametres.models import ConfigurationSAAS

class DemandeDemo(models.Model):
    nom = models.CharField(max_length=100)
    entreprise = models.CharField(max_length=100)
    email = models.EmailField()
    telephone = models.CharField(max_length=20)
    message = models.TextField(blank=True)
    date_soumission = models.DateTimeField(auto_now_add=True)
    traite = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = _("Demande de démo")
        verbose_name_plural = _("Demandes de démo")
        ordering = ['-date_soumission']
    
    def __str__(self):
        return f"{self.nom} - {self.entreprise}"