# ventes/utils.py
import os
from io import BytesIO
from django.template.loader import get_template
from django.core.mail import EmailMessage # Cet import est conservé au cas où, mais n'est pas utilisé directement ici.
from django.conf import settings # Cet import est conservé au cas où, mais n'est pas utilisé directement ici.
from xhtml2pdf import pisa
import logging

# Important : Assurez-vous d'avoir ces imports si d'autres parties de utils.py les utilisent.
# Pour le cas spécifique de render_to_pdf, ils ne sont pas nécessaires.
# from parametres.models import ConfigurationSAAS, Devise 

logger = logging.getLogger(__name__)

def render_to_pdf(template_src, context_dict={}):
    """
    Convertit un template Django en PDF.
    Gère les erreurs de génération de PDF et les loggue.
    """
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    
    try:
        # pisa.CreatePDF est la fonction moderne et robuste pour générer le PDF
        pdf = pisa.CreatePDF(BytesIO(html.encode("UTF-8")), dest=result)
        if not pdf.err:
            return result.getvalue()
        # Si pisa rapporte une erreur, nous la logguons
        logger.error(f"Erreur de génération PDF par pisa pour le template '{template_src}': {pdf.err}")
    except Exception as e:
        # Capture toutes les autres exceptions qui pourraient survenir pendant la génération du PDF
        logger.error(f"La génération du PDF a échoué de manière inattendue pour le template '{template_src}': {str(e)}", exc_info=True)
    
    return None

# La fonction send_devis_email a été déplacée dans ventes/views.py comme une méthode de la vue.
# Elle n'est donc plus nécessaire ici, sauf si d'autres parties de votre application l'appellent directement.

# ventes/utils.py
# ventes/utils.py

from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from io import BytesIO
from weasyprint import HTML
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)

# Make sure this import matches where your Commande model is defined
# Assuming it's in ventes.models or somewhere accessible
from ventes.models import Commande # Adjust this if Commande is elsewhere
from parametres.models import ConfigurationSAAS, Devise # Required for CommandePrintView context

def send_commande_pdf_email(commande, recipient_email):
    try:
        # 1. Préparer le contexte pour le template PDF
        # Pour obtenir le contexte nécessaire à CommandePrintView, nous recréons une partie de sa logique.
        # Il est crucial que le contexte pour 'print.html' soit complet.
        
        # --- Start of context generation (mimicking CommandePrintView) ---
        context = {}
        entreprise = commande.entreprise # Get the entreprise from the commande
        
        devise_principale_symbole = ''
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            if config_saas.devise_principale:
                devise_principale_symbole = config_saas.devise_principale.symbole
        except (ConfigurationSAAS.DoesNotExist, Devise.DoesNotExist):
            logger.warning(f"ConfigurationSAAS ou Devise principale non trouvée pour l'entreprise {entreprise.nom}")

        context['devise_principale_symbole'] = devise_principale_symbole
        context['entreprise_info'] = entreprise
        context['now'] = timezone.now() # Don't forget to import timezone at the top of this file
        context['commande'] = commande # Pass the commande object itself
        context['created_by_user'] = commande.created_by.username if commande.created_by else 'N/A'
        # --- End of context generation ---


        # 2. Rendre le template HTML du bon de commande (print.html)
        html_string = render_to_string('ventes/commandes/print.html', context)

        # 3. Générer le PDF à partir du HTML
        pdf_file = BytesIO()
        # Ensure settings.WEASYPRINT_BASEURL is configured correctly, e.g., 'file://' or a static URL
        HTML(string=html_string, base_url=settings.WEASYPRINT_BASEURL).write_pdf(pdf_file)
        pdf_file.seek(0)

        # 4. Préparer l'email
        subject = f"Votre Bon de Commande #{commande.numero} de {commande.entreprise.nom}"
        
        email_body = render_to_string('emails/commande_email_body.txt', {
            'commande': commande,
            'entreprise_info': commande.entreprise,
            'client': commande.client,
            'base_url': settings.SITE_URL,
        })

        email = EmailMessage(
            subject,
            email_body,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
        )
        email.attach(f"Bon_de_Commande_{commande.numero}.pdf", pdf_file.read(), 'application/pdf')

        # 5. Envoyer l'email
        email.send(fail_silently=False)
        logger.info(f"Bon de commande #{commande.numero} envoyé à {recipient_email}")
        return True

    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email pour la commande #{commande.numero}: {e}", exc_info=True)
        return False
    
    
    
    
    # ventes/utils.py
# ventes/utils.py

from django.db import transaction
from django.utils import timezone
import logging
import random
import string
import decimal # Don't forget to import decimal if you're working with DecimalFields

# Ensure these imports match your actual model locations
# Assuming Devis, LigneDevis, Commande, LigneCommande are in ventes.models
from ventes.models import *

from STOCK.models import *

# You might still need these if used in Commande, Devis, or their items
# from STOCK.Client import Client
# from STOCK.Produit import Produit # Assuming your Product model is named Produit and in STOCK.Produit
# from parametres.models import Entreprise # Assuming Entreprise is here

logger = logging.getLogger(__name__)

# (Your existing send_commande_pdf_email function)
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
import re

def convert_devis_to_commande(devis_id, user):
    """
    Convertit un devis en commande en utilisant le related_name 'items'
    """
    try:
        with transaction.atomic():
            # Récupérer le devis avec les lignes (items)
            devis = Devis.objects.select_related(
                'client', 'entreprise', 'created_by'
            ).prefetch_related(
                'items'
            ).get(pk=devis_id)

            # Vérifications préalables
            if not can_convert_devis(devis):
                error_msg = get_conversion_error_message(devis)
                return None, error_msg

            # Générer le numéro de commande
            commande_numero = generate_commande_number(devis.entreprise)
            
            # Créer la commande
            new_commande = create_commande_from_devis(devis, commande_numero, user)
            
            # Copier les lignes du devis (items) vers la commande (items)
            lignes_copied = copy_items_to_commande(devis, new_commande)
            if not lignes_copied:
                return None, "Aucune ligne à copier"

            # Recalculer les totaux de la commande
            new_commande.calculer_totaux()
            new_commande.save()

            # Mettre à jour le statut du devis
            update_devis_status(devis, 'facture', user, new_commande.numero)
            
            return new_commande, None

    except Devis.DoesNotExist:
        return None, "Devis non trouvé"
        
    except Exception as e:
        return None, f"Erreur lors de la conversion: {str(e)}"


def can_convert_devis(devis):
    """
    Vérifie si le devis peut être converti en commande
    """
    if not devis:
        return False
        
    allowed_statuses = ['brouillon', 'envoye', 'accepte']
    blocked_statuses = ['refuse', 'annule', 'facture', 'converti']
    
    return (devis.statut in allowed_statuses and 
            devis.statut not in blocked_statuses)


def get_conversion_error_message(devis):
    """
    Retourne un message d'erreur approprié selon le statut du devis
    """
    status_messages = {
        'facture': f"Le devis #{devis.numero} a déjà été facturé.",
        'converti': f"Le devis #{devis.numero} a déjà été converti.",
        'refuse': f"Le devis #{devis.numero} est refusé.",
        'annule': f"Le devis #{devis.numero} est annulé.",
    }
    
    return status_messages.get(devis.statut, 
        f"Le statut '{devis.get_statut_display()}' ne permet pas la conversion.")


def generate_commande_number(entreprise):
    """
    Génère un numéro de commande unique basé sur le nom de l'entreprise
    """
    from datetime import date
    
    today = date.today()
    year = today.year
    
    # Créer un préfixe à partir du nom de l'entreprise
    if entreprise.nom:
        # Prendre les 3 premières lettres du nom
        prefix = ''.join([word[0].upper() for word in entreprise.nom.split()[:3] if word])
        # CORRECTION SYNTAXE REGEX
        prefix = re.sub(r'[^A-Z]', '', prefix)[:3] or 'CMD'
    else:
        prefix = 'CMD'
    
    # Trouver le dernier numéro de commande de l'année
    last_commande = Commande.objects.filter(
        entreprise=entreprise,
        date__year=year
    ).order_by('-numero').first()
    
    if last_commande and last_commande.numero:
        try:
            parts = last_commande.numero.split('-')
            if len(parts) >= 2:
                last_number = extract_last_number(parts)
                new_number = last_number + 1
            else:
                new_number = 1
        except (ValueError, IndexError, AttributeError):
            new_number = 1
    else:
        new_number = 1
    
    return f"{prefix}-{year}-{new_number:04d}"


def extract_last_number(parts):
    """
    Extrait le dernier nombre d'une liste de parties de numéro
    """
    for part in reversed(parts):
        if part.isdigit():
            return int(part)
    return 1


def create_commande_from_devis(devis, numero, user):
    """
    Crée une nouvelle commande à partir d'un devis
    """
    return Commande.objects.create(
        entreprise=devis.entreprise,
        client=devis.client,
        date=timezone.now().date(),
        devis=devis,
        numero=numero,
        total_ht=devis.total_ht or Decimal('0.00'),
        total_tva=devis.total_tva or Decimal('0.00'),
        total_ttc=devis.total_ttc or Decimal('0.00'),
        notes=build_commande_notes(devis),
        statut='brouillon',
        created_by=user,
    )


def build_commande_notes(devis):
    """
    Construit les notes de la commande à partir du devis
    """
    base_note = f"Commande générée à partir du devis #{devis.numero}"
    if devis.notes:
        return f"{base_note}\n\nNotes du devis:\n{devis.notes}"
    return base_note


def copy_items_to_commande(devis, commande):
    """
    Copie les items du devis vers les items de la commande
    """
    items_devis = devis.items.all()
    
    if not items_devis.exists():
        return False
    
    for devis_item in items_devis:
        LigneCommande.objects.create(
            commande=commande,
            produit=devis_item.produit,
            quantite=devis_item.quantite,
            prix_unitaire=devis_item.prix_unitaire,
            taux_tva=devis_item.taux_tva,
            montant_ht=devis_item.montant_ht or Decimal('0.00'),
            montant_tva=devis_item.montant_tva or Decimal('0.00'),
        )
    
    return True


def update_devis_status(devis, new_status, user, commande_numero):
    """
    Met à jour le statut du devis
    """
    old_status = devis.statut
    devis.statut = new_status
    devis.save(update_fields=['statut', 'updated_at'])
    
    # Historique du statut (si votre modèle existe)
    try:
        DevisStatutHistory.objects.create(
            devis=devis,
            ancien_statut=old_status,
            nouveau_statut=new_status,
            changed_by=user,
            commentaire=f"Converti en commande #{commande_numero}"
        )
    except:
        pass
    
    
    
    
    
def convert_commande_to_bon_livraison(commande_id, user):
    """
    Convertit une commande confirmée en bon de livraison avec toutes les lignes de produits
    """
    try:
        with transaction.atomic():
            # Récupérer la commande avec les items
            commande = Commande.objects.select_related(
                'client', 'entreprise', 'created_by'
            ).prefetch_related(
                'items'
            ).get(pk=commande_id)

            # Vérifications préalables
            if not can_convert_commande(commande):
                error_msg = get_commande_conversion_error_message(commande)
                return None, error_msg

            # Générer le numéro de bon de livraison
            bon_livraison_numero = generate_bon_livraison_number(commande.entreprise)
            
            # Créer le bon de livraison
            new_bon_livraison = create_bon_livraison_from_commande(commande, bon_livraison_numero, user)
            
            # Copier les items de la commande vers le bon de livraison
            lignes_copied = copy_items_to_bon_livraison(commande, new_bon_livraison)
            if not lignes_copied:
                return None, "Aucune ligne à copier"

            # Mettre à jour les totaux du bon de livraison
            new_bon_livraison.update_totals()
            new_bon_livraison.save()

            # Mettre à jour le statut de la commande
            update_commande_status(commande, 'livre', user, new_bon_livraison.numero)
            
            # Mettre à jour le stock (sortie de stock)
            update_stock_on_delivery(new_bon_livraison.items.all(), user, action_type='out')
            
            return new_bon_livraison, None

    except Commande.DoesNotExist:
        return None, "Commande non trouvée"
        
    except Exception as e:
        return None, f"Erreur lors de la conversion: {str(e)}"


def can_convert_commande(commande):
    """
    Vérifie si la commande peut être convertie en bon de livraison
    """
    if not commande:
        return False
        
    # Statuts qui permettent la conversion
    allowed_statuses = ['Confirmee', 'en_preparation']
    
    # Statuts qui bloquent la conversion
    blocked_statuses = ['brouillon', 'annule', 'livre', 'retour']
    
    return (commande.statut in allowed_statuses and 
            commande.statut not in blocked_statuses)


def get_commande_conversion_error_message(commande):
    """
    Retourne un message d'erreur approprié selon le statut de la commande
    """
    status_messages = {
        'livre': f"La commande #{commande.numero} a déjà été livrée.",
        'annule': f"La commande #{commande.numero} est annulée.",
        'brouillon': f"La commande #{commande.numero} est un brouillon.",
        'retour': f"La commande #{commande.numero} a été retournée.",
    }
    
    return status_messages.get(commande.statut, 
        f"Le statut '{commande.get_statut_display()}' ne permet pas la conversion en bon de livraison.")


def generate_bon_livraison_number(entreprise):
    """
    Génère un numéro de bon de livraison unique en utilisant la même logique que le modèle
    """
    from datetime import date
    
    today = date.today()
    prefix = f"BL-{today.year}-"
    
    # Utiliser la même logique que la méthode generate_bl_number du modèle
    last_bl = BonLivraison.objects.filter(
        entreprise=entreprise,
        numero__startswith=prefix
    ).order_by('-numero').first()
    
    if last_bl and last_bl.numero:
        try:
            num_part = int(last_bl.numero.split('-')[-1])
            next_num = num_part + 1
        except (ValueError, IndexError):
            next_num = 1
    else:
        next_num = 1
    
    return f"{prefix}{next_num:04d}"


def create_bon_livraison_from_commande(commande, numero, user):
    """
    Crée un nouveau bon de livraison à partir d'une commande
    Basé sur la structure exacte de votre modèle BonLivraison
    """
    return BonLivraison.objects.create(
        entreprise=commande.entreprise,
        commande=commande,  # Champ essentiel pour la relation
        date=timezone.now().date(),
        numero=numero,
        total_ht=commande.total_ht or Decimal('0.00'),
        total_tva=commande.total_tva or Decimal('0.00'),
        total_ttc=commande.total_ttc or Decimal('0.00'),
        notes=build_bon_livraison_notes(commande),
        statut='prepare',  # Statut initial 'prepare' comme défini dans votre modèle
        created_by=user,
    )


def build_bon_livraison_notes(commande):
    """
    Construit les notes du bon de livraison à partir de la commande
    """
    base_note = f"Bon de livraison généré à partir de la commande #{commande.numero}"
    if commande.notes:
        return f"{base_note}\n\nNotes de la commande:\n{commande.notes}"
    return base_note


def copy_items_to_bon_livraison(commande, bon_livraison):
    """
    Copie les items de la commande vers le bon de livraison
    Utilise le related_name 'items' pour les deux modèles
    """
    items_commande = commande.items.all()
    
    if not items_commande.exists():
        return False
    
    for commande_item in items_commande:
        LigneBonLivraison.objects.create(
            bon_livraison=bon_livraison,
            produit=commande_item.produit,
            quantite=commande_item.quantite,
            prix_unitaire=commande_item.prix_unitaire,
            taux_tva=commande_item.taux_tva,
            montant_ht=commande_item.montant_ht or Decimal('0.00'),
            montant_tva=commande_item.montant_tva or Decimal('0.00'),
        )
    
    return True


def update_commande_status(commande, new_status, user, bon_livraison_numero):
    """
    Met à jour le statut de la commande
    """
    old_status = commande.statut
    commande.statut = new_status
    commande.save(update_fields=['statut', 'updated_at'])
    
    # Historique du statut
    try:
        CommandeStatutHistory.objects.create(
            commande=commande,
            ancien_statut=old_status,
            nouveau_statut=new_status,
            changed_by=user,
            commentaire=f"Converti en bon de livraison #{bon_livraison_numero}"
        )
    except:
        pass


def update_stock_on_delivery(lignes_bon_livraison, user, action_type='out'):
    """
    Met à jour le stock après livraison
    """
    for ligne in lignes_bon_livraison:
        try:
            produit = ligne.produit
            quantite = ligne.quantite
            
            if action_type == 'out':
                # Sortie de stock
                produit.stock -= quantite
            elif action_type == 'in':
                # Entrée de stock (retour)
                produit.stock += quantite
            
            produit.save()
            
            # Log de mouvement de stock
            MouvementStock.objects.create(
                produit=produit,
                quantite=quantite,
                type_mouvement='sortie' if action_type == 'out' else 'entree',
                reference=f"BL-{ligne.bon_livraison.numero}",
                created_by=user,
                entreprise=user.entreprise
            )
            
        except Exception as e:
            # Continuer avec les autres produits même en cas d'erreur sur un
            continue
