from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from parametres.models import Entreprise, ConfigurationSAAS
from django.core.exceptions import ValidationError
import json

User = get_user_model()

class KPI(models.Model):
    """Modèle pour les indicateurs de performance"""
    TYPE_KPI_CHOICES = [
        ('financial', _('Financier')),
        ('commercial', _('Commercial')),
        ('stock', _('Stock')),
        ('rh', _('Ressources Humaines')),
        ('custom', _('Personnalisé')),
    ]

    PERIODICITE_CHOICES = [
        ('daily', _('Quotidien')),
        ('weekly', _('Hebdomadaire')),
        ('monthly', _('Mensuel')),
        ('quarterly', _('Trimestriel')),
        ('yearly', _('Annuel')),
    ]

    nom = models.CharField(max_length=100, verbose_name=_("Nom du KPI"))
    code = models.CharField(max_length=50, unique=True, verbose_name=_("Code KPI"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    type_kpi = models.CharField(max_length=20, choices=TYPE_KPI_CHOICES, verbose_name=_("Type de KPI"))
    formule = models.TextField(verbose_name=_("Formule de calcul"))
    periodicite = models.CharField(max_length=20, choices=PERIODICITE_CHOICES, verbose_name=_("Périodicité"))
    unite = models.CharField(max_length=20, verbose_name=_("Unité de mesure"))
    cible = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name=_("Valeur cible"))
    seuil_alerte = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name=_("Seuil d'alerte"))
    
    # Relations avec les autres modules
    module_lie = models.CharField(max_length=50, choices=[
        ('ventes', _('Ventes')),
        ('achats', _('Achats')),
        ('stock', _('Stock')),
        ('compta', _('Comptabilité')),
        ('rh', _('Ressources Humaines')),
        ('crm', _('CRM')),
    ], verbose_name=_("Module lié"))
    
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    actif = models.BooleanField(default=True, verbose_name=_("Actif"))
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_("Créé par"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("KPI")
        verbose_name_plural = _("KPIs")
        ordering = ['nom']
  

    def __str__(self):
        return f"{self.nom} ({self.code})"

    def clean(self):
        # Validation de la formule
        try:
            # Vérifier que la formule est valide
            # Cette validation devrait être plus sophistiquée dans une implémentation réelle
            if not self.formule.strip():
                raise ValidationError(_("La formule ne peut pas être vide"))
        except Exception as e:
            raise ValidationError(_("Formule invalide: %(error)s") % {'error': str(e)})

class KPIValue(models.Model):
    """Valeurs historiques des KPI"""
    kpi = models.ForeignKey(KPI, on_delete=models.CASCADE, verbose_name=_("KPI"))
    valeur = models.DecimalField(max_digits=20, decimal_places=4, verbose_name=_("Valeur"))
    date_mesure = models.DateField(verbose_name=_("Date de mesure"))
    periode = models.CharField(max_length=20, verbose_name=_("Période"))
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Valeur KPI")
        verbose_name_plural = _("Valeurs KPI")
        unique_together = ['kpi', 'date_mesure', 'entreprise']
        ordering = ['-date_mesure']

    def __str__(self):
        return f"{self.kpi.nom} - {self.date_mesure}: {self.valeur}"

class Report(models.Model):
    """Modèle pour les rapports personnalisés"""
    TYPE_RAPPORT_CHOICES = [
        ('tableau', _('Tableau')),
        ('graphique', _('Graphique')),
        ('mixte', _('Mixte')),
    ]

    nom = models.CharField(max_length=100, verbose_name=_("Nom du rapport"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    type_rapport = models.CharField(max_length=20, choices=TYPE_RAPPORT_CHOICES, verbose_name=_("Type de rapport"))
    requete_sql = models.TextField(blank=True, verbose_name=_("Requête SQL"))
    parametres = models.JSONField(default=dict, verbose_name=_("Paramètres"))
    colonnes = models.JSONField(default=list, verbose_name=_("Colonnes"))
    options_graphique = models.JSONField(default=dict, verbose_name=_("Options graphique"))
    public = models.BooleanField(default=False, verbose_name=_("Public"))
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_("Créé par"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Rapport")
        verbose_name_plural = _("Rapports")
        ordering = ['nom']

    def __str__(self):
        return self.nom

class DataExport(models.Model):
    """Modèle pour suivre les exports de données"""
    FORMAT_CHOICES = [
        ('csv', 'CSV'),
        ('excel', 'Excel'),
        ('pdf', 'PDF'),
        ('json', 'JSON'),
    ]

    nom_fichier = models.CharField(max_length=255, verbose_name=_("Nom du fichier"))
    format_export = models.CharField(max_length=10, choices=FORMAT_CHOICES, verbose_name=_("Format"))
    parametres = models.JSONField(default=dict, verbose_name=_("Paramètres d'export"))
    taille_fichier = models.BigIntegerField(default=0, verbose_name=_("Taille du fichier (bytes)"))
    chemin_fichier = models.CharField(max_length=500, verbose_name=_("Chemin du fichier"))
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_("Exporté par"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Export de données")
        verbose_name_plural = _("Exports de données")
        ordering = ['-created_at']

class DataImport(models.Model):
    """Modèle pour suivre les imports de données"""
    STATUT_CHOICES = [
        ('pending', _('En attente')),
        ('processing', _('En cours')),
        ('completed', _('Terminé')),
        ('failed', _('Échoué')),
    ]

    nom_fichier = models.CharField(max_length=255, verbose_name=_("Nom du fichier"))
    type_import = models.CharField(max_length=50, verbose_name=_("Type d'import"))
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='pending', verbose_name=_("Statut"))
    resultat = models.JSONField(default=dict, verbose_name=_("Résultat"))
    erreurs = models.JSONField(default=list, verbose_name=_("Erreurs"))
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, verbose_name=_("Importé par"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Import de données")
        verbose_name_plural = _("Imports de données")
        ordering = ['-created_at']

class AIIntegration(models.Model):
    """Intégration IA pour l'analyse prédictive"""
    TYPE_IA_CHOICES = [
        ('prediction', _('Prédiction')),
        ('classification', _('Classification')),
        ('recommendation', _('Recommandation')),
        ('anomaly', _('Détection d\'anomalies')),
    ]

    nom = models.CharField(max_length=100, verbose_name=_("Nom du modèle"))
    type_ia = models.CharField(max_length=20, choices=TYPE_IA_CHOICES, verbose_name=_("Type d'IA"))
    modele_ia = models.CharField(max_length=200, verbose_name=_("Modèle IA"))
    parametres = models.JSONField(default=dict, verbose_name=_("Paramètres"))
    precision = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True, verbose_name=_("Précision"))
    actif = models.BooleanField(default=True, verbose_name=_("Actif"))
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Intégration IA")
        verbose_name_plural = _("Intégrations IA")
        ordering = ['nom']