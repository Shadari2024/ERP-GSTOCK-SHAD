from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Sum
from parametres.mixins import EntrepriseAccessMixin
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DetailView, DeleteView
from django.db.models import ProtectedError
from django.shortcuts import redirect
from django.contrib import messages
import logging
import io
from decimal import Decimal
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from django.db.models import ProtectedError # For the supplier deletion view
from django.urls import reverse_lazy # For the supplier deletion view

import os

from django.contrib.staticfiles import finders

from django.views.generic import TemplateView
from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce, TruncMonth, TruncWeek
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models.deletion import ProtectedError
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.db.models import F
from django.http import HttpResponse # Pour renvoyer des fichiers
import openpyxl # Pour l'exportation Excel
from reportlab.pdfgen import canvas # Pour l'exportation PDF (exemple simple)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from django.views.generic import FormView 
from django.forms import inlineformset_factory 
from .models import *
from .forms import *
from django.views.generic import View
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.db.models import Count, Sum, Q
import pandas as pd
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import IntegrityError, transaction
from django.http import HttpResponse
# --- Nouveaux imports nécessaires pour la génération PDF via HTML ---
from django.template.loader import get_template # Pour charger les templates Django
from weasyprint import HTML, CSS # <-- C'EST ÇA QUI MANQUAIT 
from django.views.generic import ListView, CreateView, DetailView
from django.contrib import messages
from django.urls import reverse_lazy
from parametres.mixins import EntrepriseAccessMixin
from .models import BonReception, CommandeAchat, LigneBonReception
from .forms import *
# Pour PDF
from io import BytesIO
from xhtml2pdf import pisa
from django.template.loader import get_template

# from chemin.vers.EntrepriseAccessMixin import EntrepriseAccessMixin # N'oublie pas d'importer ta mixin
import io
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from xhtml2pdf import pisa
import logging
from django.db import transaction 
# achats/views.py

from django.views.generic import ListView
from django.db.models import Q # Make sure Q is imported for complex queries
from django.db.models import Sum # Keep Sum if used for aggregation, not directly needed here
# Your existing imports:
# from .models import CommandeAchat, Fournisseur, Entreprise # Ensure all relevant models are imported
# from chemin.vers.EntrepriseAccessMixin import EntrepriseAccessMixin
# from parametres.models import Devise, ConfigurationSAAS # Import if you need to filter explicitly, but the property handles it

# achats/views.py

from django.views.generic import ListView
from django.db.models import Q # Pour les requêtes complexes comme les recherches
from django.contrib import messages # Pour afficher des messages à l'utilisateur
from datetime import datetime # Pour gérer les filtres de date
# achats/views.py

# --- Nouveaux imports nécessaires pour l'exportation ---
from django.http import HttpResponse # Pour renvoyer des fichiers HTTP
import openpyxl # Pour la génération de fichiers Excel
from reportlab.pdfgen import canvas # Pour la génération de PDF
from reportlab.lib.pagesizes import A4 # Pour définir la taille de la page PDF
from reportlab.lib import colors # Pour les couleurs dans le PDF
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph # Composants pour la mise en page PDF
from reportlab.lib.styles import getSampleStyleSheet # Pour les styles de texte dans le PDF
from reportlab.lib.units import inch # Pour les unités de mesure dans le PDF

# --- Assure-toi que ces imports sont aussi présents et corrects ---
from django.views.generic import ListView, CreateView, DetailView, UpdateView # Ajoute DetailView et UpdateView si tu les utilises
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib import messages
from datetime import datetime
from django.forms import inlineformset_factory



# --- Tes formulaires (doivent être définis avant les vues qui les utilisent) ---
# Copie-colle tes formulaires CommandeAchatForm et LigneCommandeAchatForm ici
# et ton LigneCommandeAchatFormSet
# ... (Tes classes CommandeAchatForm, LigneCommandeAchatForm, LigneCommandeAchatFormSet) ...


# --- EXPORT FUNCTIONS ---

def exporter_commandes_excel(request, pk=None):
    """
    Exporte une commande spécifique (si pk est fourni) ou toutes les commandes filtrées
    (si pk est None) au format Excel.
    """
    # Ensure request.entreprise is available (e.g., via a middleware or a custom mixin)
    if not hasattr(request, 'entreprise') or not request.entreprise:
        messages.error(request, "Impossible d'exporter. Les informations de l'entreprise sont manquantes.")
        return HttpResponse("Informations de l'entreprise manquantes.", status=400)


    if pk: # Cas d'exportation d'une commande unique
        commandes = CommandeAchat.objects.filter(pk=pk, entreprise=request.entreprise)
        filename = f"commande_achat_{pk}.xlsx"
    else: # Cas d'exportation de toutes les commandes (avec les filtres appliqués sur la liste)
        # On recrée l'instance de la vue pour réutiliser sa logique de get_queryset
        view = ListeCommandesView()
        view.request = request
        view.args = ()
        view.kwargs = {}
        commandes = view.get_queryset() # Récupère le queryset déjà filtré de la vue liste
        filename = "commandes_achats_filtrees.xlsx"

    if not commandes.exists():
        messages.warning(request, "Aucune commande trouvée pour l'exportation avec les critères spécifiés.")
        return HttpResponse("Aucune commande trouvée pour l'exportation.", status=404)

    # Création de la réponse HTTP avec le type de contenu Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Commandes d'Achat"

    # En-têtes des colonnes pour la feuille Excel
    headers = [
        "N° Commande", "Date Commande", "Date Livraison Prévue", "Statut",
        "Fournisseur", "Montant Total (TTC)", "Devise", "Créée par", "Date Création", "Notes"
    ]
    sheet.append(headers)

    # Remplir le fichier Excel avec les données des commandes
    for cmd in commandes:
        # Assure-toi que commande.devise est accessible (il est une propriété maintenant)
        # et que cmd.devise.code est la propriété pour le code de la devise.
        # Devise est une propriété sur CommandeAchat, qui retourne un objet Devise.
        # Donc, on accède à son attribut 'code'
        devise_code = cmd.devise.code if cmd.devise else "N/A"

        sheet.append([
            cmd.numero_commande,
            cmd.date_commande.strftime("%d/%m/%Y") if cmd.date_commande else '',
            cmd.date_livraison_prevue.strftime("%d/%m/%Y") if cmd.date_livraison_prevue else '',
            cmd.get_statut_display(),
            cmd.fournisseur.nom,
            float(cmd.total_ttc), # Utilisez total_ttc ici
            devise_code,
            cmd.created_by.get_full_name() if cmd.created_by else (cmd.created_by.username if cmd.created_by else ""),
            cmd.created_at.strftime("%d/%m/%Y %H:%M") if cmd.created_at else '',
            cmd.notes
        ])

        # Ajouter les lignes de commande sous chaque commande principale
        if cmd.lignes.exists():
            sheet.append(["", "", "", "", "", "--- Détails Lignes de Commande ---"]) # Adjusted for new headers
            sheet.append(["", "Produit", "Code Produit", "Quantité", "Prix Unitaire", "Remise (%)", "Taux TVA (%)", "Total HT Ligne", "Montant TVA Ligne", "Total TTC Ligne"])
            for ligne in cmd.lignes.all():
                sheet.append([
                    "", # Colonne vide pour l'indentation visuelle
                    ligne.produit.nom,
                    ligne.produit.code if hasattr(ligne.produit, 'code') else 'N/A', # Assuming 'code' is the attribute on Produit
                    float(ligne.quantite),
                    float(ligne.prix_unitaire),
                    float(ligne.remise),
                    float(ligne.taux_tva), # Include taux_tva
                    float(ligne.total_ht_ligne), # Use total_ht_ligne
                    float(ligne.montant_tva_ligne), # Use montant_tva_ligne (calculated in model save)
                    float(ligne.total_ttc_ligne) # Use total_ttc_ligne
                ])
            sheet.append([]) # Ligne vide pour séparer clairement les commandes dans le fichier Excel

    workbook.save(response) # Sauvegarder le classeur dans la réponse HTTP
    messages.success(request, f"Exportation Excel '{filename}' réussie.")
    return response

def exporter_commande_pdf(request, pk):
    try:
        commande = CommandeAchat.objects.select_related(
            'fournisseur',
            'created_by',
            'entreprise__config_saas__devise_principale'
        ).prefetch_related('lignes__produit').get(pk=pk, entreprise=request.entreprise)
    except CommandeAchat.DoesNotExist:
        messages.error(request, "Commande introuvable ou vous n'avez pas la permission d'y accéder.")
        return HttpResponse("Commande introuvable.", status=404)

    context = {
        'commande': commande,
        'now': datetime.now(),
        'entreprise': request.entreprise,
        'is_invoice': True, # Set to True for invoice, False for purchase order. Adjust as needed.
    }

    template_path = 'achats/commandes/commande_pdf_template.html' # <--- Make sure this path is correct
    html_content = get_template(template_path).render(context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="facture_{commande.numero_commande}.pdf"'

    HTML(string=html_content, base_url=request.build_absolute_uri()).write_pdf(response,
        stylesheets=[
            CSS(string='''
                /* Basic print styles included directly in the Python function for convenience */
                @page { size: A4; margin: 2cm; }
                body { font-family: Arial, sans-serif; font-size: 10pt; }
            ''')
        ]
    )
    messages.success(request, f"Exportation PDF de la facture '{commande.numero_commande}' réussie.")
    return response
# achats/views.py

# ... (tes imports) ...
from parametres.models import ConfigurationSAAS, Devise # Assure-toi que ces imports sont là

class ListeCommandesView(EntrepriseAccessMixin, ListView):
    model = CommandeAchat
    template_name = 'achats/commandes/liste.html'
    context_object_name = 'commandes'
    paginate_by = 5  # C'est ici que vous activez la pagination

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            entreprise=self.request.entreprise
        )
        
        queryset = queryset.select_related(
            'fournisseur',
            'created_by',
            'entreprise__config_saas__devise_principale' 
        ).prefetch_related(
            'lignes'
        )

        # Agrégation des totaux HT et TVA
        queryset = queryset.annotate(
            total_ht_agrege = Sum(
                F('lignes__quantite') * F('lignes__prix_unitaire') * (Decimal('1') - F('lignes__remise') / Decimal('100')),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            ),
            total_tva_agrege = Sum(
                'lignes__montant_tva_ligne',
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )
        
        # --- NOUVELLE ANNOTATION POUR LE TOTAL TTC ---
        # Calcule le montant total TTC directement dans la requête
        queryset = queryset.annotate(
            montant_total_ttc=F('total_ht_agrege') + F('total_tva_agrege')
        )
        # --- FIN NOUVELLE ANNOTATION ---

        queryset = queryset.order_by('-date_commande', '-created_at')

        # --- Logique de filtrage existante (pas de changement) ---
        statut = self.request.GET.get('statut')
        if statut and statut != 'all':
            queryset = queryset.filter(statut=statut)

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(numero_commande__icontains=search) |
                Q(fournisseur__nom__icontains=search)
            )

        date_debut_str = self.request.GET.get('date_debut')
        if date_debut_str:
            try:
                date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d').date()
                queryset = queryset.filter(date_commande__gte=date_debut)
            except ValueError:
                messages.error(self.request, "Format de date de début invalide. Utilisez le format AAAA-MM-JJ.")

        date_fin_str = self.request.GET.get('date_fin')
        if date_fin_str:
            try:
                date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d').date()
                date_fin_eod = datetime.combine(date_fin, time.max)
                queryset = queryset.filter(date_commande__lte=date_fin_eod)
            except ValueError:
                messages.error(self.request, "Format de date de fin invalide. Utilisez le format AAAA-MM-JJ.")

        fournisseur_id = self.request.GET.get('fournisseur')
        if fournisseur_id:
            try:
                selected_fournisseur = Fournisseur.objects.filter(
                    pk=fournisseur_id,
                    entreprise=self.request.entreprise
                ).first()
                if selected_fournisseur:
                    queryset = queryset.filter(fournisseur=selected_fournisseur)
                else:
                    messages.warning(self.request, "Fournisseur sélectionné introuvable ou non autorisé.")
            except ValueError:
                messages.error(self.request, "ID fournisseur invalide.")
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        devise_principale = None
        try:
            config_saas = self.request.entreprise.config_saas
            devise_principale = config_saas.devise_principale
        except AttributeError:
            messages.warning(self.request, "Configuration SAAS ou devise principale manquante pour votre entreprise. Veuillez la configurer.")
        except ConfigurationSAAS.DoesNotExist:
            messages.warning(self.request, "Configuration SAAS manquante pour votre entreprise. Veuillez la configurer.")
        
        context['devise_principale'] = devise_principale

        context['statuts_choices'] = [('', 'Tous les statuts')] + list(CommandeAchat.STATUT_CHOICES)
        context['statut_filter'] = self.request.GET.get('statut', '')
        context['search'] = self.request.GET.get('search', '')
        context['date_debut_filter'] = self.request.GET.get('date_debut', '')
        context['date_fin_filter'] = self.request.GET.get('date_fin', '')
        context['fournisseur_filter'] = self.request.GET.get('fournisseur', '')
        context['fournisseurs_list'] = Fournisseur.objects.filter(entreprise=self.request.entreprise).order_by('nom')
        
        return context
# IMPORTANT : La définition du formset doit être en dehors de la classe de la vue.
# Si vous l'avez mise à l'intérieur, c'est une erreur et il faut la déplacer.
LigneCommandeAchatFormSet = inlineformset_factory(
    CommandeAchat,
    LigneCommandeAchat,
    form=LigneCommandeAchatForm,
    extra=1, # Initialement une ligne vide pour la saisie
    can_delete=True
)

from .models import CommandeAchat, LigneCommandeAchat
from .forms import CommandeAchatForm, LigneCommandeAchatFormSet

class CreerCommandeView(EntrepriseAccessMixin, CreateView):
    model = CommandeAchat
    form_class = CommandeAchatForm
    template_name = 'achats/commandes/form.html'
    success_url = reverse_lazy('achats:liste_commandes')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['entreprise'] = self.request.entreprise
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.method == 'POST':
            formset = LigneCommandeAchatFormSet(
                self.request.POST,
                prefix='lignes',
                form_kwargs={'entreprise': self.request.entreprise}
            )
        else:
            formset = LigneCommandeAchatFormSet(
                queryset=LigneCommandeAchat.objects.none(),
                prefix='lignes',
                form_kwargs={'entreprise': self.request.entreprise}
            )
        context['formset'] = formset
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    commande = form.save(commit=False)
                    commande.entreprise = self.request.entreprise
                    commande.created_by = self.request.user
                    commande.save()
                    
                    formset.instance = commande
                    formset.save()
                    
                    messages.success(self.request, 'Commande créée avec succès.')
                    return HttpResponseRedirect(self.success_url)
            except Exception as e:
                messages.error(
                    self.request,
                    f"Erreur lors de l'enregistrement : {str(e)}"
                )
                return self.form_invalid(form)
        return self.form_invalid(form)
def form_invalid(self, form):
    context = self.get_context_data(form=form)
    formset = context['formset']
    
    # Affichage détaillé des erreurs
    if form.errors:
        messages.error(
            self.request,
            "Veuillez corriger les erreurs suivantes dans les informations générales :"
        )
        for field, errors in form.errors.items():
            # CORRECTION: Convertir ErrorList en string
            error_messages = ', '.join([str(error) for error in errors])
            messages.error(
                self.request,
                f"- {field}: {error_messages}"
            )
    
    if formset.errors:
        messages.error(
            self.request,
            "Veuillez corriger les erreurs suivantes dans les lignes de commande :"
        )
        for i, form_line in enumerate(formset):
            if form_line.errors:
                # CORRECTION: Convertir ErrorList en string pour chaque champ
                error_messages = []
                for field, errors in form_line.errors.items():
                    error_messages.append(f"{field}: {', '.join([str(e) for e in errors])}")
                
                messages.error(
                    self.request,
                    f"Ligne {i+1}: {', '.join(error_messages)}"
                )
        
        # Afficher aussi les erreurs non-field du formset
        if formset.non_form_errors():
            messages.error(
                self.request,
                f"Erreurs générales: {', '.join([str(e) for e in formset.non_form_errors()])}"
            )
    
    # Mode débogage
    if settings.DEBUG:
        print("\n=== Erreurs Formulaire Principal ===")
        print(form.errors)
        print("\n=== Erreurs Formset ===")
        print(formset.errors)
        if hasattr(formset, 'non_form_errors'):
            print("\n=== Erreurs Non-Form du Formset ===")
            print(formset.non_form_errors())
    
    return self.render_to_response(context)
    
class ModifierCommandeView(EntrepriseAccessMixin, UpdateView):
    model = CommandeAchat
    form_class = CommandeAchatForm
    template_name = 'achats/commandes/form.html'
    success_url = reverse_lazy('achats:liste_commandes')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['entreprise'] = self.request.entreprise
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pour une vue de modification, le formset doit toujours être lié à l'instance existante
        # (self.object est la CommandeAchat que nous modifions).
        if self.request.POST:
            # Si c'est une soumission POST, le formset est lié aux données POST
            context['formset'] = LigneCommandeAchatFormSet(
                self.request.POST,
                instance=self.object,
                prefix='lignes',
                form_kwargs={'entreprise': self.request.entreprise}
            )
        else:
            # Pour une requête GET, le formset est pré-rempli avec les lignes existantes
            context['formset'] = LigneCommandeAchatFormSet(
                instance=self.object,
                prefix='lignes',
                form_kwargs={'entreprise': self.request.entreprise}
            )
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        # Vérifions la validité des deux formulaires (principal et formset)
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Sauvegardons la commande principale.
                    # self.object est déjà l'instance que nous modifions.
                    self.object = form.save() 

                    # Liens le formset à cette même instance et sauvegardons les lignes de commande.
                    # Le formset.save() gère les ajouts, modifications et suppressions de lignes.
                    formset.instance = self.object
                    formset.save() 

                messages.success(self.request, 'Commande modifiée avec succès.')
                return HttpResponseRedirect(self.success_url) # Redirection explicite vers l'URL de succès

            except Exception as e:
                messages.error(
                    self.request,
                    f"Erreur inattendue lors de la modification de la commande : {str(e)}"
                )
                # En cas d'exception (ex: problème de base de données), on renvoie au formulaire invalide
                return self.form_invalid(form)
        else:
            # Si le formulaire principal ou le formset n'est pas valide,
            # nous déléguons l'affichage des erreurs à la méthode form_invalid.
            return self.form_invalid(form)

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        formset = context['formset']
        
        # Affichage des erreurs du formulaire principal
        if form.errors:
            messages.error(
                self.request,
                "Veuillez corriger les erreurs suivantes dans les informations générales de la commande :"
            )
            for field, errors in form.errors.items():
                messages.error(
                    self.request,
                    f"- {field}: {', '.join(errors)}"
                )
        
        # Affichage des erreurs du formset (lignes de commande)
        if formset.errors:
            messages.error(
                self.request,
                "Veuillez corriger les erreurs suivantes dans les lignes de commande :"
            )
            for i, line_form in enumerate(formset):
                if line_form.errors:
                    # Collecte et affiche toutes les erreurs pour chaque ligne de commande
                    messages.error(
                        self.request,
                        f"Ligne {i+1}: {', '.join(error for error_list in line_form.errors.values() for error in error_list)}"
                    )
            # Affiche les erreurs non liées à un champ spécifique du formset (ex: erreurs de validation globales du formset)
            if formset.non_form_errors():
                messages.error(
                    self.request,
                    f"Erreurs générales dans les lignes de commande : {', '.join(formset.non_form_errors())}"
                )
        
        # Mode débogage : Impression des erreurs dans la console (visible uniquement si settings.DEBUG est True)
        if settings.DEBUG:
            print("\n=== Erreurs Formulaire Principal ===")
            print(form.errors)
            print("\n=== Erreurs Formset ===")
            print(formset.errors)
            if hasattr(formset, 'non_form_errors'):
                print("\n=== Erreurs Non-Form du Formset ===")
                print(formset.non_form_errors)
        
        return self.render_to_response(context) 
        
class DetailCommandeView(EntrepriseAccessMixin, DetailView):
    model = CommandeAchat
    template_name = 'achats/commandes/detail.html'
    context_object_name = 'commande'

    def get_queryset(self):
        return super().get_queryset().filter(
            entreprise=self.request.entreprise
        ).select_related(
            'fournisseur',
            'created_by',
            'entreprise__config_saas__devise_principale'
        ).prefetch_related('lignes__produit')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        commande = self.object

        # Récupération de la devise principale
        devise_principale = None
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.entreprise)
            devise_principale = config_saas.devise_principale
        except ConfigurationSAAS.DoesNotExist:
            messages.warning(self.request, "Configuration SAAS manquante pour votre entreprise. Veuillez la configurer.")
        except Devise.DoesNotExist:
            messages.warning(self.request, "Aucune devise principale configurée dans votre configuration SAAS. Veuillez la définir.")
        
        context['devise_principale'] = devise_principale
        context['can_validate'] = self.request.user.has_perm('achats.valider_commandeachat')

        # Récupération des lignes de commande avec préchargement
        context['lignes'] = commande.lignes.all()

        # Ajout des totaux calculés depuis le modèle CommandeAchat
        context['total_ht'] = commande.total_ht
        context['total_tva'] = commande.total_tva
        context['total_ttc'] = commande.total_ttc

        # Pour afficher le détail des taux de TVA utilisés dans la commande
        lignes_par_tva = {}
        for ligne in context['lignes']:
            taux = ligne.taux_tva
            if taux not in lignes_par_tva:
                lignes_par_tva[taux] = {
                    'montant_ht': Decimal('0.00'),
                    'montant_tva': Decimal('0.00')
                }
            lignes_par_tva[taux]['montant_ht'] += ligne.total_ht_ligne
            lignes_par_tva[taux]['montant_tva'] += ligne.montant_tva_ligne
        
        context['tva_details'] = sorted(
            [(taux, data) for taux, data in lignes_par_tva.items()],
            key=lambda x: x[0],
            reverse=True
        )

        return context
    

logger = logging.getLogger(__name__)

class DashboardView(EntrepriseAccessMixin, TemplateView):
    template_name = "achats/dashboard/index.html"

    def get_date_filters(self):
        """Gère les filtres de date depuis les paramètres GET"""
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        
        filters = {}
        if date_debut and date_fin:
            try:
                date_debut_obj = datetime.strptime(date_debut, "%Y-%m-%d").date()
                date_fin_obj = datetime.strptime(date_fin, "%Y-%m-%d").date()
                filters['date_commande__range'] = [date_debut_obj, date_fin_obj]
            except ValueError:
                logger.error(f"Invalid date format for date_debut: {date_debut} or date_fin: {date_fin}")
                pass # Continue without date filters if format is wrong
        return filters

    def get_commandes_stats(self, entreprise, commande_filters):
        """Calcule les statistiques des commandes"""
        commandes_qs = CommandeAchat.objects.filter(
            entreprise=entreprise,
            **commande_filters
        )
        
        montant_total = commandes_qs.aggregate(
            total=Coalesce(Sum(
                ExpressionWrapper(
                    F('lignes__prix_unitaire') * F('lignes__quantite') * (Decimal('1.0') - F('lignes__remise') / Decimal('100.0')),
                    output_field=DecimalField()
                )
            ), Decimal('0.0'))
        )['total']
        
        count = commandes_qs.count()

        return {
            'montant_total': montant_total,
            'count': count,
            'commandes_qs': commandes_qs
        }

    def get_top_fournisseurs(self, commandes_qs):
        """Retourne les 3 fournisseurs avec le plus gros montant de commandes"""
        top_fournisseurs_data = (
            Fournisseur.objects
            .filter(commandes__in=commandes_qs)
            .annotate(
                total_montant=Coalesce(Sum(
                    ExpressionWrapper(
                        F('commandes__lignes__prix_unitaire') * F('commandes__lignes__quantite') * (Decimal('1.0') - F('commandes__lignes__remise') / Decimal('100.0')),
                        output_field=DecimalField()
                    )
                ), Decimal('0.0')),
                commandes_count=Count('commandes', distinct=True)
            )
            .order_by('-total_montant')[:3]
        )
        
        results = []
        for item in top_fournisseurs_data:
            try:
                fournisseur_obj = Fournisseur.objects.get(id=item['id'])
                results.append({
                    'fournisseur': fournisseur_obj,
                    'montant_total': item['total_montant'],
                    'commandes_count': item['commandes_count']
                })
            except Fournisseur.DoesNotExist:
                logger.warning(f"Fournisseur with ID {item['id']} not found for top suppliers list.")
                continue # Skip if supplier somehow doesn't exist

        return results


    def get_commandes_par_periode(self, commandes_qs):
        """Agrège les commandes par période pour les graphiques"""
        period = self.request.GET.get('period', 'month')
        
        trunc_func = TruncMonth('commande__date_commande')
        if period == 'week':
            trunc_func = TruncWeek('commande__date_commande')
        elif period == 'day':
            trunc_func = TruncDay('commande__date_commande')

        return (
            LigneCommandeAchat.objects
            .filter(commande__in=commandes_qs)
            .annotate(
                period_date=trunc_func,
                montant=ExpressionWrapper(
                    F('prix_unitaire') * F('quantite') * (Decimal('1.0') - F('remise') / Decimal('100.0')),
                    output_field=DecimalField()
                )
            )
            .values('period_date')
            .annotate(
                count=Count('commande', distinct=True),
                montant_total=Coalesce(Sum('montant'), Decimal('0.0'))
            )
            .order_by('period_date')
        )

    def get_commandes_par_statut(self, commandes_qs):
        """Retourne le nombre de commandes par statut et leur montant total"""
        return (
            commandes_qs
            .values('statut')
            .annotate(
                count=Count('id'),
                montant_total=Coalesce(Sum(
                    ExpressionWrapper(
                        F('lignes__prix_unitaire') * F('lignes__quantite') * (Decimal('1.0') - F('lignes__remise') / Decimal('100.0')),
                        output_field=DecimalField()
                    )
                ), Decimal('0.0'))
            )
            .order_by('-montant_total', 'statut')
        )

    def get_bons_reception_stats(self, entreprise, commande_filters):
        """Calcule les statistiques des bons de réception"""
        # Note: 'en_attente' logic here is an example. Adjust based on your BonReception model's status.
        return BonReception.objects.filter(
            entreprise=entreprise,
            commande__in=CommandeAchat.objects.filter(
                entreprise=entreprise,
                **commande_filters
            )
        ).aggregate(
            count=Count('id'),
            # This 'en_attente' implies that some quantity on reception lines is less than ordered.
            # If BonReception has a specific 'status' field (e.g., 'pending', 'validated'), use that instead.
            # Example: en_attente=Count('id', filter=Q(statut='en_attente')) if a 'statut' field exists.
            en_attente=Count('id', filter=Q(lignes__quantite__lt=F('lignes__ligne_commande__quantite')))
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.user.entreprise

        date_filters = self.get_date_filters()
        
        # Statistiques des commandes (Achats)
        commandes_stats = self.get_commandes_stats(entreprise, date_filters)
        context.update({
            'montant_total_commandes': commandes_stats['montant_total'],
            'nombre_commandes': commandes_stats['count'],
            'commandes_achat_qs': commandes_stats['commandes_qs']
        })

        # Top fournisseurs (based on the filtered purchase orders)
        context['top_fournisseurs'] = self.get_top_fournisseurs(
            context['commandes_achat_qs']
        )

        # Commandes par période (pour graphique)
        commandes_par_periode_data = self.get_commandes_par_periode(
            context['commandes_achat_qs']
        )
        
        chart_labels = []
        chart_values = []
        for item in commandes_par_periode_data:
            if self.request.GET.get('period') == 'week':
                chart_labels.append(f"S{item['period_date'].isocalendar().week} {item['period_date'].year}")
            elif self.request.GET.get('period') == 'day':
                chart_labels.append(item['period_date'].strftime('%d/%m'))
            else: # Default to month
                chart_labels.append(item['period_date'].strftime('%b %Y'))
            chart_values.append(float(item['montant_total']))

        context['commandes_chart_labels'] = chart_labels
        context['commandes_chart_data'] = chart_values


        # Commandes par statut
        context['commandes_par_statut'] = self.get_commandes_par_statut(
            context['commandes_achat_qs']
        )

        # Statistiques des bons de réception
        reception_stats = self.get_bons_reception_stats(entreprise, date_filters)
        context.update({
            'nombre_bons_reception': reception_stats['count'],
            'bons_en_attente': reception_stats['en_attente']
        })

        # Alertes
        today = timezone.localdate()
        context['commandes_en_retard'] = CommandeAchat.objects.filter(
            entreprise=entreprise,
            date_livraison_prevue__lt=today,
            statut__in=['envoyee', 'partiellement_livree']
        ).count()

        # Corrected for Produit model fields 'stock' and 'seuil_alerte'
        context['low_stock_products_count'] = Produit.objects.filter(
            entreprise=entreprise,
            stock__lte=F('seuil_alerte') # Use 'stock' and 'seuil_alerte' directly
        ).count()

        context['total_alerts'] = context['commandes_en_retard'] + context['low_stock_products_count']

        # Pass current filter params to template for active state in UI
        context['current_date_debut'] = self.request.GET.get('date_debut', '')
        context['current_date_fin'] = self.request.GET.get('date_fin', '')
        context['active_period'] = self.request.GET.get('period', 'month')

        return context
import io
import logging
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.views import View
from django.contrib import messages
from django.core.mail import EmailMessage
from django.utils import timezone   

from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)

class ValiderCommandeView(EntrepriseAccessMixin, View):
    """
    Vue pour valider une commande d'achat avec prévisualisation PDF et envoi email
    """

    def get(self, request, pk):
        """Affiche la page de confirmation avec prévisualisation"""
        commande = self.get_object_filtered(pk)
        if not commande:
            messages.error(request, "Commande introuvable ou non autorisée.")
            return redirect('achats:liste_commandes')

        if commande.statut != 'brouillon':
            messages.warning(
                request,
                f"Cette commande est déjà en statut '{commande.get_statut_display()}'. "
                "Seules les commandes en brouillon peuvent être validées."
            )
            return redirect('achats:detail_commande', pk=commande.pk)

        # Génération de la prévisualisation PDF
        try:
            symbole_devise = self._get_devise_symbol(commande)
            lignes = list(commande.lignes.all().select_related('produit'))
            pdf_content = self._generate_pdf_content(
                request, commande, lignes, symbole_devise
            )
            
            # Sauvegarde temporaire du PDF pour prévisualisation
            preview_path = f"temp/preview_bc_{commande.pk}.pdf"
            full_path = os.path.join(settings.MEDIA_ROOT, preview_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'wb') as f:
                f.write(pdf_content)
            
            preview_url = settings.MEDIA_URL + preview_path
        except Exception as e:
            logger.error(f"Erreur génération prévisualisation PDF: {str(e)}")
            preview_url = None
            messages.warning(request, "La prévisualisation n'a pas pu être générée")

        context = {
            'commande': commande,
            'statut_actuel': commande.get_statut_display(),
            'preview_url': preview_url,
            'symbole_devise': symbole_devise,
            'totals': {
                'ht': commande.total_ht,
                'tva': commande.total_tva,
                'ttc': commande.total_ttc
            }
        }
        return render(request, 'achats/commandes/confirmer_validation.html', context)

    def post(self, request, pk):
        """Traite la validation définitive de la commande"""
        commande = self.get_object_filtered(pk)
        if not commande:
            messages.error(request, "Commande introuvable ou non autorisée.")
            return redirect('achats:liste_commandes')

        if commande.statut != 'brouillon':
            messages.error(
                request,
                f"Statut actuel : {commande.get_statut_display()}. "
                "Seules les commandes en brouillon peuvent être validées."
            )
            return redirect('achats:detail_commande', pk=commande.pk)

        try:
            with transaction.atomic():
                # 1. Validation et mise à jour du statut
                commande.statut = 'envoyee'
                commande.date_envoi = timezone.now()
                commande.save()

                # 2. Génération PDF finale
                symbole_devise = self._get_devise_symbol(commande)
                lignes = list(commande.lignes.all().select_related('produit'))
                pdf_content = self._generate_pdf_content(
                    request, commande, lignes, symbole_devise
                )

                # 3. Envoi email
                self._send_confirmation_email(request, commande, pdf_content)

                # Nettoyage de la prévisualisation
                preview_path = f"temp/preview_bc_{commande.pk}.pdf"
                full_path = os.path.join(settings.MEDIA_ROOT, preview_path)
                if os.path.exists(full_path):
                    os.remove(full_path)

                messages.success(
                    request, 
                    f"Commande #{commande.numero_commande} validée et envoyée avec succès. "
                    f"Total TTC: {commande.total_ttc:.2f} {symbole_devise}"
                )
                logger.info(f"Commande {commande.pk} validée par {request.user.email}")

        except Exception as e:
            logger.error(f"Erreur validation commande {pk}: {str(e)}", exc_info=True)
            messages.error(request, f"Erreur lors de la validation : {str(e)}")
            return redirect('achats:detail_commande', pk=pk)

        return redirect('achats:detail_commande', pk=commande.pk)

    def get_object_filtered(self, pk):
        """Récupère la commande avec toutes les relations nécessaires"""
        try:
            return CommandeAchat.objects.filter(
                pk=pk,
                entreprise=self.request.entreprise
            ).select_related(
                'fournisseur',
                'entreprise',
                'entreprise__config_saas__devise_principale',
                'created_by'
            ).prefetch_related(
                'lignes__produit'
            ).first()
        except Exception as e:
            logger.error(f"Erreur dans get_object_filtered: {str(e)}")
            return None

    def _get_devise_symbol(self, commande):
        """Récupère le symbole de la devise principale"""
        config_saas = getattr(commande.entreprise, 'config_saas', None)
        devise_principale = getattr(config_saas, 'devise_principale', None) if config_saas else None
        return getattr(devise_principale, 'symbole', '$')

    def _generate_pdf_content(self, request, commande, lignes, symbole_devise):
        """Génère le contenu PDF du bon de commande"""
        context = {
            'commande': commande,
            'lignes': lignes,
            'entreprise': request.entreprise,
            'total_ht': commande.total_ht,
            'total_tva': commande.total_tva,
            'total_ttc': commande.total_ttc,
            'symbole_devise': symbole_devise,
            'now': timezone.now(),
            'user': request.user,
            'is_invoice': False,
        }

        html = render_to_string('achats/commandes/bon_commande_pdf.html', context)
        result_file = io.BytesIO()

        pdf = pisa.CreatePDF(
            html,
            dest=result_file,
            encoding='utf-8',
            link_callback=self._fetch_resources
        )

        if pdf.err:
            error_msg = f"Erreur génération PDF: {pdf.err}"
            if hasattr(pdf, 'log'):
                error_msg += f"\nLog: {pdf.log}"
            raise ValueError(error_msg)

        pdf_content = result_file.getvalue()
        result_file.close()

        if not pdf_content:
            raise ValueError("Le contenu PDF généré est vide")

        return pdf_content

    def _fetch_resources(self, uri, rel):
        """Gère les ressources externes (images, CSS) pour le PDF"""
        if uri.startswith('http') or uri.startswith('https'):
            return uri

        if uri.startswith('/media/'):
            path = os.path.join(settings.MEDIA_ROOT, uri[7:])
            if os.path.exists(path):
                return path

        if uri.startswith('/static/'):
            path = os.path.join(settings.STATIC_ROOT, uri[8:])
            if os.path.exists(path):
                return path

        return None

    def _send_confirmation_email(self, request, commande, pdf_content):
        """Envoie l'email de confirmation au fournisseur"""
        if not commande.fournisseur or not commande.fournisseur.email:
            logger.warning(f"Email fournisseur manquant pour la commande {commande.pk}")
            return

        try:
            context = {
                'commande': commande,
                'entreprise': request.entreprise,
                'totals': {
                    'ht': commande.total_ht,
                    'tva': commande.total_tva,
                    'ttc': commande.total_ttc
                },
                'date_validation': timezone.now(),
                'user': request.user,
                'symbole_devise': self._get_devise_symbol(commande)
            }

            subject = f"Bon de Commande #{commande.numero_commande} - {request.entreprise.nom}"
            body = render_to_string('achats/commandes/bon_commande_email.html', context)

            email = EmailMessage(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [commande.fournisseur.email],
                reply_to=[request.user.email],
            )
            email.content_subtype = "html"
            email.attach(
                f"BonCommande_{commande.numero_commande}.pdf",
                pdf_content,
                "application/pdf"
            )
            email.send()
            logger.info(f"Email envoyé à {commande.fournisseur.email} pour la commande {commande.pk}")

        except Exception as e:
            logger.error(f"Erreur envoi email commande {commande.pk}: {str(e)}")
            raise Exception("Erreur lors de l'envoi de l'email de confirmation")
    
class ListeFournisseursView(EntrepriseAccessMixin, ListView):
    model = Fournisseur
    template_name = 'achats/fournisseurs/liste.html'
    context_object_name = 'fournisseurs'

    def get_queryset(self):
        return super().get_queryset().filter(
            entreprise=self.request.entreprise
        ).order_by('nom')
        
        
# --- NOUVELLES VUES D'IMPORT/EXPORT ---
class ImporterFournisseursView(EntrepriseAccessMixin, FormView): # Changed from CreateView to FormView
    template_name = 'achats/fournisseurs/importer.html'
    form_class = ImportFournisseurForm
    success_url = reverse_lazy('achats:liste_fournisseurs')

    # The form_valid method logic remains largely the same,
    # but we need to pass the form instance to super().form_valid()
    def form_valid(self, form):
        fichier_excel = self.request.FILES['fichier_excel']
        entreprise_actuelle = self.request.entreprise
        fournisseurs_crees = 0
        fournisseurs_mis_a_jour = 0
        erreurs = []

        try:
            df = pd.read_excel(fichier_excel)

            colonnes_requises = ['Nom', 'Code', 'Email', 'Telephone', 'Adresse']
            if not all(col in df.columns for col in colonnes_requises):
                messages.error(self.request, "Le fichier Excel doit contenir les colonnes 'Nom', 'Code', 'Email', 'Telephone', 'Adresse'.")
                return self.form_invalid(form)

            with transaction.atomic():
                for index, row in df.iterrows():
                    nom = row['Nom']
                    code = row['Code'] # The code can be provided or generated if empty
                    email = row['Email']
                    telephone = row['Telephone']
                    adresse = row['Adresse'] if pd.notna(row['Adresse']) else ''

                    try:
                        fournisseur, created = Fournisseur.objects.update_or_create(
                            entreprise=entreprise_actuelle,
                            code=code,
                            defaults={
                                'nom': nom,
                                'email': email,
                                'telephone': telephone,
                                'adresse': adresse,
                            }
                        )
                        if created:
                            fournisseurs_crees += 1
                        else:
                            fournisseurs_mis_a_jour += 1
                    except IntegrityError as e:
                        erreurs.append(f"Ligne {index + 2} (Code: {code}, Nom: {nom}): Erreur d'intégrité - {e}")
                    except Exception as e:
                        erreurs.append(f"Ligne {index + 2} (Code: {code}, Nom: {nom}): Erreur inattendue - {e}")

            if erreurs:
                msg = f"{fournisseurs_crees} fournisseurs créés, {fournisseurs_mis_a_jour} mis à jour. Mais il y a eu des erreurs pour certains fournisseurs : {'; '.join(erreurs)}"
                messages.warning(self.request, msg)
            else:
                messages.success(self.request, f"{fournisseurs_crees} fournisseurs créés et {fournisseurs_mis_a_jour} mis à jour avec succès.")

        except pd.errors.EmptyDataError:
            messages.error(self.request, "Le fichier Excel est vide.")
        except FileNotFoundError:
            messages.error(self.request, "Fichier non trouvé (erreur interne).")
        except Exception as e:
            messages.error(self.request, f"Une erreur s'est produite lors de la lecture du fichier : {e}")

        # For FormView, super().form_valid() expects the form instance
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Veuillez sélectionner un fichier Excel valide.")
        return super().form_invalid(form)

def exporter_fournisseurs_excel(request):
    # S'assurer que l'utilisateur a accès à l'entreprise
    if not hasattr(request, 'entreprise'):
        messages.error(request, "Accès refusé. Veuillez vous connecter ou sélectionner une entreprise.")
        return redirect('url_de_connexion_ou_selection_entreprise') # Remplace par ta vraie URL

    fournisseurs = Fournisseur.objects.filter(entreprise=request.entreprise).order_by('nom')

    data = {
        'Code': [f.code for f in fournisseurs],
        'Nom': [f.nom for f in fournisseurs],
        'Email': [f.email for f in fournisseurs],
        'Telephone': [f.telephone for f in fournisseurs],
        'Adresse': [f.adresse for f in fournisseurs],
        'Date Creation': [f.created_at.strftime("%Y-%m-%d %H:%M") for f in fournisseurs],
    }
    df = pd.DataFrame(data)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="fournisseurs_{request.entreprise.nom}_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    df.to_excel(response, index=False)
    return response


def exporter_fournisseurs_pdf(request):
    # S'assurer que l'utilisateur a accès à l'entreprise
    if not hasattr(request, 'entreprise'):
        messages.error(request, "Accès refusé. Veuillez vous connecter ou sélectionner une entreprise.")
        return redirect('url_de_connexion_ou_selection_entreprise') # Remplace par ta vraie URL

    fournisseurs = Fournisseur.objects.filter(entreprise=request.entreprise).order_by('nom')

    template_path = 'achats/fournisseurs/fournisseurs_pdf.html' # Crée ce template
    context = {'fournisseurs': fournisseurs, 'entreprise': request.entreprise}

    # Rendu du template HTML en chaîne
    template = get_template(template_path)
    html = template.render(context)

    # Création du PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="fournisseurs_{request.entreprise.nom}_{pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")}.pdf"'

    pisa_status = pisa.CreatePDF(
        html, dest=response
    )
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    return response


class CreerFournisseurView(EntrepriseAccessMixin, CreateView):
    model = Fournisseur
    form_class = FournisseurForm
    template_name = 'achats/fournisseurs/form.html'
    success_url = reverse_lazy('achats:liste_fournisseurs')

    def form_valid(self, form):
        # 'entreprise' est toujours nécessaire car c'est une clé étrangère non-nullable.
        # Le champ 'code' sera généré par la méthode save du modèle, donc pas besoin ici.
        form.instance.entreprise = self.request.entreprise
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['entreprise'] = self.request.entreprise
        return kwargs
class CreerFournisseurView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Fournisseur
    form_class = FournisseurForm
    template_name = 'achats/fournisseurs/form.html'
    permission_required = 'achats.add_fournisseur'
    success_url = reverse_lazy('achats:liste_fournisseurs')
    success_message = "Le fournisseur '%(nom)s' a été créé avec succès."

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['entreprise'] = self.request.user.entreprise
        return kwargs
        
    def form_valid(self, form):
        form.instance.entreprise = self.request.user.entreprise
        return super().form_valid(form)


class ModifierFournisseurView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Fournisseur
    form_class = FournisseurForm
    template_name = 'achats/fournisseurs/form.html'
    permission_required = 'achats.change_fournisseur'
    success_url = reverse_lazy('achats:liste_fournisseurs')
    success_message = "Le fournisseur '%(nom)s' a été modifié avec succès."

    def get_queryset(self):
        # Assurez-vous que seuls les fournisseurs de l'entreprise actuelle peuvent être manipulés
        return super().get_queryset().filter(entreprise=self.request.user.entreprise)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['entreprise'] = self.request.user.entreprise
        return kwargs

class SupprimerFournisseurView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Fournisseur
    template_name = 'achats/fournisseurs/delete.html'
    permission_required = 'achats.delete_fournisseur'
    success_url = reverse_lazy('achats:liste_fournisseurs')

    def get_queryset(self):
        return super().get_queryset().filter(entreprise=self.request.user.entreprise)

    def form_valid(self, form):
        try:
            # Tente de supprimer l'objet et affiche un message de succès
            response = super().form_valid(form)
            messages.success(self.request, f"Le fournisseur '{self.object.nom}' a été supprimé avec succès.")
            return response
        except ProtectedError:
            # En cas d'erreur de protection (objets liés)
            fournisseur = self.object
            messages.error(
                self.request,
                f"Impossible de supprimer le fournisseur '{fournisseur.nom}' car il a des commandes liées. "
                "Veuillez d'abord supprimer les commandes d'achat associées."
            )
            return redirect('achats:detail_fournisseur', pk=fournisseur.pk)

class DetailFournisseurView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Fournisseur
    template_name = 'achats/fournisseurs/detail.html'
    permission_required = 'achats.view_fournisseur'

    def get_queryset(self):
        return super().get_queryset().filter(entreprise=self.request.user.entreprise)

logger = logging.getLogger(__name__)


# --- VUES POUR LES BONS DE RÉCEPTION ---

class ListeBonsView(EntrepriseAccessMixin, ListView):
    model = BonReception
    template_name = 'achats/bons/liste.html'
    context_object_name = 'bons'

    def get_queryset(self):
        return super().get_queryset().filter(
            entreprise=self.request.entreprise
        ).select_related('commande', 'commande__fournisseur', 'created_by')
import logging
from django.db import transaction
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, View
from django.db.models import F
from decimal import Decimal
from .models import BonReception, LigneBonReception, CommandeAchat, LigneCommandeAchat
from .forms import LigneBonReceptionFormSet

logger = logging.getLogger(__name__)

class CreerBonView(CreateView,EntrepriseAccessMixin,LoginRequiredMixin, PermissionRequiredMixin):
    model = BonReception
    fields = ['numero_bon', 'date_reception', 'notes']
    template_name = 'achats/bons/form.html'

    def dispatch(self, request, *args, **kwargs):
        self.commande = CommandeAchat.objects.filter(
            pk=kwargs['commande_pk'],
            entreprise=request.entreprise
        ).select_related(
            'fournisseur',
            'entreprise__config_saas', 
            'entreprise__config_saas__devise_principale', 
            'created_by'
        ).first()

        if not self.commande:
            messages.error(request, "Commande introuvable.")
            return redirect('achats:liste_commandes')
        
        if self.commande.statut == 'livree':
            messages.warning(request, f"La commande {self.commande.numero_commande} est déjà entièrement livrée.")
            return redirect('achats:detail_commande', pk=self.commande.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['initial'] = {
            'date_reception': timezone.now().date(),
            'numero_bon': self._generate_bon_reception_number()
        }
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['commande'] = self.commande
        context['fournisseur'] = self.commande.fournisseur
        
        config_saas = getattr(self.commande.entreprise, 'config_saas', None)
        devise_principale = config_saas.devise_principale if config_saas else None
        context['devise_principale'] = devise_principale
        context['symbole_devise'] = devise_principale.symbole if devise_principale else '$'

        formset_common_kwargs = {
            'prefix': 'lignes',
            'instance': None, 
            'queryset': LigneBonReception.objects.none(), 
            'form_kwargs': {'commande': self.commande.pk} 
        }

        if self.request.POST:
            context['formset'] = LigneBonReceptionFormSet(
                self.request.POST,
                self.request.FILES,
                **formset_common_kwargs 
            )
        else:
            context['formset'] = LigneBonReceptionFormSet(
                **formset_common_kwargs 
            )
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']

        if not formset.is_valid():
            messages.error(self.request, "Veuillez corriger les erreurs dans les lignes de réception.")
            return self.render_to_response(self.get_context_data(form=form))

        with transaction.atomic():
            self.object = form.save(commit=False)
            self.object.entreprise = self.request.entreprise
            self.object.commande = self.commande
            self.object.created_by = self.request.user
            self.object.save()

            formset.instance = self.object 
            lignes_reception_a_sauver = formset.save(commit=False)
            
            for ligne_reception in lignes_reception_a_sauver:
                if ligne_reception.quantite > Decimal('0') and not getattr(ligne_reception, 'DELETE', False): 
                    try:
                        ligne_commande = ligne_reception.ligne_commande
                        produit_recu = ligne_commande.produit

                        # Mise à jour du stock
                        if hasattr(produit_recu, 'ajouter_stock'):
                            if produit_recu.ajouter_stock(ligne_reception.quantite): 
                                messages.info(self.request, f"Stock de '{produit_recu.nom}' augmenté de {ligne_reception.quantite.normalize()}.")
                                
                                # Mise à jour de la quantité livrée
                                LigneCommandeAchat.objects.filter(pk=ligne_commande.pk).update(
                                    quantite_livree=F('quantite_livree') + ligne_reception.quantite
                                )
                                ligne_commande.refresh_from_db() 
                                
                                # Mise à jour du statut de livraison
                                if ligne_commande.quantite_livree >= ligne_commande.quantite:
                                    ligne_commande.livree = True
                                    ligne_commande.save(update_fields=['livree'])
                                    messages.info(self.request, f"Ligne de commande pour '{produit_recu.nom}' est maintenant entièrement livrée.")
                                
                                ligne_reception.save() 
                            else:
                                raise Exception(f"Impossible d'ajouter le stock pour '{produit_recu.nom}'. Quantité reçue invalide.")
                        else:
                            # Méthode alternative si ajouter_stock n'existe pas
                            produit_recu.quantite_stock += ligne_reception.quantite
                            produit_recu.save()
                            messages.info(self.request, f"Stock de '{produit_recu.nom}' augmenté de {ligne_reception.quantite.normalize()}.")
                            
                            # Mise à jour de la quantité livrée
                            LigneCommandeAchat.objects.filter(pk=ligne_commande.pk).update(
                                quantite_livree=F('quantite_livree') + ligne_reception.quantite
                            )
                            ligne_commande.refresh_from_db()
                            
                            # Mise à jour du statut de livraison
                            if ligne_commande.quantite_livree >= ligne_commande.quantite:
                                ligne_commande.livree = True
                                ligne_commande.save(update_fields=['livree'])
                                messages.info(self.request, f"Ligne de commande pour '{produit_recu.nom}' est maintenant entièrement livrée.")
                            
                            ligne_reception.save()
                            
                    except Exception as e:
                        logger.error(f"Erreur lors de la mise à jour du stock pour BonReception {self.object.pk}: {e}", exc_info=True)
                        messages.error(self.request, f"Erreur de stock pour {ligne_reception.ligne_commande.produit.nom}: {e}")
                        raise 

            # Mise à jour du statut de la commande
            self.commande.refresh_from_db()
            lignes_commande_all = self.commande.lignes.all()
            toutes_lignes_commande_livrees = all(lc.livree for lc in lignes_commande_all)
            au_moins_une_ligne_partiellement_livree = any(lc.quantite_livree > Decimal('0') for lc in lignes_commande_all)

            if toutes_lignes_commande_livrees:
                self.commande.statut = 'livree'
                messages.info(self.request, f"Commande {self.commande.numero_commande} est maintenant 'Livrée'.")
            elif au_moins_une_ligne_partiellement_livree:
                self.commande.statut = 'partiellement_livree'
                messages.info(self.request, f"Commande {self.commande.numero_commande} est maintenant 'Partiellement livrée'.")
            else:
                self.commande.statut = 'envoyee'
            
            self.commande.save(update_fields=['statut'])

            messages.success(self.request, 'Bon de réception créé et stock mis à jour avec succès.')
            return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('achats:detail_bon', kwargs={'pk': self.object.pk})

    def _generate_bon_reception_number(self):
        last_bon = BonReception.objects.filter(entreprise=self.request.entreprise).order_by('-pk').first()
        if last_bon and last_bon.numero_bon:
            try:
                last_num_str = last_bon.numero_bon.split('-')[-1]
                new_num = int(last_num_str) + 1 if last_num_str.isdigit() else 1
            except (ValueError, IndexError):
                new_num = 1
        else:
            new_num = 1
        return f"BR-{new_num:05d}"


def creer_bon_reception_automatique(commande_id, request):
    """
    Crée automatiquement un bon de réception pour une commande
    avec toutes les lignes livrées en totalité
    """
    try:
        commande = CommandeAchat.objects.get(
            pk=commande_id, 
            entreprise=request.entreprise
        )
        
        with transaction.atomic():
            # Créer le bon de réception
            bon = BonReception.objects.create(
                entreprise=request.entreprise,
                commande=commande,
                numero_bon=generer_numero_bon(request.entreprise),
                date_reception=timezone.now().date(),
                created_by=request.user
            )
            
            # Créer les lignes de réception pour chaque ligne de commande
            for ligne_commande in commande.lignes.all():
                quantite_a_livrer = ligne_commande.quantite - ligne_commande.quantite_livree
                
                if quantite_a_livrer > 0:
                    # Créer la ligne de réception
                    LigneBonReception.objects.create(
                        bon=bon,
                        ligne_commande=ligne_commande,
                        quantite=quantite_a_livrer,
                        conditionnement="Livraison complète"
                    )
                    
                    # Mettre à jour le stock
                    if hasattr(ligne_commande.produit, 'ajouter_stock'):
                        ligne_commande.produit.ajouter_stock(quantite_a_livrer)
                    else:
                        # Méthode alternative
                        ligne_commande.produit.quantite_stock += quantite_a_livrer
                        ligne_commande.produit.save()
                    
                    # Mettre à jour la quantité livrée
                    ligne_commande.quantite_livree = ligne_commande.quantite
                    ligne_commande.livree = True
                    ligne_commande.save()
            
            # Mettre à jour le statut de la commande
            commande.statut = 'livree'
            commande.save()
            
            messages.success(request, f"Bon de réception {bon.numero_bon} créé automatiquement avec succès.")
            return bon
            
    except Exception as e:
        logger.error(f"Erreur création bon réception automatique: {e}")
        messages.error(request, f"Erreur lors de la création automatique du bon de réception: {str(e)}")
        return None


def generer_numero_bon(entreprise):
    """Génère un numéro de bon de réception unique"""
    last_bon = BonReception.objects.filter(
        entreprise=entreprise
    ).order_by('-created_at').first()
    
    if last_bon and last_bon.numero_bon:
        try:
            last_num = int(last_bon.numero_bon.split('-')[-1])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 1
    else:
        new_num = 1
    
    return f"BR-{new_num:05d}"


class CreerBonAutomatique(View,EntrepriseAccessMixin,LoginRequiredMixin ):
    """Vue pour créer automatiquement un bon de réception complet"""
    
    def post(self, request, *args, **kwargs):
        commande_id = kwargs.get('commande_pk')
        
        bon = creer_bon_reception_automatique(commande_id, request)
        
        if bon:
            return redirect('achats:detail_bon', pk=bon.pk)
        else:
            return redirect('achats:detail_commande', pk=commande_id)



















# achats/views.py
class DetailBonView(EntrepriseAccessMixin, DetailView):
    model = BonReception
    template_name = 'achats/bons/detail.html'
    context_object_name = 'bon'

    def get_queryset(self):
        return super().get_queryset().filter(
            entreprise=self.request.entreprise
        ).select_related(
            'commande',
            'commande__fournisseur',
            'created_by'
        ).prefetch_related(
            'lignes__ligne_commande__produit'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bon = self.object
        
        # Récupération de la devise principale
        devise_principale = None
        symbole_devise = "€"  # symbole par défaut
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.entreprise)
            devise_principale = config_saas.devise_principale
            if devise_principale:
                symbole_devise = devise_principale.symbole
        except (ConfigurationSAAS.DoesNotExist, AttributeError):
            messages.warning(self.request, "Configuration SAAS ou devise principale manquante.")
        
        context['devise_principale'] = devise_principale
        context['symbole_devise'] = symbole_devise
        
        # Récupération des lignes avec calcul des totaux
        lignes = bon.lignes.all()
        total_bon = Decimal('0.00')
        
        for ligne in lignes:
            # Calcul du total HT pour chaque ligne
            ligne.total_ht_ligne = ligne.quantite * ligne.ligne_commande.prix_unitaire
            total_bon += ligne.total_ht_ligne
        
        context['lignes'] = lignes
        context['total_bon'] = total_bon
        
        return context
# achats/views.py
from django.http import HttpResponse
import os
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.views.generic import View
from django.shortcuts import redirect

class ExportBonReceptionPDFView(View):
    """Vue pour exporter un bon de réception en PDF"""
    
    def get(self, request, *args, **kwargs):
        try:
            from .utils import generate_bon_reception_pdf
            bon = get_object_or_404(BonReception, pk=kwargs['pk'], entreprise=request.entreprise)
            
            pdf_buffer = generate_bon_reception_pdf(bon)
            
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="bon_reception_{bon.numero_bon}.pdf"'
            response.write(pdf_buffer.getvalue())
            pdf_buffer.close()
            
            return response
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la génération du PDF: {str(e)}")
            return redirect('achats:detail_bon', pk=kwargs['pk'])

class ExportBonReceptionExcelView(View):
    """Vue pour exporter un bon de réception en Excel"""
    
    def get(self, request, *args, **kwargs):
        try:
            from .utils import generate_bon_reception_excel
            bon = get_object_or_404(BonReception, pk=kwargs['pk'], entreprise=request.entreprise)
            
            excel_path = generate_bon_reception_excel(bon)
            
            with open(excel_path, 'rb') as excel_file:
                response = HttpResponse(
                    excel_file.read(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = f'attachment; filename="bon_reception_{bon.numero_bon}.xlsx"'
            
            os.unlink(excel_path)
            
            return response
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la génération du Excel: {str(e)}")
            return redirect('achats:detail_bon', pk=kwargs['pk'])
    
# Dans vos views.py
from django.shortcuts import render
from comptabilite.models import PlanComptableOHADA, JournalComptable

def diagnostic_comptabilite(request):
    """Vue pour diagnostiquer l'état de la comptabilité"""
    entreprise = request.entreprise
    
    # Vérifier les comptes
    comptes = PlanComptableOHADA.objects.filter(entreprise=entreprise)
    comptes_essentiels = comptes.filter(numero__in=['31', '401'])
    
    # Vérifier les journaux
    journaux = JournalComptable.objects.filter(entreprise=entreprise)
    journal_achat = journaux.filter(code='ACH').first()
    
    context = {
        'entreprise': entreprise,
        'total_comptes': comptes.count(),
        'comptes_essentiels': comptes_essentiels,
        'total_journaux': journaux.count(),
        'journal_achat': journal_achat,
        'comptes_list': comptes[:10],  # Premiers 10 comptes
        'journaux_list': journaux,
    }
    
    return render(request, 'comptabilite/diagnostic.html', context)


# Dans vos views.py
from django.shortcuts import redirect
from django.contrib import messages
from comptabilite.models import PlanComptableOHADA, JournalComptable

def init_comptabilite_manuelle(request):
    """Initialisation manuelle de la comptabilité"""
    entreprise = request.entreprise
    
    try:
        comptes_crees = PlanComptableOHADA.initialiser_plan_comptable(entreprise)
        journaux_crees = JournalComptable.initialiser_journaux(entreprise)
        
        messages.success(
            request, 
            f"Comptabilité initialisée: {len(comptes_crees)} comptes et {len(journaux_crees)} journaux créés."
        )
    except Exception as e:
        messages.error(request, f"Erreur lors de l'initialisation: {str(e)}")
    
    return redirect('comptabilite:diagnostic_comptabilite')





from django.views.generic import ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.forms import modelformset_factory

from .models import FactureFournisseur, PaiementFournisseur
from .forms import FactureFournisseurForm, PaiementFournisseurForm
from parametres.models import ConfigurationSAAS
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

class FactureListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = FactureFournisseur
    template_name = 'achats/factures/liste.html'
    permission_required = 'achats.view_facturefournisseur'
    context_object_name = 'factures'
    paginate_by = 20

    def get_queryset(self):
        queryset = FactureFournisseur.objects.filter(
            entreprise=self.request.user.entreprise
        ).select_related('fournisseur', 'bon_reception')
        
        # Filtres
        statut = self.request.GET.get('statut')
        if statut:
            queryset = queryset.filter(statut=statut)
        
        fournisseur_id = self.request.GET.get('fournisseur')
        if fournisseur_id:
            queryset = queryset.filter(fournisseur_id=fournisseur_id)
        
        date_debut = self.request.GET.get('date_debut')
        if date_debut:
            queryset = queryset.filter(date_facture__gte=date_debut)
        
        date_fin = self.request.GET.get('date_fin')
        if date_fin:
            queryset = queryset.filter(date_facture__lte=date_fin)
        
        # Tri
        sort_field = self.request.GET.get('sort', 'date_facture')
        sort_order = self.request.GET.get('order', 'desc')
        
        if sort_order == 'desc':
            sort_field = f'-{sort_field}'
        
        return queryset.order_by(sort_field)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer la devise principale
        try:
            from parametres.models import ConfigurationSAAS
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except:
            devise_symbole = "€"
        
        # Liste des fournisseurs pour le filtre
        from .models import Fournisseur
        context['fournisseurs'] = Fournisseur.objects.filter(entreprise=self.request.user.entreprise)
        
        context["devise_principale_symbole"] = devise_symbole
        
        # Ajouter des propriétés aux factures pour le template
        today = timezone.now().date()
        for facture in context['factures']:
            facture.est_en_retard = facture.date_echeance < today and facture.reste_a_payer > 0
            facture.est_bientot_echeance = (facture.date_echeance - today <= timedelta(days=7) and 
                                          facture.date_echeance >= today and 
                                          facture.reste_a_payer > 0)
        
        return context

class FactureCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = FactureFournisseur
    form_class = FactureFournisseurForm
    template_name = 'achats/factures/form.html'
    permission_required = 'achats.add_facturefournisseur'
    success_url = reverse_lazy('achats:liste_factures')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['entreprise'] = self.request.user.entreprise
        return kwargs

    def form_valid(self, form):
        facture = form.save(commit=False)
        facture.entreprise = self.request.user.entreprise
        facture.created_by = self.request.user
        facture.save()
        
        messages.success(self.request, 'Facture créée avec succès.')
        return HttpResponseRedirect(self.success_url)


# achats/views.py
from django.views.generic import View
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .utils import generer_facture_depuis_bon

class GenererFactureDepuisBonView(View):
    """Vue pour générer une facture à partir d'un bon de réception"""
    
    def post(self, request, *args, **kwargs):
        bon_id = kwargs.get('pk')
        bon = get_object_or_404(BonReception, pk=bon_id, entreprise=request.entreprise)
        
        facture = generer_facture_depuis_bon(bon, request)
        
        if facture:
            return redirect('achats:detail_facture', pk=facture.pk)
        else:
            return redirect('achats:detail_bon', pk=bon_id)



# achats/views.py
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin

class FactureDetailView(LoginRequiredMixin, DetailView):
    model = FactureFournisseur
    template_name = 'achats/factures/detail.html'
    context_object_name = 'facture'

    def get_queryset(self):
        return super().get_queryset().filter(entreprise=self.request.user.entreprise)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        facture = self.object
        
        # Récupération de la devise principale
        devise_principale_symbole = "€"  # Par défaut
        try:
            from parametres.models import ConfigurationSAAS
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            if config_saas.devise_principale:
                devise_principale_symbole = config_saas.devise_principale.symbole
        except:
            pass
        
        context['devise_principale_symbole'] = devise_principale_symbole
        context['paiements'] = facture.get_paiements()
        
        return context

class FactureUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = FactureFournisseur
    form_class = FactureFournisseurForm
    template_name = 'achats/factures/form.html'
    permission_required = 'achats.change_facturefournisseur'
    success_url = reverse_lazy('achats:liste_factures')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['entreprise'] = self.request.user.entreprise
        return kwargs

from django.views.generic import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.shortcuts import get_object_or_404
from .models import PaiementFournisseur, FactureFournisseur
from .forms import PaiementFournisseurForm

class PaiementCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = PaiementFournisseur
    form_class = PaiementFournisseurForm
    template_name = 'achats/paiements/form.html'
    permission_required = 'achats.add_paiementfournisseur'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['entreprise'] = self.request.user.entreprise
        kwargs['facture_id'] = self.kwargs.get('facture_id')
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['facture'] = get_object_or_404(
            FactureFournisseur, 
            pk=self.kwargs.get('facture_id'),
            entreprise=self.request.user.entreprise
        )
        return context

    def form_valid(self, form):
        facture = get_object_or_404(
            FactureFournisseur, 
            pk=self.kwargs.get('facture_id'),
            entreprise=self.request.user.entreprise
        )
        
        paiement = form.save(commit=False)
        paiement.entreprise = self.request.user.entreprise
        paiement.facture = facture
        paiement.created_by = self.request.user
        
        # Créer l'écriture comptable si le statut est validé
        if form.cleaned_data.get('statut') == 'valide':
            paiement.statut = 'valide'
            paiement.save()
            ecriture = paiement.creer_ecriture_comptable()
            if ecriture:
                messages.success(self.request, 'Paiement enregistré et écriture comptable créée avec succès.')
            else:
                messages.warning(self.request, 'Paiement enregistré mais erreur lors de la création de l\'écriture comptable.')
        else:
            paiement.save()
            messages.success(self.request, 'Paiement enregistré avec succès.')
        
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy('achats:detail_facture', kwargs={'pk': self.kwargs.get('facture_id')})

class PaiementUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = PaiementFournisseur
    form_class = PaiementFournisseurForm
    template_name = 'achats/paiements/form.html'
    permission_required = 'achats.change_paiementfournisseur'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['entreprise'] = self.request.user.entreprise
        kwargs['facture_id'] = self.object.facture.id
        return kwargs

    def form_valid(self, form):
        paiement = form.save(commit=False)
        
        # Si le statut passe à validé, créer l'écriture comptable
        if form.cleaned_data.get('statut') == 'valide' and self.object.statut != 'valide':
            ecriture = paiement.creer_ecriture_comptable()
            if ecriture:
                messages.success(self.request, 'Paiement modifié et écriture comptable créée avec succès.')
            else:
                messages.warning(self.request, 'Paiement modifié mais erreur lors de la création de l\'écriture comptable.')
        else:
            messages.success(self.request, 'Paiement modifié avec succès.')
        
        paiement.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy('achats:detail_facture', kwargs={'pk': self.object.facture.id})
    
    
    
    
    # achats/views.py
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
from decimal import Decimal

@login_required
@permission_required('achats.add_paiementfournisseur', raise_exception=True)
def creer_paiement_direct(request, pk):
    """Vue pour créer un paiement directement depuis le détail de la facture"""
    facture = get_object_or_404(FactureFournisseur, pk=pk, entreprise=request.user.entreprise)
    
    if request.method == 'POST':
        try:
            # Validation des données
            mode_paiement = request.POST.get('mode_paiement')
            montant = Decimal(request.POST.get('montant', '0'))
            date_paiement = request.POST.get('date_paiement')
            reference = request.POST.get('reference', '')
            notes = request.POST.get('notes', '')
            
            # Validation du montant
            if montant <= 0:
                messages.error(request, "Le montant doit être supérieur à zéro.")
                return redirect('achats:detail_facture', pk=facture.pk)
            
            if montant > facture.reste_a_payer:
                messages.error(request, f"Le montant ne peut pas dépasser le reste à payer: {facture.reste_a_payer}")
                return redirect('achats:detail_facture', pk=facture.pk)
            
            # Création du paiement
            paiement = PaiementFournisseur(
                entreprise=request.user.entreprise,
                facture=facture,
                mode_paiement=mode_paiement,
                montant=montant,
                date_paiement=date_paiement,
                reference=reference,
                notes=notes,
                statut='valide',  # Statut validé par défaut pour les paiements directs
                created_by=request.user
            )
            
            paiement.save()
            
            # Création de l'écriture comptable
            ecriture = paiement.creer_ecriture_comptable()
            if ecriture:
                messages.success(request, f"Paiement de {montant} enregistré et écriture comptable créée avec succès.")
            else:
                messages.warning(request, f"Paiement enregistré mais erreur lors de la création de l'écriture comptable.")
            
            return redirect('achats:detail_facture', pk=facture.pk)
            
        except Exception as e:
            messages.error(request, f"Erreur lors de l'enregistrement du paiement: {str(e)}")
            return redirect('achats:detail_facture', pk=facture.pk)
    
    return redirect('achats:detail_facture', pk=facture.pk)

from django.views.generic import DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
# achats/views.py
class PaiementDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = PaiementFournisseur
    template_name = 'achats/paiements/confirm_delete.html'
    permission_required = 'achats.delete_paiementfournisseur'
    context_object_name = 'paiement'
    
    def get_success_url(self):
        messages.success(self.request, 'Paiement supprimé avec succès.')
        return reverse_lazy('achats:detail_facture', kwargs={'pk': self.object.facture.id})
    
    def get_queryset(self):
        return super().get_queryset().filter(entreprise=self.request.user.entreprise)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['facture'] = self.object.facture
        return context