# signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from parametres.models import Entreprise, Module, ModuleEntreprise

@receiver(post_save, sender=Entreprise)
def init_entreprise_modules(sender, instance, created, **kwargs):
    if created:
        # Activer les modules par défaut pour la nouvelle entreprise
        modules_defaut = Module.objects.filter(actif_par_defaut=True)
        for module in modules_defaut:
            ModuleEntreprise.objects.create(
                entreprise=instance,
                module=module,
                est_actif=True
            )