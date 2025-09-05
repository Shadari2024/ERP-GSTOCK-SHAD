from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

from django.db.models import Sum, Count
from django.utils import timezone
from .models import *

def envoyer_mail_bienvenue(client):
    subject = f"Bienvenue {client.nom} chez Obed service"
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = client.email

    # Contexte pour le template HTML
    context = {
        'nom': client.nom,
        'email': client.email,
    }

    html_content = render_to_string('emails/bienvenue.html', context)

    msg = EmailMultiAlternatives(subject, '', from_email, [to_email])
    msg.attach_alternative(html_content, "text/html")
    msg.send()



from django.db.models import Sum, Count
from django.utils import timezone

def bilan_caisse_du_jour(vendeur):
    today = timezone.now().date()
    commandes = Commande.objects.filter(
        vente_au_comptoir=True,
        vente_confirmee=True,
        vendeur=vendeur,
        date_commande__date=today
    )

    total = commandes.aggregate(Sum("montant_total"))["montant_total__sum"] or 0
    nb_commandes = commandes.count()

    return {
        
        "total": total,
        "nb_commandes": nb_commandes,
        "commandes": commandes
    }



from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def generer_pdf_facture(facture):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []

    styles = getSampleStyleSheet()
    story.append(Paragraph(f"Facture n°{facture.numero}", styles['Title']))
    
    # Ajouter les détails de la facture
    data = [
        ["Désignation", "Quantité", "Prix unitaire", "Total HT"],
        *[[l.produit.nom, l.quantite, l.prix_unitaire, l.total_ligne_ht()] 
          for l in facture.commande.lignes.all()],
        ["TVA", "", "", f"{facture.commande.total_tva()}€"],
        ["Total TTC", "", "", f"{facture.montant_total}€"]
    ]
    
    # Sauvegarde du PDF
    filename = f"facture_{facture.numero}.pdf"
    facture.pdf.save(filename, ContentFile(buffer.getvalue()))
    buffer.close()