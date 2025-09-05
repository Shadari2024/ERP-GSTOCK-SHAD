from django.db import models
from django.conf import settings  # Ajoutez cette importation
from django.utils.translation import gettext_lazy as _
from parametres.models import ConfigurationSAAS, Entreprise
from comptabilite.models import PlanComptableOHADA
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image, ImageDraw, ImageFont
import os
from django.conf import settings
from datetime import datetime


class Departement(models.Model):
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    code = models.CharField(max_length=20, verbose_name=_("Code"))
    nom = models.CharField(max_length=100, verbose_name=_("Nom"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    responsable = models.ForeignKey('Employe', on_delete=models.SET_NULL, blank=True, null=True, 
                                   related_name='departements_diriges', verbose_name=_("Responsable"))
    compte_comptable = models.ForeignKey(PlanComptableOHADA, on_delete=models.SET_NULL, blank=True, null=True, 
                                        verbose_name=_("Compte comptable"))
    actif = models.BooleanField(default=True, verbose_name=_("Actif"))
    
    class Meta:
        unique_together = ['entreprise', 'code']
        verbose_name = _("Département")
        verbose_name_plural = _("Départements")
    
    def __str__(self):
        return f"{self.code} - {self.nom}"

class Poste(models.Model):
    TYPE_CONTRAT_CHOICES = [
        ('CDI', _('CDI')),
        ('CDD', _('CDD')),
        ('STAGE', _('Stage')),
        ('INTERIM', _('Intérim')),
        ('FREELANCE', _('Freelance')),
    ]
    
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    code = models.CharField(max_length=20, verbose_name=_("Code"))
    intitule = models.CharField(max_length=100, verbose_name=_("Intitulé"))
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, verbose_name=_("Département"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    type_contrat = models.CharField(max_length=20, choices=TYPE_CONTRAT_CHOICES, default='CDI', verbose_name=_("Type de contrat"))
    salaire_min = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Salaire minimum"))
    salaire_max = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Salaire maximum"))
    actif = models.BooleanField(default=True, verbose_name=_("Actif"))
    
    class Meta:
        unique_together = ['entreprise', 'code']
        verbose_name = _("Poste")
        verbose_name_plural = _("Postes")
    
    def __str__(self):
        return f"{self.code} - {self.intitule}"

class Employe(models.Model):
    STATUT_CHOICES = [
        ('ACTIF', _('Actif')),
        ('INACTIF', _('Inactif')),
        ('CONGE', _('En congé')),
        ('SUSPENDU', _('Suspendu')),
    ]
    
    GENRE_CHOICES = [
        ('M', _('Masculin')),
        ('F', _('Féminin')),
        ('A', _('Autre')),
    ]
    
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    # CORRECTION: Utilisez settings.AUTH_USER_MODEL au lieu de User
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True, verbose_name=_("Utilisateur"))
    matricule = models.CharField(max_length=20, unique=True, verbose_name=_("Matricule"))
    nom = models.CharField(max_length=100, verbose_name=_("Nom"))
    prenom = models.CharField(max_length=100, verbose_name=_("Prénom"))
    genre = models.CharField(max_length=1, choices=GENRE_CHOICES, verbose_name=_("Genre"))
    date_naissance = models.DateField(verbose_name=_("Date de naissance"))
    email = models.EmailField(verbose_name=_("Email professionnel"))
    telephone = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Téléphone"))
    adresse = models.TextField(verbose_name=_("Adresse"))
    ville = models.CharField(max_length=100, verbose_name=_("Ville"))
    code_postal = models.CharField(max_length=20, verbose_name=_("Code postal"))
    pays = models.CharField(max_length=100, default="France", verbose_name=_("Pays"))
    date_embauche = models.DateField(verbose_name=_("Date d'embauche"))
    poste = models.ForeignKey(Poste, on_delete=models.CASCADE, verbose_name=_("Poste"))
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='ACTIF', verbose_name=_("Statut"))
    photo = models.ImageField(upload_to='employes/photos/', blank=True, null=True, verbose_name=_("Photo"))
    cv = models.FileField(upload_to='employes/cv/', blank=True, null=True, verbose_name=_("CV"))
    carte_employe = models.ImageField(upload_to='cartes_employes/', blank=True, null=True, verbose_name=_("Carte d'employé"))
    
    def generer_carte_employe(self):
        """Génère la carte d'employé avec QR code"""
        # Créer l'image de la carte
        width, height = 800, 450
        background_color = (255, 255, 255)
        card = Image.new('RGB', (width, height), background_color)
        draw = ImageDraw.Draw(card)
        
        try:
            # Charger une police (essayer plusieurs polices)
            try:
                font_large = ImageFont.truetype("arial.ttf", 28)
                font_medium = ImageFont.truetype("arial.ttf", 20)
                font_small = ImageFont.truetype("arial.ttf", 16)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Entête de la carte
            draw.rectangle([(0, 0), (width, 80)], fill=(0, 51, 102))
            draw.text((width//2, 40), self.entreprise.nom, fill=(255, 255, 255), 
                     font=font_large, anchor="mm")
            
            # Photo de l'employé
            if self.photo:
                photo = Image.open(self.photo.path)
                photo = photo.resize((150, 150), Image.LANCZOS)
                # Créer un cadre rond pour la photo
                mask = Image.new('L', (150, 150), 0)
                draw_mask = ImageDraw.Draw(mask)
                draw_mask.ellipse((0, 0, 150, 150), fill=255)
                photo.putalpha(mask)
                card.paste(photo, (50, 100), photo)
            else:
                # Placeholder si pas de photo
                draw.ellipse([(50, 100), (200, 250)], outline=(200, 200, 200), width=2)
                draw.text((125, 175), "Photo", fill=(150, 150, 150), font=font_medium, anchor="mm")
            
            # Informations de l'employé
            y_position = 110
            infos = [
                f"Nom: {self.nom_complet}",
                f"Matricule: {self.matricule}",
                f"Poste: {self.poste.intitule}",
                f"Département: {self.poste.departement.nom}",
                f"Date embauche: {self.date_embauche.strftime('%d/%m/%Y')}"
            ]
            
            for info in infos:
                draw.text((250, y_position), info, fill=(0, 0, 0), font=font_medium)
                y_position += 35
            
            # Générer le QR code
            qr_data = f"""
            EMPLOYE: {self.nom_complet}
            MATRICULE: {self.matricule}
            POSTE: {self.poste.intitule}
            DEPARTEMENT: {self.poste.departement.nom}
            ENTREPRISE: {self.entreprise.nom}
            DATE EMBAUCHE: {self.date_embauche.strftime('%d/%m/%Y')}
            """
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=4,
                border=2,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_img = qr_img.resize((120, 120), Image.LANCZOS)
            
            # Positionner le QR code
            card.paste(qr_img, (width - 150, height - 140))
            draw.text((width - 90, height - 15), "Scan me", fill=(100, 100, 100), font=font_small, anchor="mm")
            
            # Sauvegarder l'image
            buffer = BytesIO()
            card.save(buffer, format='PNG', quality=95)
            
            # Sauvegarder dans le champ carte_employe
            if self.carte_employe:
                # Supprimer l'ancienne carte
                old_path = self.carte_employe.path
                if os.path.exists(old_path):
                    os.remove(old_path)
            
            self.carte_employe.save(
                f'carte_employe_{self.matricule}.png',
                File(buffer),
                save=False
            )
            
            return True
            
        except Exception as e:
            print(f"Erreur génération carte: {e}")
            return False
    
    def save(self, *args, **kwargs):
        # Générer automatiquement la carte si c'est une nouvelle création
        is_new = self._state.adding
        super().save(*args, **kwargs)
        
        if is_new or not self.carte_employe:
            self.generer_carte_employe()
            super().save(update_fields=['carte_employe'])
    
    class Meta:
        verbose_name = _("Employé")
        verbose_name_plural = _("Employés")
    
    def __str__(self):
        return f"{self.matricule} - {self.nom} {self.prenom}"
    
    @property
    def nom_complet(self):
        return f"{self.nom} {self.prenom}"
    
    def anciennete(self):
        from datetime import date
        if self.date_embauche:
            return (date.today() - self.date_embauche).days // 365
        return 0
    
    def get_contrat_actuel(self):
        """Retourne le contrat actuel de l'employé"""
        return self.contrat_set.filter(statut='EN_COURS').first()

# ... Le reste de vos modèles (Contrat, BulletinPaie, LigneBulletinPaie, Conge) reste inchangé ...

class Contrat(models.Model):
    STATUT_CHOICES = [
        ('EN_COURS', _('En cours')),
        ('TERMINE', _('Terminé')),
        ('RESILIE', _('Résilié')),
    ]
    
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, verbose_name=_("Employé"))
    reference = models.CharField(max_length=50, verbose_name=_("Référence"))
    type_contrat = models.CharField(max_length=20, choices=Poste.TYPE_CONTRAT_CHOICES, verbose_name=_("Type de contrat"))
    date_debut = models.DateField(verbose_name=_("Date de début"))
    date_fin = models.DateField(blank=True, null=True, verbose_name=_("Date de fin"))
    poste = models.ForeignKey(Poste, on_delete=models.CASCADE, verbose_name=_("Poste"))
    salaire_base = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Salaire de base"))
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_COURS', verbose_name=_("Statut"))
    duree_essai = models.IntegerField(blank=True, null=True, verbose_name=_("Durée d'essai (jours)"))
    date_fin_essai = models.DateField(blank=True, null=True, verbose_name=_("Date de fin de période d'essai"))
    heures_semaine = models.IntegerField(default=35, verbose_name=_("Heures par semaine"))
    jours_conges_an = models.IntegerField(default=25, verbose_name=_("Jours de congés par an"))
    fichier_contrat = models.FileField(upload_to='contrats/', blank=True, null=True, verbose_name=_("Fichier du contrat"))
    
    class Meta:
        verbose_name = _("Contrat")
        verbose_name_plural = _("Contrats")
   
    
    def __str__(self):
        return f"{self.reference} - {self.employe.nom_complet}"

class BulletinPaie(models.Model):
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, verbose_name=_("Employé"))
    contrat = models.ForeignKey(Contrat, on_delete=models.CASCADE, verbose_name=_("Contrat"))
    periode = models.CharField(max_length=7, verbose_name=_("Période (YYYY-MM)"))
    date_edition = models.DateField(auto_now_add=True, verbose_name=_("Date d'édition"))
    salaire_brut = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Salaire brut"))
    total_cotisations = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Total cotisations"))
    salaire_net = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Salaire net"))
    net_a_payer = models.DecimalField(max_digits=12, decimal_places=2, verbose_name=_("Net à payer"))
    jours_travailles = models.IntegerField(verbose_name=_("Jours travaillés"))
    heures_travaillees = models.DecimalField(max_digits=5, decimal_places=2, verbose_name=_("Heures travaillées"))
    fichier_bulletin = models.FileField(upload_to='bulletins/', blank=True, null=True, verbose_name=_("Fichier bulletin"))
    
    class Meta:
        unique_together = ['employe', 'periode']
        verbose_name = _("Bulletin de paie")
        verbose_name_plural = _("Bulletins de paie")
    
    def __str__(self):
        
        return f"Bulletin {self.periode} - {self.employe.nom_complet}"
    def save(self, *args, **kwargs):
        """Override save pour générer automatiquement le PDF"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Générer le PDF après la création
        if is_new and not self.fichier_bulletin:
            from .utils import BulletinPaiePDFGenerator
            BulletinPaiePDFGenerator.save_bulletin_pdf(self)
    
    
class Presence(models.Model):
    STATUT_CHOICES = [
        ('PRESENT', _('Présent')),
        ('ABSENT', _('Absent')),
        ('CONGE', _('Congé')),
        ('MALADIE', _('Maladie')),
        ('AUTRE', _('Autre')),
    ]
    
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, verbose_name=_("Employé"))
    date = models.DateField(verbose_name=_("Date"))
    heure_arrivee = models.TimeField(blank=True, null=True, verbose_name=_("Heure d'arrivée"))
    heure_depart = models.TimeField(blank=True, null=True, verbose_name=_("Heure de départ"))
    heures_travaillees = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name=_("Heures travaillées"))
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='PRESENT', verbose_name=_("Statut"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    
    class Meta:
        unique_together = ['employe', 'date']
        verbose_name = _("Présence")
        verbose_name_plural = _("Présences")
    
    def __str__(self):
        return f"{self.employe.nom_complet} - {self.date}"
    
    def save(self, *args, **kwargs):
        # Calcul automatique des heures travaillées
        if self.heure_arrivee and self.heure_depart and self.statut == 'PRESENT':
            arrivee = datetime.combine(self.date, self.heure_arrivee)
            depart = datetime.combine(self.date, self.heure_depart)
            duree = depart - arrivee
            self.heures_travaillees = round(duree.total_seconds() / 3600, 2)
        super().save(*args, **kwargs)   
    
    
    
    

class LigneBulletinPaie(models.Model):
    TYPE_LIGNE_CHOICES = [
        ('GAINS', _('Gains')),
        ('RETENUES', _('Retenues')),
    ]
    
    bulletin = models.ForeignKey(BulletinPaie, on_delete=models.CASCADE, related_name='lignes', verbose_name=_("Bulletin"))
    type_ligne = models.CharField(max_length=10, choices=TYPE_LIGNE_CHOICES, verbose_name=_("Type de ligne"))
    libelle = models.CharField(max_length=100, verbose_name=_("Libellé"))
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Montant"))
    ordre = models.IntegerField(default=0, verbose_name=_("Ordre d'affichage"))
    
    class Meta:
        verbose_name = _("Ligne de bulletin de paie")
        verbose_name_plural = _("Lignes de bulletin de paie")
        ordering = ['ordre']
    
    def __str__(self):
        return f"{self.libelle} - {self.montant}"

class Conge(models.Model):
    TYPE_CONGE_CHOICES = [
        ('ANNUEL', _('Congé annuel')),
        ('MALADIE', _('Congé maladie')),
        ('MATERNITE', _('Congé maternité')),
        ('PATERNITE', _('Congé paternité')),
        ('SANS_SOLDE', _('Congé sans solde')),
        ('EXCEPTIONNEL', _('Congé exceptionnel')),
    ]
    
    STATUT_CHOICES = [
        ('DEMANDE', _('Demandé')),
        ('VALIDE', _('Validé')),
        ('REJETE', _('Rejeté')),
        ('ANNULE', _('Annulé')),
    ]
    
    entreprise = models.ForeignKey(Entreprise, on_delete=models.CASCADE, verbose_name=_("Entreprise"))
    employe = models.ForeignKey(Employe, on_delete=models.CASCADE, verbose_name=_("Employé"))
    type_conge = models.CharField(max_length=20, choices=TYPE_CONGE_CHOICES, verbose_name=_("Type de congé"))
    date_debut = models.DateField(verbose_name=_("Date de début"))
    date_fin = models.DateField(verbose_name=_("Date de fin"))
    nombre_jours = models.IntegerField(verbose_name=_("Nombre de jours"))
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='DEMANDE', verbose_name=_("Statut"))
    motif = models.TextField(blank=True, null=True, verbose_name=_("Motif"))
    date_demande = models.DateTimeField(auto_now_add=True, verbose_name=_("Date de demande"))
    date_validation = models.DateTimeField(blank=True, null=True, verbose_name=_("Date de validation"))
    valide_par = models.ForeignKey(Employe, on_delete=models.SET_NULL, blank=True, null=True, 
                                  related_name='conges_valides', verbose_name=_("Validé par"))
    
    class Meta:
        verbose_name = _("Congé")
        verbose_name_plural = _("Congés")
     
    
    def __str__(self):
        return f"{self.employe.nom_complet} - {self.type_conge} ({self.date_debut} au {self.date_fin})"