from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.http import JsonResponse
from datetime import datetime, timedelta
from parametres.models import *
import base64
import smtplib
import datetime
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views import View
from django.utils.translation import gettext_lazy as _
from django import forms
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from django.db.models import F, Avg
from decimal import Decimal
from django.conf import settings
from datetime import datetime
from ventes.models import VentePOS, LigneVentePOS, SessionPOS, PointDeVente
from STOCK.models import Produit
from parametres.models import ConfigurationSAAS, Entreprise
from datetime import date  # ← Ajoutez cet import en haut du fichier
import datetime  # ← Gardez aussi datetime si vous l'utilisez ailleurs
import os
from .filters import CommandeFilter # Importez votre filtre
from io import BytesIO
from django.template.loader import get_template
from django.core.mail import EmailMessage
from .models import  *
import datetime # <<< AJOUTEZ CET IMPORT pour la génération du numéro
from parametres.mixins import EntrepriseAccessMixin
from STOCK.models import Produit, Client
from .forms import (
   DevisForm, LigneDevisFormSet, CommandeForm, 
    LigneCommandeFormSet, BonLivraisonForm, LigneBonLivraisonFormSet,
    FactureForm,  PaiementForm, PointDeVenteForm,
    SessionPOSForm, VentePOSForm, LigneVentePOSFormSet, PaiementPOSForm,CommandeStatutForm
)

from ventes.utils import render_to_pdf 
import logging
import logging
import datetime
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView # Ajoutez les vues nécessaires
from django.core.mail import EmailMessage
from django.conf import settings # Assurez-vous que settings est importé

# --- IMPORTS DE VOS MODÈLES ET FORMULAIRES ---
# Assurez-vous que tous les modèles utilisés sont importés ici
from .models import Devis, LigneDevis, DevisStatutHistory, DevisAuditLog # <<< NOUVEAU: Importez DevisAuditLog
from .forms import DevisForm, LigneDevisFormSet
from parametres.models import ConfigurationSAAS, Devise, Entreprise
from STOCK.models import Produit, Client
from parametres.mixins import EntrepriseAccessMixin
import logging
import datetime
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, DetailView, View
from django.utils import timezone # Import timezone for date comparisons
logger = logging.getLogger(__name__)

# ventes/views.py

import logging
import datetime
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    UpdateView,
    DeleteView,
    DetailView,
    ListView,
    View,
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.forms import inlineformset_factory
import decimal
from django.http import JsonResponse
from django.conf import settings
from django.core.mail import EmailMessage

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.urls import reverse_lazy
import logging

# Import models
from .models import Facture, LigneFacture 
from parametres.models import Entreprise 

# Import forms and the formset-getting function
from .forms import FactureForm

# Import filters
from .filters import FactureFilter


from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.utils import timezone
from django.db.models import Sum, Count, Q
from io import BytesIO
import logging
import decimal
from datetime import datetime

from .models import Facture, LigneFacture, Paiement, FactureStatutHistory, FactureAuditLog
from .forms import FactureForm, LigneFactureFormSet, PaiementForm, FactureStatutForm
from parametres.models import ConfigurationSAAS
from STOCK.models import Client, Produit
from parametres.mixins import EntrepriseAccessMixin
from .filters import FactureFilter
from .utils import render_to_pdf
from django.utils.html import strip_tags
import logging
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
from .models import Facture, LigneFacture, FactureStatutHistory, FactureAuditLog
from .forms import FactureForm, LigneFactureFormSet, FactureStatutForm
from .filters import FactureFilter
from parametres.models import ConfigurationSAAS
from django.http import HttpResponse # Importation ajoutée pour la gestion de l'envoi de PDF
from django.template.loader import render_to_string # Importation ajoutée
import weasyprint # Assurez-vous d'avoir installé WeasyPrint
from.utils import *

logger = logging.getLogger(__name__)

# --- Helper Functions & Mixins ---
def create_commande_status_history(
    commande, old_status, new_status, changed_by, comment=""
):
    try:
        CommandeStatutHistory.objects.create(
            commande=commande,
            ancien_statut=old_status,
            nouveau_statut=new_status,
            changed_by=changed_by,
            commentaire=comment,
        )
        logger.info(
            f"Historique de statut créé pour Commande {commande.numero}: {old_status or 'N/A'} -> {new_status}"
        )
    except Exception as e:
        logger.error(
            f"Erreur lors de la création de l'historique de statut pour Commande {commande.numero}: {e}",
            exc_info=True,
        )


def create_commande_audit_log(
    action, description, commande_instance=None, performed_by=None, details=None
):
    try:
        CommandeAuditLog.objects.create(
            commande=commande_instance,
            action=action,
            description=description,
            performed_by=performed_by,
            details=details,
        )
        logger.info(
            f"Audit log enregistré: Action '{action}' sur Commande {commande_instance.numero if commande_instance else 'N/A'}"
        )
    except Exception as e:
        logger.error(
            f"Erreur lors de la création du journal d'audit pour action '{action}' sur Commande {commande_instance.numero if commande_instance else 'N/A'}: {e}",
            exc_info=True,
        )


class CommandeBaseMixin:
    """
    Mixin de base pour les vues de gestion des commandes.
    """

    def get_devise_symbol(self, entreprise):
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            if config_saas.devise_principale:
                return config_saas.devise_principale.symbole
        except (ConfigurationSAAS.DoesNotExist, Devise.DoesNotExist):
            return ""
        return ""

    def log_formset_errors(self, form, formset):
        logger.error("Le formset de commande n'est PAS valide.")
        if form.errors:
            logger.error(f"Erreurs du formulaire Commande principal : {form.errors.as_json()}")
        for i, line_form in enumerate(formset):
            if line_form.errors:
                logger.error(
                    f"Erreurs de la ligne de formset {i} : {line_form.errors.as_json()}"
                )
            if line_form.non_field_errors():
                logger.error(
                    f"Erreurs non-champ de la ligne de formset {i} : {line_form.non_field_errors()}"
                )
            if line_form.cleaned_data.get("DELETE") and line_form.errors:
                logger.warning(
                    f"Ligne de formset {i} marquée pour suppression a toujours des erreurs : {line_form.errors.as_json()}"
                )

    def generate_commande_number(self):
        if not self.object.numero:
            today_str = datetime.date.today().strftime("%Y%m%d")
            last_commande = (
                Commande.objects.filter(
                    entreprise=self.request.entreprise, created_at__date=datetime.date.today()
                )
                .order_by("-numero")
                .first()
            )
            sequence = 1
            if last_commande:
                try:
                    parts = last_commande.numero.split("-")
                    if len(parts) == 3 and parts[1] == today_str:
                        last_sequence = int(parts[2])
                        sequence = last_sequence + 1
                except (ValueError, IndexError):
                    pass
            self.object.numero = f"CMD-{today_str}-{sequence:03d}"
            while Commande.objects.filter(
                numero=self.object.numero, entreprise=self.request.entreprise
            ).exists():
                sequence += 1
                self.object.numero = f"CMD-{today_str}-{sequence:03d}"


# ==================== VUES DE GESTION DES COMMANDES ====================

class CommandeCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, CommandeBaseMixin, CreateView
):
    model = Commande
    form_class = CommandeForm
    template_name = "ventes/commandes/form.html"
    permission_required = "ventes.add_commande"

    def get_initial(self):
        initial = super().get_initial()
        # Pré-remplir avec le devis si spécifié dans l'URL
        devis_id = self.request.GET.get('devis_id')
        if devis_id:
            try:
                devis = Devis.objects.get(id=devis_id, entreprise=self.request.entreprise)
                initial['devis'] = devis
                initial['client'] = devis.client
                initial['date'] = timezone.now().date()
            except Devis.DoesNotExist:
                pass
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["entreprise"] = self.request.entreprise
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.entreprise
        formset_form_kwargs = {"entreprise": entreprise}

        # Vérifier si on vient d'un devis
        devis_id = self.request.GET.get('devis_id')
        initial_formset_data = []
        
        if devis_id and not self.request.POST:
            try:
                devis = Devis.objects.get(id=devis_id, entreprise=entreprise)
                # Pré-remplir le formset avec les lignes du devis
                for ligne in devis.lignes.all():
                    initial_formset_data.append({
                        'produit': ligne.produit,
                        'quantite': ligne.quantite,
                        'prix_unitaire': ligne.prix_unitaire,
                        'taux_tva': ligne.taux_tva,
                    })
            except Devis.DoesNotExist:
                pass

        if self.request.POST:
            context["formset"] = LigneCommandeFormSet(
                self.request.POST,
                instance=self.object if hasattr(self, "object") else None,
                prefix="form",
                form_kwargs=formset_form_kwargs,
            )
        else:
            # Pré-remplir le formset avec les données du devis
            context["formset"] = LigneCommandeFormSet(
                instance=self.object if hasattr(self, "object") else None,
                prefix="form",
                form_kwargs=formset_form_kwargs,
                initial=initial_formset_data
            )

        context["devise_principale_symbole"] = self.get_devise_symbol(entreprise)
        context["from_devis"] = devis_id is not None
        return context

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        formset = context["formset"]

        if not formset.is_valid():
            self.log_formset_errors(form, formset)
            messages.error(self.request, "Veuillez corriger les erreurs dans les articles de la commande.")
            return self.render_to_response(self.get_context_data(form=form, formset=formset))

        with transaction.atomic():
            self.object = form.save(commit=False)
            self.object.entreprise = self.request.entreprise
            self.object.created_by = self.request.user

            if self.object.devis:
                self.object.statut = "confirme"
            else:
                self.object.statut = "brouillon"

            self.generate_commande_number()
            self.object.save()
            formset.instance = self.object
            formset.save()

            self.object.total_ht = sum((item.montant_ht for item in self.object.items.all()), 0)
            self.object.total_tva = sum((item.montant_tva for item in self.object.items.all()), 0)
            self.object.total_ttc = self.object.total_ht + self.object.total_tva
            self.object.save(update_fields=["total_ht", "total_tva", "total_ttc"])

            if self.object.devis:
                create_commande_audit_log(
                    action="conversion_devis",
                    description=f"Commande #{self.object.numero} créée à partir du devis #{self.object.devis.numero}.",
                    commande_instance=self.object,
                    performed_by=self.request.user,
                    details={
                        "devis_id": self.object.devis.pk,
                        "devis_numero": self.object.devis.numero,
                    },
                )

            create_commande_status_history(
                commande=self.object,
                old_status=None,
                new_status=self.object.statut,
                changed_by=self.request.user,
                comment="Commande créée et statut initial défini.",
            )

            create_commande_audit_log(
                action="creation",
                description=f"Commande #{self.object.numero} créée.",
                commande_instance=self.object,
                performed_by=self.request.user,
            )

            messages.success(self.request, "Commande créée avec succès.")
            return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("ventes:commande_detail", kwargs={"pk": self.object.pk})


from django.http import JsonResponse
from django.views.decorators.http import require_GET

@require_GET
def get_devis_lignes(request, devis_id):
    try:
        devis = Devis.objects.get(id=devis_id, entreprise=request.entreprise)
        lignes = []
        
        for ligne in devis.lignes.all():
            lignes.append({
                'produit_id': ligne.produit.id,
                'produit_nom': str(ligne.produit),
                'quantite': float(ligne.quantite),
                'prix_unitaire': float(ligne.prix_unitaire),
                'taux_tva': float(ligne.taux_tva),
            })
        
        return JsonResponse({
            'success': True,
            'lignes': lignes,
            'client_id': devis.client.id if devis.client else None
        })
        
    except Devis.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Devis non trouvé'})






class CommandeUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, CommandeBaseMixin, UpdateView
):
    model = Commande
    form_class = CommandeForm
    template_name = "ventes/commandes/form.html"
    permission_required = "ventes.change_commande"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["entreprise"] = self.request.entreprise
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.entreprise
        formset_form_kwargs = {"entreprise": entreprise}

        if self.request.POST:
            context["formset"] = LigneCommandeFormSet(
                self.request.POST,
                instance=self.object,
                prefix="form",
                form_kwargs=formset_form_kwargs,
            )
        else:
            context["formset"] = LigneCommandeFormSet(
                instance=self.object,
                prefix="form",
                form_kwargs=formset_form_kwargs,
            )

        context["devise_principale_symbole"] = self.get_devise_symbol(entreprise)
        return context

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        formset = context["formset"]
        old_status = self.object.statut

        if not formset.is_valid():
            self.log_formset_errors(form, formset)
            messages.error(self.request, "Veuillez corriger les erreurs dans les articles de la commande.")
            return self.render_to_response(self.get_context_data(form=form, formset=formset))

        with transaction.atomic():
            self.object = form.save(commit=False)
            self.object.save()
            formset.instance = self.object
            formset.save()

            self.object.total_ht = sum((item.montant_ht for item in self.object.items.all()), 0)
            self.object.total_tva = sum((item.montant_tva for item in self.object.items.all()), 0)
            self.object.total_ttc = self.object.total_ht + self.object.total_tva
            self.object.save(update_fields=["total_ht", "total_tva", "total_ttc"])

            create_commande_audit_log(
                action="modification",
                description=f"Commande #{self.object.numero} modifiée.",
                commande_instance=self.object,
                performed_by=self.request.user,
            )

            if self.object.statut != old_status:
                create_commande_status_history(
                    commande=self.object,
                    old_status=old_status,
                    new_status=self.object.statut,
                    changed_by=self.request.user,
                    comment="Statut modifié via le formulaire d'édition.",
                )
                create_commande_audit_log(
                    action="changement_statut",
                    description=f"Statut de Commande #{self.object.numero} changé de '{old_status}' à '{self.object.statut}'.",
                    commande_instance=self.object,
                    performed_by=self.request.user,
                    details={"old_status": old_status, "new_status": self.object.statut},
                )

            messages.success(self.request, "Commande modifiée avec succès.")
            return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("ventes:commande_detail", kwargs={"pk": self.object.pk})


class CommandeDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DeleteView
):
    model = Commande
    template_name = "ventes/commandes/confirm_delete.html"
    success_url = reverse_lazy("ventes:commande_list")
    permission_required = "ventes.delete_commande"

    def form_valid(self, form):
        commande_info = f"Commande #{self.object.numero} (ID: {self.object.pk})"
        with transaction.atomic():
            response = super().form_valid(form)
            create_commande_audit_log(
                action="suppression",
                description=f"{commande_info} supprimée.",
                commande_instance=None,
                performed_by=self.request.user,
                details={"commande_id": self.object.pk, "commande_numero": self.object.numero},
            )
            messages.success(self.request, f"Commande {commande_info} supprimée avec succès.")
            return response


class CommandeStatutUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, UpdateView
):
    model = Commande
    form_class = CommandeStatutForm
    template_name = "ventes/commandes/change_status.html"
    permission_required = "ventes.change_commande"

    def get_success_url(self):
        return reverse_lazy("ventes:commande_detail", kwargs={"pk": self.object.pk})

    def form_valid(self, form):
        new_status = form.cleaned_data["statut"]
        commentaire = form.cleaned_data["commentaire"]

        try:
            old_status = self.object.statut
            # Update the status directly on the object and save
            self.object.statut = new_status
            self.object.save(update_fields=["statut"])

            create_commande_status_history(
                commande=self.object,
                old_status=old_status,
                new_status=new_status,
                changed_by=self.request.user,
                comment=commentaire,
            )

            create_commande_audit_log(
                action="changement_statut",
                description=f"Statut de Commande #{self.object.numero} changé de '{old_status}' à '{new_status}'.",
                commande_instance=self.object,
                performed_by=self.request.user,
                details={"old_status": old_status, "new_status": new_status},
            )

            messages.success(
                self.request,
                f"Statut de la commande #{self.object.numero} mis à jour à '{self.object.get_statut_display()}'."
            )
            return super().form_valid(form)
        except ValueError as e:
            messages.error(self.request, f"Erreur lors du changement de statut : {e}")
            return self.form_invalid(form)


class CommandeDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DetailView
):
    model = Commande
    template_name = "ventes/commandes/detail.html"
    permission_required = "ventes.view_commande"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_history"] = self.object.status_history.all()
        context["audit_logs"] = self.object.audit_logs.all()
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.object.entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else ''
            context["devise_principale_symbole"] = devise_symbole
        except ConfigurationSAAS.DoesNotExist:
            context["devise_principale_symbole"] = ''
        return context


class CommandeCancelView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, View):
    permission_required = "ventes.change_commande"

    def post(self, request, pk, *args, **kwargs):
        commande = get_object_or_404(Commande, pk=pk, entreprise=request.entreprise)
        if commande.statut in ["annule", "livre", "rembourse"]:
            messages.error(
                request,
                f"La commande #{commande.numero} ne peut pas être annulée car elle est déjà '{commande.get_statut_display()}'."
            )
        else:
            old_status = commande.statut
            with transaction.atomic():
                commande.statut = "annule"
                commande.save(update_fields=["statut"])
                create_commande_status_history(
                    commande=commande,
                    old_status=old_status,
                    new_status="annule",
                    changed_by=request.user,
                    comment="Commande annulée manuellement par l'utilisateur.",
                )
                create_commande_audit_log(
                    action="changement_statut",
                    description=f"Commande #{commande.numero} annulée. Statut changé de '{old_status}' à 'annule'.",
                    commande_instance=commande,
                    performed_by=request.user,
                    details={"old_status": old_status, "new_status": "annule"},
                )
                messages.success(request, f"La commande #{commande.numero} a été annulée avec succès.")

        return redirect("ventes:commande_detail", pk=pk)


class CommandeAuditLogListView(
    LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, ListView
):
    model = CommandeAuditLog
    template_name = "ventes/commandes/audit_log_list.html"
    context_object_name = "audit_logs"
    permission_required = "ventes.view_audit_log"
    paginate_by = 25

    def get_queryset(self):
        return CommandeAuditLog.objects.filter(commande__entreprise=self.request.entreprise).order_by(
            "-performed_at"
        )


class CommandeListView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, ListView):
    model = Commande
    template_name = "ventes/commandes/list.html"
    context_object_name = "commandes"
    permission_required = "ventes.view_commande"
    paginate_by = 10

    def get_queryset(self):
        queryset = Commande.objects.filter(entreprise=self.request.entreprise).order_by(
            "-created_at"
        )
        self.filterset = CommandeFilter(self.request.GET, queryset=queryset, request=self.request)
        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["filter"] = self.filterset
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.entreprise)
            context["devise_principale_symbole"] = (
                config_saas.devise_principale.symbole if config_saas.devise_principale else ""
            )
        except (ConfigurationSAAS.DoesNotExist, Devise.DoesNotExist):
            context["devise_principale_symbole"] = ""
        return context


class CommandePrintView(
    LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DetailView
):
    model = Commande
    template_name = "ventes/commandes/print.html"
    context_object_name = "commande"
    permission_required = "ventes.view_commande"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.entreprise
        devise_principale_symbole = ""
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            if config_saas.devise_principale:
                devise_principale_symbole = config_saas.devise_principale.symbole
        except (ConfigurationSAAS.DoesNotExist, Devise.DoesNotExist):
            logger.warning(
                f"ConfigurationSAAS ou Devise principale non trouvée pour l'entreprise {entreprise.nom}"
            )
        context["devise_principale_symbole"] = devise_principale_symbole
        context["entreprise_info"] = entreprise
        context["now"] = timezone.now()
        context["created_by_user"] = (
            self.object.created_by.username if self.object.created_by else "N/A"
        )
        return context


def send_commande_pdf_email(commande, recipient_email):
    """
    Fonction utilitaire pour envoyer le PDF de la commande par e-mail.
    """
    try:
        pdf_context = {
            "commande": commande,
            "entreprise": commande.entreprise,
            "client": commande.client,
            "devise_principale_symbole": (
                commande.entreprise.configuration_saas.devise_principale.symbole
                if hasattr(commande.entreprise, 'configuration_saas') and commande.entreprise.configuration_saas.devise_principale
                else ""
            ),
        }
        pdf = render_to_pdf("ventes/commandes/print.html", pdf_context)
        if not pdf:
            logger.error(
                f"La génération du PDF a échoué pour la commande {commande.numero}. L'e-mail ne peut pas être envoyé."
            )
            return False

        subject = f"Votre bon de commande #{commande.numero} de {commande.entreprise.nom}"
        message = f"""Cher(e) {commande.client.nom},

Veuillez trouver ci-joint votre bon de commande numéro {commande.numero} pour votre examen.

Date de la commande : {commande.date.strftime('%d/%m/%Y')}
Montant total TTC : {commande.total_ttc} {pdf_context['devise_principale_symbole']}

N'hésitez pas à nous contacter si vous avez des questions.

Cordialement,

L'équipe de {commande.entreprise.nom}
"""
        from_email = settings.DEFAULT_FROM_EMAIL
        email = EmailMessage(
            subject,
            message,
            from_email,
            [recipient_email],
        )
        email.attach(f"commande_{commande.numero}.pdf", pdf, "application/pdf")
        email.send()
        logger.info(
            f"Bon de commande {commande.numero} envoyé avec succès par e-mail au client {recipient_email}."
        )
        return True
    except Exception as e:
        logger.error(
            f"Échec critique de l'envoi de l'e-mail pour la commande {commande.numero}: {str(e)}",
            exc_info=True,
        )
        return False


class CommandeSendEmailView(
    LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, View
):
    permission_required = "ventes.change_commande"

    def post(self, request, pk, *args, **kwargs):
        commande = get_object_or_404(Commande, pk=pk, entreprise=request.entreprise)
        recipient_email = commande.client.email
        if not recipient_email:
            messages.error(request, "L'adresse e-mail du client n'est pas renseignée.")
            return redirect("ventes:commande_detail", pk=pk)

        if send_commande_pdf_email(commande, recipient_email):
            messages.success(
                request,
                f"Le bon de commande #{commande.numero} a été envoyé à {recipient_email} avec succès.",
            )
        else:
            messages.error(request, f"Échec de l'envoi du bon de commande #{commande.numero} par e-mail.")

        return redirect("ventes:commande_detail", pk=pk)
    
# ventes/views.py
# ventes/views.py
import logging 
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
# Il est crucial d'importer les modèles que vous utilisez dans la vue
from .models import  * 

logger = logging.getLogger(__name__)

def get_client_info(request, client_id):
    """
    Vue AJAX pour récupérer les informations d'un client.
    """
    try:
        # Tente de trouver le client par son ID
        client = get_object_or_404(Client, pk=client_id)
        
        # Récupère la devise liée au client.
        # La condition `if client.devise else None` gère le cas où la devise est nulle.
        devise_symbole = client.devise.symbole if client.devise else None
        
        # Prépare la réponse JSON
        data = {
            'success': True,
            'devise_symbole': devise_symbole,
        }
        return JsonResponse(data)
    except Client.DoesNotExist:
        # Si le client n'est pas trouvé, renvoie une erreur 404
        return JsonResponse({'success': False, 'error': 'Client not found'}, status=404)
    except Exception as e:
        # En cas d'autre erreur (comme un problème avec l'attribut `symbole`),
        # le logger enregistre le détail de l'erreur dans la console de votre serveur.
        logger.error(f"Erreur lors de la récupération des informations du client : {e}")
        return JsonResponse({'success': False, 'error': 'Internal server error'}, status=500)
   
from .utils import convert_devis_to_commande

logger = logging.getLogger(__name__)

# ... (Your existing CommandeDetailView, CommandePrintView, etc.) ...
class DevisConvertView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, View):
    permission_required = 'ventes.add_commande'

    def post(self, request, pk, *args, **kwargs):
        devis = get_object_or_404(Devis, pk=pk, entreprise=request.entreprise)

        # Vérifier que le devis peut être converti
        if devis.statut != 'accepte':
            messages.error(
                request, 
                f"Seuls les devis acceptés peuvent être convertis en commande. Statut actuel: {devis.get_statut_display()}"
            )
            return redirect('ventes:devis_detail', pk=devis.pk)

        new_commande, error_message = convert_devis_to_commande(devis.pk, request.user)

        if new_commande:
            messages.success(
                request, 
                f"Le devis #{devis.numero} a été converti en commande #{new_commande.numero} avec succès."
            )
            return redirect('ventes:commande_detail', pk=new_commande.pk)
        else:
            messages.error(
                request, 
                error_message or f"Impossible de convertir le devis #{devis.numero} en commande."
            )
            return redirect('ventes:devis_detail', pk=devis.pk)
# ventes/views.py


class PointDeVenteCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = PointDeVente
    form_class = PointDeVenteForm
    template_name = 'ventes/pos/form.html'
    permission_required = 'ventes.add_pointdevente'
    success_url = reverse_lazy('ventes:pos_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['entreprise'] = self.request.user.entreprise
        return kwargs

    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Créer l'instance manuellement sans passer par form.save()
                point_de_vente = PointDeVente(
                    entreprise=self.request.user.entreprise,
                    code=form.cleaned_data['code'],
                    nom=form.cleaned_data['nom'],
                    adresse=form.cleaned_data['adresse'],
                    actif=form.cleaned_data['actif']
                )
                
                # Sauvegarder d'abord l'instance de base
                point_de_vente.save()
                
                # Ensuite assigner le responsable et les caissiers
                if form.cleaned_data.get('responsable'):
                    point_de_vente.responsable = form.cleaned_data['responsable']
                    point_de_vente.save()
                
                if form.cleaned_data.get('caissiers'):
                    point_de_vente.caissiers.set(form.cleaned_data['caissiers'])
                
                self.object = point_de_vente
                
                messages.success(self.request, 
                    f"Point de vente {self.object.nom} créé avec succès"
                )
                return redirect(self.get_success_url())
                
        except Exception as e:
            messages.error(self.request, f"Erreur lors de la création: {str(e)}")
            return self.form_invalid(form)

class PointDeVenteUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = PointDeVente
    form_class = PointDeVenteForm
    template_name = 'ventes/pos/form.html'
    permission_required = 'ventes.change_pointdevente'
    success_url = reverse_lazy('ventes:pos_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['entreprise'] = self.request.user.entreprise
        return kwargs

    def get_queryset(self):
        return PointDeVente.objects.filter(entreprise=self.request.user.entreprise)

    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Mettre à jour les champs de base
                self.object.code = form.cleaned_data['code']
                self.object.nom = form.cleaned_data['nom']
                self.object.adresse = form.cleaned_data['adresse']
                self.object.actif = form.cleaned_data['actif']
                self.object.save()
                
                # Mettre à jour les relations
                if form.cleaned_data.get('responsable'):
                    self.object.responsable = form.cleaned_data['responsable']
                    self.object.save()
                
                if form.cleaned_data.get('caissiers'):
                    self.object.caissiers.set(form.cleaned_data['caissiers'])
                
                messages.success(self.request, 
                    f"Point de vente {self.object.nom} modifié avec succès"
                )
                return redirect(self.get_success_url())
                
        except Exception as e:
            messages.error(self.request, f"Erreur lors de la modification: {str(e)}")
            return self.form_invalid(form)# ventes/views.py

class PointDeVenteListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = PointDeVente
    template_name = 'ventes/pos/liste.html'
    permission_required = 'ventes.view_pointdevente'
    context_object_name = 'points_de_vente'

    def get_queryset(self):
        # Utiliser la méthode du modèle pour obtenir les POS accessibles
        return self.request.user.get_accessible_pos().select_related('responsable').prefetch_related('caissiers')

from django.core.exceptions import PermissionDenied

class PointDeVenteDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = PointDeVente
    template_name = 'ventes/pos/detail.html'
    permission_required = 'ventes.view_pointdevente'
    context_object_name = 'pos'

    def get_queryset(self):
        # Filtrer par POS accessibles
        return self.request.user.get_accessible_pos()

    def dispatch(self, request, *args, **kwargs):
        # Vérification supplémentaire d'accès
        obj = self.get_object()
        if not request.user.can_access_pos(obj):
            raise PermissionDenied("Vous n'avez pas accès à ce point de vente")
        return super().dispatch(request, *args, **kwargs)



from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import Coalesce, TruncDate, TruncMonth, TruncHour
from django.utils import timezone
from decimal import Decimal

# Import your models
from parametres.models import ConfigurationSAAS, Devise
from ventes.models import VentePOS, SessionPOS

class CaissierDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'ventes/pos/caissier_dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.role != 'CAISSIER':
            raise PermissionDenied("Accès réservé aux caissiers")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # --- Add currency retrieval here ---
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=user.entreprise)
            context['devise_symbole'] = config_saas.devise_principale.symbole if config_saas.devise_principale else ''
        except (ConfigurationSAAS.DoesNotExist, Devise.DoesNotExist):
            context['devise_symbole'] = ''
        
        # Récupérer le POS principal
        context['main_pos'] = user.get_main_pos() or user.get_assigned_pos().first()
        context['all_pos'] = user.get_assigned_pos()
        
        # Vérifier les sessions ouvertes
        if context['main_pos']:
            session_ouverte = SessionPOS.objects.filter(
                point_de_vente=context['main_pos'],
                utilisateur=user,
                statut='ouverte'
            ).first()
            
            context['session_ouverte'] = session_ouverte
            
            # Statistiques du jour
            aujourd_hui = timezone.now().date()
            ventes_aujourdhui = VentePOS.objects.filter(
                session__point_de_vente=context['main_pos'],
                session__utilisateur=user,
                date__date=aujourd_hui
            )
            
            context['nombre_ventes'] = ventes_aujourdhui.count()
            
            # Calcul manuel du chiffre d'affaires
            chiffre_affaires = Decimal('0.00')
            for vente in ventes_aujourdhui:
                chiffre_affaires += vente.total_ttc
            
            context['chiffre_affaires'] = chiffre_affaires
        
        return context



User = get_user_model()

class CaissierListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = User
    template_name = 'ventes/pos/caissiers.html'
    permission_required = 'ventes.view_pointdevente'
    context_object_name = 'caissiers'
    
    def get_queryset(self):
        # Retourne seulement les caissiers de l'entreprise avec leurs POS préchargés
        return User.objects.filter(
            entreprise=self.request.user.entreprise,
            role='CAISSIER'  # Note: majuscules si c'est comme ça dans votre modèle
        ).prefetch_related('pos_caissiers')  # Précharger les relations ManyToMany
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ajouter les POS avec leurs caissiers préchargés
        context['points_de_vente'] = PointDeVente.objects.filter(
            entreprise=self.request.user.entreprise
        ).prefetch_related('caissiers').select_related('responsable')
        return context
    
    
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required

User = get_user_model()

@login_required
@require_GET
def get_caissier_info(request):
    caissier_id = request.GET.get('caissier_id')
    
    try:
        caissier = User.objects.get(
            id=caissier_id,
            entreprise=request.user.entreprise,
            role='caissier'
        )
        
        return JsonResponse({
            'success': True,
            'full_name': caissier.get_full_name(),
            'email': caissier.email,
            'role_display': caissier.get_role_display()
        })
        
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Caissier non trouvé'
        })  
    
    
    
    
    
class PointDeVenteDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = PointDeVente
    template_name = 'ventes/pos/confirm_delete.html'
    permission_required = 'ventes.delete_pointdevente'
    success_url = reverse_lazy('ventes:pos_list')

    def get_queryset(self):
        return PointDeVente.objects.filter(entreprise=self.request.user.entreprise)

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Point de vente supprimé avec succès")
        return super().delete(request, *args, **kwargs)
    


# Ensure these imports are correct based on your project structure
from .models import (
    BonLivraison, LigneBonLivraison,
    BonLivraisonStatutHistory, BonLivraisonAuditLog,
    Commande
)
from .forms import BonLivraisonForm, LigneBonLivraisonFormSet
# from parametres.models import ConfigurationSAAS, Devise
# from STOCK.Client import Client
# Import your FilterSets
from .filters import CommandeFilter, BonLivraisonFilter 
logger = logging.getLogger(__name__)

# --- Your existing BonLivraison Views (Revised) ---
# --- BonLivraisonListView (Updated) ---
class BonLivraisonListView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, ListView):
    model = BonLivraison
    template_name = 'ventes/livraisons/liste.html'
    context_object_name = 'bons_livraison'
    permission_required = 'ventes.view_bonlivraison'
    paginate_by = 10

    def get_queryset(self):
        # 1. Filter first by the user's enterprise
        queryset = BonLivraison.objects.filter(entreprise=self.request.entreprise).order_by('-date', '-created_at')

        # 2. Apply advanced search filters using django-filter
        self.filterset = BonLivraisonFilter(self.request.GET, queryset=queryset, request=self.request)
        
        # Log applied filters
        logger.info(f"BonLivraison filters applied by {self.request.user}: {self.request.GET.urlencode()}")
        
        return self.filterset.qs # Return the filtered queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass the filter object to the template
        context['filter'] = self.filterset 
        
        # For displaying the currency symbol in the list if needed
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.entreprise)
            context['devise_principale_symbole'] = config_saas.devise_principale.symbole if config_saas.devise_principale else ''
        except (ConfigurationSAAS.DoesNotExist, Devise.DoesNotExist):
            logger.warning(f"ConfigurationSAAS or primary currency not found for enterprise {self.request.entreprise.nom} when displaying delivery notes.")
            context['devise_principale_symbole'] = ''

        return context


# ventes/views.py
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
import logging
from decimal import Decimal




logger = logging.getLogger(__name__)


# --- Fonctions utilitaires pour la gestion du stock ---
# RENOMMÉ request_user EN request_obj POUR ACCEPTER L'OBJET HttpRequest
def update_stock_on_delivery(bon_livraison_lines, request_obj, action_type='out'):
    """
    Met à jour le stock des produits en fonction des lignes de bon de livraison.
    request_obj doit être l'objet HttpRequest pour les messages.
    action_type='out' pour une sortie (création/modification qui réduit le stock)
    action_type='in' pour une entrée (suppression/annulation qui augmente le stock)
    """
    for ligne_bl in bon_livraison_lines:
        produit = ligne_bl.produit
        quantite_change = ligne_bl.quantite

        # Convertir quantite_change en Decimal pour éviter les erreurs de type
        if not isinstance(quantite_change, Decimal):
            quantite_change = Decimal(str(quantite_change))

        if action_type == 'out':
            # Réduction du stock
            if produit.stock is not None:
                # La vérification préalable au niveau du form_valid est meilleure,
                # mais ici on s'assure de ne pas avoir de stock négatif si possible.
                if produit.stock >= quantite_change:
                    produit.stock -= quantite_change
                    produit.save(update_fields=['stock'])
                    messages.info(request_obj, f"Stock du produit '{produit.nom}' mis à jour. Nouvelle quantité: {produit.stock}")
                else:
                    # Permet le stock négatif ici si la validation précédente n'a pas empêché
                    messages.warning(request_obj, f"Attention: Stock insuffisant pour '{produit.nom}'. Livré: {quantite_change}, Actuel: {produit.stock}. Stock sera négatif.")
                    produit.stock -= quantite_change
                    produit.save(update_fields=['stock'])
            else:
                messages.warning(request_obj, f"Le produit '{produit.nom}' n'a pas de stock défini. Stock non mis à jour à la sortie.")
        elif action_type == 'in':
            # Augmentation du stock
            if produit.stock is not None:
                produit.stock += quantite_change
                produit.save(update_fields=['stock'])
                messages.info(request_obj, f"Stock du produit '{produit.nom}' remis à jour suite à annulation/suppression. Nouvelle quantité: {produit.stock}")
            else:
                messages.warning(request_obj, f"Le produit '{produit.nom}' n'a pas de stock défini. Stock non remis à jour à l'entrée.")


# --- Vues BonLivraison ---

class BonLivraisonCreateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, CreateView):
    model = BonLivraison
    form_class = BonLivraisonForm
    template_name = 'ventes/livraisons/form.html'
    permission_required = 'ventes.add_bonlivraison'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = LigneBonLivraisonFormSet(
                self.request.POST,
                instance=self.object,
                form_kwargs={'entreprise': self.request.entreprise}
            )
        else:
            context['formset'] = LigneBonLivraisonFormSet(
                instance=None,
                form_kwargs={'entreprise': self.request.entreprise}
            )
        return context

    def form_valid(self, form):
        with transaction.atomic():
            form.instance.entreprise = self.request.entreprise
            form.instance.created_by = self.request.user

            context = self.get_context_data(form=form)
            formset = context['formset']

            if formset.is_valid():
                # --- VÉRIFICATION DE STOCK AVANT DE SAUVEGARDER ---
                stock_issues = []
                for ligne_form in formset:
                    # Traite seulement les formulaires qui sont soumis et non marqués pour suppression
                    if ligne_form.has_changed() and not ligne_form.cleaned_data.get('DELETE'):
                        produit = ligne_form.cleaned_data.get('produit')
                        quantite_demandee = ligne_form.cleaned_data.get('quantite')

                        if produit and quantite_demandee is not None:
                            produit.refresh_from_db() # Assurez-vous que le stock est à jour depuis la base de données
                            if produit.stock < quantite_demandee:
                                stock_issues.append(f"Stock insuffisant pour '{produit.nom}'. Demandé: {quantite_demandee}, Disponible: {produit.stock}.")
                
                if stock_issues:
                    for issue in stock_issues:
                        messages.error(self.request, issue)
                    return self.render_to_response(self.get_context_data(form=form))
                # --- FIN VÉRIFICATION DE STOCK ---

                self.object = form.save()
                formset.instance = self.object
                saved_lines = formset.save() # Sauvegarde les lignes du bon de livraison

                # --- MISE À JOUR DU STOCK LORS DE LA CRÉATION (SORTIE) ---
                # PASSE self.request À LA FONCTION
                update_stock_on_delivery(saved_lines, self.request, action_type='out')
                # --- FIN MISE À JOUR DU STOCK ---

                BonLivraisonAuditLog.objects.create(
                    bon_livraison=self.object,
                    action='creation',
                    description=f"Bon de livraison #{self.object.numero} créé.",
                    performed_by=self.request.user,
                    details={'commande_id': self.object.commande.pk if self.object.commande else None}
                )

                messages.success(self.request, f"Bon de livraison #{self.object.numero} créé avec succès et stock mis à jour.")
                return redirect(self.get_success_url())
            else:
                messages.error(self.request, "Veuillez corriger les erreurs dans les articles du bon de livraison.")
                return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('ventes:livraison_detail', kwargs={'pk': self.object.pk})



class CommandeConvertToBLView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, View):
    permission_required = 'ventes.add_bonlivraison'

    def post(self, request, pk, *args, **kwargs):
        try:
            commande = get_object_or_404(Commande, pk=pk, entreprise=request.entreprise)

            # Vérification supplémentaire côté vue
            if not can_convert_commande(commande):
                messages.error(request, get_commande_conversion_error_message(commande))
                return redirect('ventes:commande_detail', pk=commande.pk)

            new_bon_livraison, error_message = convert_commande_to_bon_livraison(commande.pk, request.user)

            if new_bon_livraison:
                messages.success(
                    request, 
                    f"✅ La commande #{commande.numero} a été convertie en bon de livraison #{new_bon_livraison.numero} avec succès."
                )
                return redirect('ventes:livraison_detail', pk=new_bon_livraison.pk)
            else:
                messages.error(request, error_message or "Erreur lors de la conversion.")
                return redirect('ventes:commande_detail', pk=commande.pk)
                
        except Exception as e:
            messages.error(request, f"Erreur critique: {str(e)}")
            return redirect('ventes:commande_detail', pk=pk)


class BonLivraisonDetailView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DetailView):
    model = BonLivraison
    template_name = 'ventes/livraisons/detail.html'
    context_object_name = 'bon_livraison'
    permission_required = 'ventes.view_bonlivraison'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bon_livraison = self.get_object()

        devise_principale_symbole = ''
        try:
            from parametres.models import ConfigurationSAAS, Devise
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.entreprise)
            if config_saas.devise_principale:
                devise_principale_symbole = config_saas.devise_principale.symbole
        except (ImportError, ConfigurationSAAS.DoesNotExist, Devise.DoesNotExist):
            logger.warning(f"ConfigurationSAAS ou Devise principale non trouvée pour l'entreprise {self.request.entreprise.nom}")

        context['devise_principale_symbole'] = devise_principale_symbole
        context['entreprise_info'] = self.request.entreprise
        context['current_datetime'] = timezone.now() # Pour la vue d'impression

        context['status_history'] = bon_livraison.status_history.all()
        context['audit_logs'] = bon_livraison.audit_logs.all()

        return context
class BonLivraisonUpdateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, UpdateView):
    model = BonLivraison
    form_class = BonLivraisonForm
    template_name = 'ventes/livraisons/form.html'
    permission_required = 'ventes.change_bonlivraison'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = LigneBonLivraisonFormSet(
                self.request.POST,
                instance=self.object,
                form_kwargs={'entreprise': self.request.entreprise}
            )
        else:
            context['formset'] = LigneBonLivraisonFormSet(
                instance=self.object,
                form_kwargs={'entreprise': self.request.entreprise}
            )
        return context

    def form_valid(self, form):
        with transaction.atomic():
            old_status = self.object.statut if 'statut' in form.changed_data else None

            # Récupérer les anciennes quantités AVANT de sauvegarder
            old_lines_quantities = {
                item.produit_id: item.quantite
                for item in self.object.items.all()
            }
            
            # Sauvegarder le formulaire principal
            self.object = form.save()
            context = self.get_context_data(form=form)
            formset = context['formset']
            
            if formset.is_valid():
                # --- VÉRIFICATION DE STOCK AVANT DE SAUVEGARDER ---
                stock_issues = []
                
                for ligne_form in formset:
                    if ligne_form.has_changed() and not ligne_form.cleaned_data.get('DELETE'):
                        produit = ligne_form.cleaned_data.get('produit')
                        quantite_demandee = ligne_form.cleaned_data.get('quantite')
                        ligne_bl_instance = ligne_form.instance

                        if produit and quantite_demandee is not None:
                            produit.refresh_from_db()

                            if ligne_bl_instance.pk: # Ligne existante modifiée
                                old_quantite_for_product = old_lines_quantities.get(produit.pk, Decimal('0'))
                                net_change = quantite_demandee - old_quantite_for_product
                                if net_change > 0 and produit.stock < net_change:
                                    stock_issues.append(f"Stock insuffisant pour '{produit.nom}'. Augmentation demandée: {net_change}, Disponible: {produit.stock}.")
                            else: # Nouvelle ligne
                                if produit.stock < quantite_demandee:
                                    stock_issues.append(f"Stock insuffisant pour '{produit.nom}'. Demandé: {quantite_demandee}, Disponible: {produit.stock}.")
                
                if stock_issues:
                    for issue in stock_issues:
                        messages.error(self.request, issue)
                    return self.render_to_response(self.get_context_data(form=form))
                # --- FIN VÉRIFICATION DE STOCK ---

                # CORRECTION ICI : Gérer les lignes supprimées différemment
                instances_to_save = []
                instances_to_delete = []
                
                for ligne_form in formset:
                    if ligne_form.cleaned_data.get('DELETE') and ligne_form.instance.pk:
                        # Marquer pour suppression + retour stock
                        instances_to_delete.append(ligne_form.instance)
                    elif ligne_form.has_changed():
                        instances_to_save.append(ligne_form)

                # 1. D'abord traiter les suppressions (retour au stock)
                for instance in instances_to_delete:
                    update_stock_on_delivery([instance], self.request, action_type='in')
                    instance.delete()

                # 2. Ensuite traiter les modifications et ajouts
                for ligne_form in instances_to_save:
                    ligne_bl = ligne_form.save(commit=False)
                    produit = ligne_bl.produit
                    nouvelle_quantite = ligne_bl.quantite
                    
                    if ligne_bl.pk: # Ligne existante modifiée
                        ancienne_quantite = old_lines_quantities.get(produit.pk, Decimal('0'))
                        difference = nouvelle_quantite - ancienne_quantite
                        
                        if difference > 0: # Quantité augmentée
                            update_stock_on_delivery(
                                [type('obj', (), {'produit': produit, 'quantite': difference})()], 
                                self.request, 
                                action_type='out'
                            )
                        elif difference < 0: # Quantité diminuée
                            update_stock_on_delivery(
                                [type('obj', (), {'produit': produit, 'quantite': abs(difference)})()], 
                                self.request, 
                                action_type='in'
                            )
                    else: # Nouvelle ligne
                        update_stock_on_delivery([ligne_bl], self.request, action_type='out')
                    
                    ligne_bl.save()

                # 3. Sauvegarder les totaux
                self.object.update_totals()
                self.object.save()

                # Log d'audit
                action = 'modification'
                description = f"Bon de livraison #{self.object.numero} modifié."
                details = {'changed_fields': form.changed_data}

                if old_status and self.object.statut != old_status:
                    self.object.update_status(self.object.statut, self.request.user, "Statut mis à jour via le formulaire.")
                    action = 'changement_statut_et_modification'
                    description += f" Statut changé de '{old_status}' à '{self.object.statut}'."
                    details['old_status'] = old_status
                    details['new_status'] = self.object.statut

                BonLivraisonAuditLog.objects.create(
                    bon_livraison=self.object,
                    action=action,
                    description=description,
                    performed_by=self.request.user,
                    details=details
                )

                messages.success(self.request, f"Bon de livraison #{self.object.numero} mis à jour avec succès et stock ajusté.")
                return redirect(self.get_success_url())
            else:
                messages.error(self.request, "Veuillez corriger les erreurs dans les articles du bon de livraison.")
                return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return reverse_lazy('ventes:livraison_detail', kwargs={'pk': self.object.pk})
    
    
    
    
    
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.http import JsonResponse

class BonLivraisonSendEmailView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, View):
    permission_required = 'ventes.change_bonlivraison'

    def post(self, request, pk, *args, **kwargs):
        bon_livraison = get_object_or_404(BonLivraison, pk=pk, entreprise=request.entreprise)
        
        # Vérifier si le client a un email
        if not bon_livraison.commande.client or not bon_livraison.commande.client.email:
            messages.error(request, "Le client n'a pas d'adresse email valide.")
            return redirect('ventes:livraison_detail', pk=bon_livraison.pk)

        try:
            # Générer le PDF du bon de livraison
            pdf_context = {
                "bon_livraison": bon_livraison,
                "entreprise": bon_livraison.entreprise,
                "client": bon_livraison.commande.client,
                "devise_principale_symbole": self.get_devise_symbol(bon_livraison.entreprise),
            }

            pdf = render_to_pdf("ventes/livraisons/print.html", pdf_context)
            if not pdf:
                messages.error(request, "Erreur lors de la génération du PDF.")
                return redirect('ventes:livraison_detail', pk=bon_livraison.pk)

            # Préparer l'email
            subject = f"Votre bon de livraison #{bon_livraison.numero} - {bon_livraison.entreprise.nom}"
            
            message = f"""Bonjour {bon_livraison.commande.client.nom},

Veuillez trouver ci-joint votre bon de livraison n°{bon_livraison.numero}.

Détails :
- Numéro : {bon_livraison.numero}
- Date : {bon_livraison.date.strftime('%d/%m/%Y')}
- Client : {bon_livraison.commande.client.nom}
- Total TTC : {bon_livraison.total_ttc} {pdf_context['devise_principale_symbole']}

N'hésitez pas à nous contacter si vous avez des questions.

Cordialement,
L'équipe {bon_livraison.entreprise.nom}
"""

            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [bon_livraison.commande.client.email]

            # Ajouter l'email du commercial si disponible
            if bon_livraison.created_by and bon_livraison.created_by.email:
                recipient_list.append(bon_livraison.created_by.email)

            email = EmailMessage(
                subject,
                message,
                from_email,
                recipient_list,
            )
            
            # Attacher le PDF
            email.attach(
                f"bon_livraison_{bon_livraison.numero}.pdf",
                pdf,
                "application/pdf"
            )
            
            # Envoyer l'email
            email.send(fail_silently=False)
            
            # Log d'audit
            BonLivraisonAuditLog.objects.create(
                bon_livraison=bon_livraison,
                action='envoi_email',
                description=f"Bon de livraison #{bon_livraison.numero} envoyé par email à {bon_livraison.commande.client.email}",
                performed_by=request.user,
                details={
                    'destinataires': recipient_list,
                    'sujet': subject
                }
            )
            
            messages.success(request, f"Email envoyé avec succès à {bon_livraison.commande.client.email}")
            
        except Exception as e:
            logger.error(f"Erreur envoi email BL {bon_livraison.numero}: {str(e)}")
            messages.error(request, f"Erreur lors de l'envoi de l'email: {str(e)}")
        
        return redirect('ventes:livraison_detail', pk=bon_livraison.pk)

    def get_devise_symbol(self, entreprise):
        """Méthode utilitaire pour récupérer le symbole de la devise"""
        try:
            if hasattr(entreprise, 'devise_principale') and entreprise.devise_principale:
                return entreprise.devise_principale.symbole
            return "€"
        except:
            return "€"   
    
class BonLivraisonCancelView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, View):
    permission_required = 'ventes.change_bonlivraison'

    def get(self, request, pk, *args, **kwargs):
        """Affiche le formulaire de confirmation d'annulation"""
        bon_livraison = get_object_or_404(BonLivraison, pk=pk, entreprise=request.entreprise)
        
        if bon_livraison.statut == 'annule':
            messages.warning(request, "Ce bon de livraison est déjà annulé.")
            return redirect('ventes:livraison_detail', pk=pk)
        
        if bon_livraison.statut == 'livre':
            messages.error(request, "Impossible d'annuler un bon de livraison déjà livré.")
            return redirect('ventes:livraison_detail', pk=pk)
            
        return render(request, 'ventes/livraisons/confirm_cancel.html', {
            'bon_livraison': bon_livraison
        })

    def post(self, request, pk, *args, **kwargs):
        bon_livraison = get_object_or_404(BonLivraison, pk=pk, entreprise=request.entreprise)
        
        if bon_livraison.statut == 'annule':
            messages.warning(request, f"Le bon de livraison #{bon_livraison.numero} est déjà annulé.")
            return redirect('ventes:livraison_detail', pk=bon_livraison.pk)
        
        if bon_livraison.statut == 'livre':
            messages.error(request, "Impossible d'annuler un bon de livraison déjà livré.")
            return redirect('ventes:livraison_detail', pk=bon_livraison.pk)

        try:
            with transaction.atomic():
                ancien_statut = bon_livraison.statut
                raison = request.POST.get('raison', 'Non spécifiée')
                
                # Changer le statut
                bon_livraison.statut = 'annule'
                bon_livraison.save(update_fields=['statut', 'updated_at'])
                
                # Remettre le stock
                self.return_stock_to_inventory(bon_livraison, request.user)
                
                # Historique de statut
                BonLivraisonStatutHistory.objects.create(
                    bon_livraison=bon_livraison,
                    ancien_statut=ancien_statut,
                    nouveau_statut='annule',
                    changed_by=request.user,
                    commentaire=f"Annulé - Raison: {raison}"
                )
                
                # Audit log
                BonLivraisonAuditLog.objects.create(
                    bon_livraison=bon_livraison,
                    action='annulation',
                    description=f"Bon de livraison #{bon_livraison.numero} annulé",
                    performed_by=request.user,
                    details={
                        'ancien_statut': ancien_statut,
                        'raison': raison
                    }
                )
                
                messages.success(request, f"Le bon de livraison #{bon_livraison.numero} a été annulé avec succès.")
                
        except Exception as e:
            messages.error(request, f"Erreur lors de l'annulation: {str(e)}")
        
        return redirect('ventes:livraison_detail', pk=bon_livraison.pk)

    def return_stock_to_inventory(self, bon_livraison, user):
        """Remet les produits en stock"""
        for ligne in bon_livraison.items.all():
            try:
                produit = ligne.produit
                ancien_stock = produit.stock
                produit.stock += ligne.quantite
                produit.save()
                
                MouvementStock.objects.create(
                    produit=produit,
                    quantite=ligne.quantite,
                    type_mouvement='entree',
                    reference=f"ANNULATION-BL-{bon_livraison.numero}",
                    created_by=user,
                    entreprise=user.entreprise,
                    commentaire=f"Retour stock annulation BL. Ancien stock: {ancien_stock}, Nouveau stock: {produit.stock}"
                )
                
            except Exception as e:
                logger.error(f"Erreur retour stock produit {ligne.produit_id}: {e}")
    
    
    

class BonLivraisonDeleteView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DeleteView):
    model = BonLivraison
    template_name = 'ventes/livraisons/confirm_delete.html'
    success_url = reverse_lazy('ventes:livraison_list')
    # Make sure this line is present and correctly spelled!
    permission_required = 'ventes.delete_bonlivraison' 
    context_object_name = 'bon_livraison'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object:
            context['object_pk'] = self.object.pk
        return context

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object() 

        with transaction.atomic():
            bl_numero = self.object.numero
            
            lines_to_restore_stock = list(self.object.items.all()) 
            update_stock_on_delivery(lines_to_restore_stock, self.request, action_type='in')
            
            BonLivraisonAuditLog.objects.create(
                bon_livraison=None, 
                action='suppression',
                description=f"Bon de livraison #{bl_numero} supprimé.",
                performed_by=self.request.user,
                details={'bon_livraison_pk': self.object.pk, 'bon_livraison_numero': bl_numero}
            )

            response = super().delete(request, *args, **kwargs)

            messages.success(self.request, f"Bon de livraison #{bl_numero} supprimé avec succès et stock remis à jour.")
            return response

# ventes/views.py

class BonLivraisonChangeStatusView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, View):
    permission_required = 'ventes.change_bonlivraison'

    def post(self, request, pk, *args, **kwargs):
        bon_livraison = get_object_or_404(BonLivraison, pk=pk, entreprise=request.entreprise)
        new_status = request.POST.get('new_status')
        comment = request.POST.get('comment', '')

        if not new_status:
            messages.error(request, "Le nouveau statut est requis.")
            return redirect('ventes:livraison_detail', pk=bon_livraison.pk)

        # La transaction atomique doit englober toute la logique
        # pour que les annulations de transaction fonctionnent.
        with transaction.atomic():
            try:
                old_status = bon_livraison.statut
                status_changed = False

                if bon_livraison.update_status(new_status, request.user, comment):
                    status_changed = True
                    messages.success(request, f"Statut du bon de livraison #{bon_livraison.numero} mis à jour à '{bon_livraison.get_statut_display()}' avec succès.")
                else:
                    messages.info(request, f"Le statut du bon de livraison #{bon_livraison.numero} était déjà '{bon_livraison.get_statut_display()}'. Aucun changement effectué.")

                # Mise à jour du stock suite au changement de statut
                if status_changed and new_status == 'annule':  # Adaptez 'annule' à votre statut réel
                    update_stock_on_delivery(bon_livraison.items.all(), request, action_type='in')
                    messages.info(request, "Stock des produits remis à jour suite à l'annulation du bon de livraison.")

            except Exception as e:
                # Si une erreur (comme le problème 'no setter' ou une autre) survient,
                # on affiche le message d'erreur. La transaction sera automatiquement
                # annulée par le bloc 'atomic' si une exception est levée.
                messages.error(request, f"Une erreur inattendue est survenue lors du changement de statut: {e}")
                
                # Le `raise` permet au bloc `atomic` de détecter l'erreur et de l'annuler.
                # Cela garantit que la transaction est bien annulée.
                raise

        return redirect('ventes:livraison_detail', pk=bon_livraison.pk)



# ... (other imports) ...
from django.utils import timezone # Make sure this is imported at the top

class BonLivraisonPrintView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DetailView):
    model = BonLivraison
    template_name = 'ventes/livraisons/print.html'
    context_object_name = 'bon_livraison'
    permission_required = 'ventes.view_bonlivraison'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        bon_livraison = self.get_object()

        # Get the primary currency symbol for display
        devise_principale_symbole = ''
        try:
            from parametres.models import ConfigurationSAAS, Devise # Ensure import
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.entreprise)
            if config_saas.devise_principale:
                devise_principale_symbole = config_saas.devise_principale.symbole
        except (ConfigurationSAAS.DoesNotExist, Devise.DoesNotExist):
            logger.warning(f"ConfigurationSAAS ou Devise principale non trouvée pour l'entreprise {self.request.entreprise.nom} lors de l'impression du BL.")

        context['devise_principale_symbole'] = devise_principale_symbole
        context['entreprise_info'] = self.request.entreprise
        
        # --- FIX IS HERE ---
        # Pass the full datetime object, not just the date
        context['current_datetime'] = timezone.now() # Renamed context variable for clarity
        # You can also keep it as current_date if you prefer, but ensure it's a datetime object
        # context['current_date'] = timezone.now()
        # --- END FIX ---

        return context
    # If you want to force a print dialog directly, you can add this (optional)
    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)
        # Optional: Add headers to suggest printing
        # response['Content-Disposition'] = 'inline; filename="bon_livraison_{}.html"'.format(self.object.numero)
        # response['Content-Type'] = 'text/html'
        return response



logger = logging.getLogger(__name__)

# --- Helper Functions ---
def create_facture_status_history(facture, old_status, new_status, changed_by, comment=""):
    try:
        FactureStatutHistory.objects.create(
            facture=facture,
            ancien_statut=old_status,
            nouveau_statut=new_status,
            changed_by=changed_by,
            commentaire=comment
        )
        logger.info(f"Historique de statut créé pour Facture {facture.numero}: {old_status or 'N/A'} -> {new_status}")
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'historique de statut pour Facture {facture.numero}: {e}", exc_info=True)

def create_facture_audit_log(action, description, facture_instance=None, performed_by=None, details=None):
    try:
        FactureAuditLog.objects.create(
            facture=facture_instance,
            action=action,
            description=description,
            performed_by=performed_by,
            details=details
        )
        logger.info(f"Audit log enregistré: Action '{action}' sur Facture {facture_instance.numero if facture_instance else 'N/A'}")
    except Exception as e:
        logger.error(f"Erreur lors de la création du journal d'audit pour action '{action}' sur Facture {facture_instance.numero if facture_instance else 'N/A'}: {e}", exc_info=True)

# Helper function to render a template to PDF
def render_to_pdf(template_src, context_dict={}):
    html_string = render_to_string(template_src, context_dict)
    try:
        pdf_file = weasyprint.HTML(string=html_string).write_pdf()
        return pdf_file
    except Exception as e:
        logger.error(f"Erreur lors de la génération du PDF: {e}")
        return None

# EntrepriseAccessMixin doit être défini quelque part, par exemple dans un fichier `mixins.py`
class EntrepriseAccessMixin:
    def get_queryset(self):
        return super().get_queryset().filter(entreprise=self.request.entreprise)
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.entreprise != self.request.entreprise:
            raise PermissionDenied("Vous n'avez pas la permission d'accéder à cet objet.")
        return obj
class FactureListView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, ListView):
    model = Facture
    template_name = 'ventes/factures/liste.html'
    context_object_name = 'factures'
    permission_required = 'ventes.view_facture'
    paginate_by = 20

    def get_queryset(self):
        # Utiliser date_facture au lieu de date
        queryset = Facture.objects.filter(entreprise=self.request.user.entreprise).order_by('-date_facture', '-created_at')
        
        # Si vous utilisez un filtre, assurez-vous qu'il utilise aussi date_facture
        if hasattr(self, 'filterset'):
            self.filterset = FactureFilter(self.request.GET, queryset=queryset, request=self.request)
            return self.filterset.qs
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Initialiser le filtre si nécessaire
        queryset = Facture.objects.filter(entreprise=self.request.user.entreprise)
        self.filterset = FactureFilter(self.request.GET, queryset=queryset, request=self.request)
        context['filter'] = self.filterset
        
        # Stats pour le dashboard
        context['total_impayes'] = Facture.objects.filter(
            entreprise=self.request.user.entreprise,
            statut__in=['validee', 'paye_partiel']  # Corrigé pour correspondre à vos choix
        ).aggregate(total=Sum('montant_restant'))['total'] or 0
        
        context['count_factures'] = {
            'brouillon': Facture.objects.filter(entreprise=self.request.user.entreprise, statut='brouillon').count(),
            'validee': Facture.objects.filter(entreprise=self.request.user.entreprise, statut='validee').count(),  # Corrigé
            'paye': Facture.objects.filter(entreprise=self.request.user.entreprise, statut='paye').count(),
        }
        
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            context['devise_principale_symbole'] = config_saas.devise_principale.symbole if config_saas.devise_principale else ''
        except ConfigurationSAAS.DoesNotExist:
            context['devise_principale_symbole'] = ''
        
        return context
    
from django.db import transaction
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from comptabilite.models import EcritureComptable, LigneEcriture, JournalComptable, PlanComptableOHADA
from .models import Facture, LigneFacture
from .forms import FactureForm, LigneFactureFormSet

class FactureCreateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, CreateView):
    model = Facture
    form_class = FactureForm
    template_name = 'ventes/factures/form.html'
    permission_required = 'ventes.add_facture'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['entreprise'] = self.request.user.entreprise
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.POST:
            context['formset'] = LigneFactureFormSet(
                self.request.POST,
                prefix='items',
                entreprise=self.request.user.entreprise
            )
        else:
            context['formset'] = LigneFactureFormSet(
                prefix='items',
                entreprise=self.request.user.entreprise
            )
        
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            context['devise_principale_symbole'] = config_saas.devise_principale.symbole if config_saas.devise_principale else ''
        except ConfigurationSAAS.DoesNotExist:
            context['devise_principale_symbole'] = ''
            
        return context

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        formset = context['formset']
        
        if not formset.is_valid():
            messages.error(self.request, "Veuillez corriger les erreurs dans les lignes de facture.")
            return self.render_to_response(context)

        with transaction.atomic():
            # Créer et sauvegarder l'instance de Facture en premier pour avoir une PK
            self.object = form.save(commit=False)
            self.object.entreprise = self.request.user.entreprise
            self.object.created_by = self.request.user
            self.object.statut = 'brouillon'
            
            # Générer le numéro de facture
            self.generate_facture_number()
            
            # Sauvegarder d'abord la facture
            self.object.save()
            
            # Traiter le formset
            for form_line in formset:
                if form_line.cleaned_data and not form_line.cleaned_data.get('DELETE', False):
                    instance = form_line.save(commit=False)
                    instance.facture = self.object
                    instance.save()
            
            # Gérer les suppressions
            for form_line in formset.deleted_forms:
                if form_line.instance.pk:
                    form_line.instance.delete()
            
            # Mettre à jour les totaux
            self.object.refresh_from_db()
            self.object.calculate_totals()
            self.object.save(update_fields=['total_ht', 'total_tva', 'total_ttc', 'montant_restant'])

            # Audit logging
            self.create_facture_audit_log(
                action='creation',
                description=f"Facture #{self.object.numero} créée.",
                facture_instance=self.object,
                performed_by=self.request.user
            )
            
            self.create_facture_status_history(
                facture=self.object,
                old_status=None,
                new_status='brouillon',
                changed_by=self.request.user,
                comment="Facture créée avec statut initial 'brouillon'"
            )

            messages.success(self.request, f"Facture {self.object.numero} créée avec succès.")
            return redirect(self.get_success_url())

    def generate_facture_number(self):
        if not self.object.numero:
            today = timezone.now().date()
            prefix = f"FAC-{today.year}-{today.month:02d}-"
            
            last_facture = Facture.objects.filter(
                entreprise=self.request.user.entreprise,
                numero__startswith=prefix
            ).order_by('-numero').first()

            sequence = 1
            if last_facture:
                try:
                    num_part = int(last_facture.numero.split('-')[-1])
                    sequence = num_part + 1
                except (ValueError, IndexError):
                    pass

            self.object.numero = f"{prefix}{sequence:04d}"

    def get_success_url(self):
        return reverse_lazy('ventes:facture_detail', kwargs={'pk': self.object.pk})

    def create_facture_audit_log(self, action, description, facture_instance, performed_by):
        # Implémentez votre logique d'audit ici
        # Exemple: AuditLog.objects.create(...)
        pass

    def create_facture_status_history(self, facture, old_status, new_status, changed_by, comment):
        # Implémentez votre historique de statut ici
        # Exemple: FactureStatusHistory.objects.create(...)
        pass


class FactureValidateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, UpdateView):
    model = Facture
    permission_required = 'ventes.change_facture'
    template_name = 'ventes/factures/confirm_validate.html'
    fields = []  # Aucun champ nécessaire, juste la validation

    def dispatch(self, request, *args, **kwargs):
        # Vérifier que la facture peut être validée
        self.object = self.get_object()
        if self.object.statut != 'brouillon':
            messages.error(request, f"La facture {self.object.numero} ne peut pas être validée (statut: {self.object.get_statut_display()}).")
            return redirect('ventes:facture_detail', pk=self.object.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            context['devise_principale_symbole'] = config_saas.devise_principale.symbole if config_saas.devise_principale else ''
        except ConfigurationSAAS.DoesNotExist:
            context['devise_principale_symbole'] = ''
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        try:
            with transaction.atomic():
                # Valider la facture
                self.object.statut = 'validee'
                self.object.date_validation = timezone.now()
                self.object.validated_by = request.user
                self.object.save(update_fields=['statut', 'date_validation', 'validated_by'])
                
                # Créer l'écriture comptable
                ecriture = self.create_comptability_entry()
                
                # Historique et audit
                self.create_facture_status_history(
                    facture=self.object,
                    old_status='brouillon',
                    new_status='validee',
                    changed_by=request.user,
                    comment="Facture validée et écriture comptable créée"
                )
                
                self.create_facture_audit_log(
                    action='validation',
                    description=f"Facture #{self.object.numero} validée. Écriture #{ecriture.numero} créée.",
                    facture_instance=self.object,
                    performed_by=request.user
                )
                
                messages.success(request, f"Facture {self.object.numero} validée et écriture comptable créée avec succès.")
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la validation: {str(e)}")
            return redirect('ventes:facture_detail', pk=self.object.pk)
        
        return redirect('ventes:facture_detail', pk=self.object.pk)

    def create_comptability_entry(self):
        """Crée l'écriture comptable pour la facture"""
        try:
            # Récupérer le journal des ventes
            journal_ventes = JournalComptable.objects.get(
                entreprise=self.request.user.entreprise,
                code='VTE',
                actif=True
            )
        except JournalComptable.DoesNotExist:
            # Créer le journal s'il n'existe pas
            journal_ventes = JournalComptable.objects.create(
                code='VTE',
                intitule='Journal des Ventes',
                type_journal='vente',
                entreprise=self.request.user.entreprise,
                actif=True
            )
        
        # Générer le numéro d'écriture
        dernier_numero = EcritureComptable.objects.filter(
            entreprise=self.request.user.entreprise,
            journal=journal_ventes
        ).order_by('-numero').first()
        
        if dernier_numero and dernier_numero.numero:
            try:
                dernier_num = int(dernier_numero.numero.split('-')[-1])
                nouveau_num = dernier_num + 1
            except (ValueError, IndexError):
                nouveau_num = 1
        else:
            nouveau_num = 1
        
        numero_ecriture = f"{journal_ventes.code}-{nouveau_num:06d}"
        
        # Créer l'écriture comptable
        ecriture = EcritureComptable.objects.create(
            journal=journal_ventes,
            numero=numero_ecriture,
            date_ecriture=self.object.date_facture,
            date_comptable=self.object.date_facture,
            libelle=f"Facture {self.object.numero} - {self.object.client}",
            piece_justificative=self.object.numero,
            montant_devise=self.object.total_ttc,
            entreprise=self.request.user.entreprise,
            created_by=self.request.user
        )
        
        # Créer les lignes d'écriture
        self.create_ecriture_lines(ecriture)
        
        return ecriture

    def create_ecriture_lines(self, ecriture):
        """Crée les lignes d'écriture comptable pour la facture"""
        # 1. Ligne de produit (vente)
        try:
            compte_produits = PlanComptableOHADA.objects.get(
                entreprise=self.request.user.entreprise,
                numero__startswith='701'  # Compte de produits
            )
        except PlanComptableOHADA.DoesNotExist:
            # Créer le compte s'il n'existe pas
            compte_produits = PlanComptableOHADA.objects.create(
                classe='7',
                numero='701000',
                intitule='Ventes de produits finis',
                type_compte='produit',
                entreprise=self.request.user.entreprise
            )
        
        LigneEcriture.objects.create(
            ecriture=ecriture,
            compte=compte_produits,
            libelle=f"Vente {self.object.numero}",
            credit=self.object.total_ht,  # Produit = crédit
            entreprise=self.request.user.entreprise
        )
        
        # 2. Ligne de TVA collectée
        if self.object.total_tva > 0:
            try:
                compte_tva = PlanComptableOHADA.objects.get(
                    entreprise=self.request.user.entreprise,
                    numero__startswith='4457'  # TVA collectée
                )
            except PlanComptableOHADA.DoesNotExist:
                compte_tva = PlanComptableOHADA.objects.create(
                    classe='4',
                    numero='445700',
                    intitule='TVA collectée',
                    type_compte='passif',
                    entreprise=self.request.user.entreprise
                )
            
            LigneEcriture.objects.create(
                ecriture=ecriture,
                compte=compte_tva,
                libelle=f"TVA {self.object.numero}",
                credit=self.object.total_tva,  # TVA = crédit
                entreprise=self.request.user.entreprise
            )
        
        # 3. Ligne de client (débiteur)
        try:
            compte_client = PlanComptableOHADA.objects.get(
                entreprise=self.request.user.entreprise,
                numero__startswith='411'  # Clients
            )
        except PlanComptableOHADA.DoesNotExist:
            compte_client = PlanComptableOHADA.objects.create(
                classe='4',
                numero='411000',
                intitule='Clients - Ventes de biens ou prestations de services',
                type_compte='actif',
                entreprise=self.request.user.entreprise
            )
        
        LigneEcriture.objects.create(
            ecriture=ecriture,
            compte=compte_client,
            libelle=f"Client {self.object.client}",
            debit=self.object.total_ttc,  # Client = débit
            entreprise=self.request.user.entreprise
        )
        
        # Vérifier l'équilibre de l'écriture
        self.verify_ecriture_balance(ecriture)

    def verify_ecriture_balance(self, ecriture):
        """Vérifie que l'écriture est équilibrée"""
        total_debit = sum(ligne.debit for ligne in ecriture.lignes.all())
        total_credit = sum(ligne.credit for ligne in ecriture.lignes.all())
        
        if abs(total_debit - total_credit) > 0.01:
            raise ValueError(f"Écriture non équilibrée: Débit={total_debit}, Crédit={total_credit}")

    def create_facture_audit_log(self, action, description, facture_instance, performed_by):
        # Implémentez votre logique d'audit ici
        # Exemple: AuditLog.objects.create(...)
        pass

    def create_facture_status_history(self, facture, old_status, new_status, changed_by, comment):
        # Implémentez votre historique de statut ici
        # Exemple: FactureStatusHistory.objects.create(...)
        pass


class FactureGenerateEcritureView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, View):
    permission_required = 'ventes.change_facture'
    
    def post(self, request, pk):
        facture = get_object_or_404(Facture, pk=pk, entreprise=request.user.entreprise)
        
        # Vérifier que la facture est validée
        if facture.statut != 'paye':
            messages.error(request, "Seules les factures validées peuvent générer une écriture comptable.")
            return redirect('ventes:facture_detail', pk=facture.pk)
        
        # Vérifier si une écriture existe déjà
        existing_ecriture = EcritureComptable.objects.filter(
            piece_justificative=facture.numero,
            entreprise=request.user.entreprise
        ).first()
        
        if existing_ecriture:
            messages.info(request, f"Une écriture comptable existe déjà pour cette facture: {existing_ecriture.numero}")
            return redirect('ventes:facture_detail', pk=facture.pk)
        
        try:
            with transaction.atomic():
                # Créer l'écriture comptable
                ecriture = self.create_comptability_entry(facture)
                
                messages.success(request, f"Écriture comptable #{ecriture.numero} générée avec succès pour la facture {facture.numero}.")
                
        except Exception as e:
            messages.error(request, f"Erreur lors de la génération de l'écriture comptable: {str(e)}")
        
        return redirect('ventes:facture_detail', pk=facture.pk)
    
    def create_comptability_entry(self, facture):
        """Crée l'écriture comptable pour la facture"""
        try:
            # Récupérer le journal des ventes
            journal_ventes = JournalComptable.objects.get(
                entreprise=self.request.user.entreprise,
                code='VTE',
                actif=True
            )
        except JournalComptable.DoesNotExist:
            # Créer le journal s'il n'existe pas
            journal_ventes = JournalComptable.objects.create(
                code='VTE',
                intitule='Journal des Ventes',
                type_journal='vente',
                entreprise=self.request.user.entreprise,
                actif=True
            )
        
        # Générer le numéro d'écriture
        dernier_numero = EcritureComptable.objects.filter(
            entreprise=self.request.user.entreprise,
            journal=journal_ventes
        ).order_by('-numero').first()
        
        if dernier_numero and dernier_numero.numero:
            try:
                dernier_num = int(dernier_numero.numero.split('-')[-1])
                nouveau_num = dernier_num + 1
            except (ValueError, IndexError):
                nouveau_num = 1
        else:
            nouveau_num = 1
        
        numero_ecriture = f"{journal_ventes.code}-{nouveau_num:06d}"
        
        # Créer l'écriture comptable
        ecriture = EcritureComptable.objects.create(
            journal=journal_ventes,
            numero=numero_ecriture,
            date_ecriture=facture.date_facture,
            date_comptable=facture.date_facture,
            libelle=f"Facture {facture.numero} - {facture.client}",
            piece_justificative=facture.numero,
            montant_devise=facture.total_ttc,
            entreprise=self.request.user.entreprise,
            created_by=self.request.user
        )
        
        # Créer les lignes d'écriture
        self.create_ecriture_lines(ecriture, facture)
        
        return ecriture

    def create_ecriture_lines(self, ecriture, facture):
        """Crée les lignes d'écriture comptable pour la facture"""
        # Get the entreprise from the ecriture object to use for all lines
        entreprise = ecriture.entreprise
        
        # 1. Ligne de produit (vente)
        try:
            compte_produits = PlanComptableOHADA.objects.get(
                entreprise=entreprise,  # Use 'entreprise' here
                numero__startswith='701'
            )
        except PlanComptableOHADA.DoesNotExist:
            compte_produits = PlanComptableOHADA.objects.create(
                classe='7',
                numero='701000',
                intitule='Ventes de produits finis',
                type_compte='produit',
                entreprise=entreprise  # Use 'entreprise' here
            )
        
        LigneEcriture.objects.create(
            ecriture=ecriture,
            compte=compte_produits,
            libelle=f"Vente {facture.numero}",
            credit=facture.total_ht,
            entreprise=entreprise  # <--- You must add this line
        )
        
        # 2. Ligne de TVA collectée
        if facture.total_tva > 0:
            try:
                compte_tva = PlanComptableOHADA.objects.get(
                    entreprise=entreprise,  # Use 'entreprise' here
                    numero__startswith='4457'
                )
            except PlanComptableOHADA.DoesNotExist:
                compte_tva = PlanComptableOHADA.objects.create(
                    classe='4',
                    numero='445700',
                    intitule='TVA collectée',
                    type_compte='passif',
                    entreprise=entreprise  # Use 'entreprise' here
                )
            
            LigneEcriture.objects.create(
                ecriture=ecriture,
                compte=compte_tva,
                libelle=f"TVA {facture.numero}",
                credit=facture.total_tva,
                entreprise=entreprise  # <--- You must add this line
            )
        
        # 3. Ligne de client (débiteur)
        try:
            compte_client = PlanComptableOHADA.objects.get(
                entreprise=entreprise,  # Use 'entreprise' here
                numero__startswith='411'
            )
        except PlanComptableOHADA.DoesNotExist:
            compte_client = PlanComptableOHADA.objects.create(
                classe='4',
                numero='411000',
                intitule='Clients - Ventes de biens ou prestations de services',
                type_compte='actif',
                entreprise=entreprise  # Use 'entreprise' here
            )
        
        LigneEcriture.objects.create(
            ecriture=ecriture,
            compte=compte_client,
            libelle=f"Client {facture.client}",
            debit=facture.total_ttc,
            entreprise=entreprise  # <--- You must add this line
        )
        
        
        # Vérifier l'équilibre de l'écriture
        self.verify_ecriture_balance(ecriture)

    def verify_ecriture_balance(self, ecriture):
        """Vérifie que l'écriture est équilibrée"""
        total_debit = sum(ligne.debit for ligne in ecriture.lignes.all())
        total_credit = sum(ligne.credit for ligne in ecriture.lignes.all())
        
        if abs(total_debit - total_credit) > 0.01:
            raise ValueError(f"Écriture non équilibrée: Débit={total_debit}, Crédit={total_credit}")



class FactureDetailView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DetailView):
    model = Facture
    template_name = 'ventes/factures/detail.html'
    permission_required = 'ventes.view_facture'
    context_object_name = 'facture'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            context['devise_principale_symbole'] = config_saas.devise_principale.symbole if config_saas.devise_principale else ''
        except ConfigurationSAAS.DoesNotExist:
            context['devise_principale_symbole'] = ''
        
        # Vérifier s'il existe une écriture comptable liée
        facture = self.get_object()
        
        # Recherche par numéro de pièce justificative
        context['ecriture_comptable'] = EcritureComptable.objects.filter(
            piece_justificative=facture.numero,
            entreprise=self.request.user.entreprise
        ).first()
        
        # Debug: Vérifier ce qui est trouvé
        print(f"Facture numéro: {facture.numero}")
        if context['ecriture_comptable']:
            print(f"Écriture trouvée: {context['ecriture_comptable'].numero}")
        else:
            print("Aucune écriture trouvée")
            # Vérifier s'il existe d'autres écritures avec des numéros similaires
            autres_ecritures = EcritureComptable.objects.filter(
                piece_justificative__icontains=facture.numero,
                entreprise=self.request.user.entreprise
            )
            for ecriture in autres_ecritures:
                print(f"Écriture similaire: {ecriture.numero} - {ecriture.piece_justificative}")
        
        return context
    
class BonLivraisonConvertToFactureView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, View):
    permission_required = 'ventes.add_facture'

    def post(self, request, pk, *args, **kwargs):
        bon_livraison = get_object_or_404(BonLivraison, pk=pk, entreprise=request.entreprise)

        # Vérifications préalables
        if not self.can_convert_to_facture(bon_livraison):
            error_msg = self.get_conversion_error_message(bon_livraison)
            messages.error(request, error_msg)
            return redirect('ventes:livraison_detail', pk=bon_livraison.pk)

        try:
            with transaction.atomic():
                # Convertir le BL en facture
                nouvelle_facture = self.convert_bl_to_facture(bon_livraison, request.user)
                
                messages.success(
                    request, 
                    f"✅ Le bon de livraison #{bon_livraison.numero} a été converti en facture #{nouvelle_facture.numero}"
                )
                return redirect('ventes:facture_detail', pk=nouvelle_facture.pk)

        except Exception as e:
            logger.error(f"Erreur conversion BL {bon_livraison.numero} en facture: {e}")
            messages.error(request, f"Erreur lors de la conversion: {str(e)}")
            return redirect('ventes:livraison_detail', pk=bon_livraison.pk)

    def can_convert_to_facture(self, bon_livraison):
        """Vérifie si le BL peut être converti en facture"""
        if not bon_livraison:
            return False
            
        # Vérifier si le BL est déjà lié à une facture
        if hasattr(bon_livraison, 'facture') and bon_livraison.facture:
            return False
            
        # Vérifier le statut du BL
        if bon_livraison.statut != 'livre':
            return False
            
        # Vérifier qu'il y a des lignes
        if not bon_livraison.items.exists():
            return False
            
        return True

    def get_conversion_error_message(self, bon_livraison):
        """Retourne un message d'erreur approprié"""
        if hasattr(bon_livraison, 'facture') and bon_livraison.facture:
            return f"Le bon de livraison #{bon_livraison.numero} est déjà lié à une facture."
            
        if bon_livraison.statut != 'livre':
            return f"Seuls les bons de livraison livrés peuvent être convertis en facture. Statut actuel: {bon_livraison.get_statut_display()}"
            
        if not bon_livraison.items.exists():
            return "Le bon de livraison ne contient aucun article."
            
        return "Impossible de convertir ce bon de livraison en facture."

    def convert_bl_to_facture(self, bon_livraison, user):
        """Convertit un bon de livraison en facture"""
        # Générer le numéro de facture
        facture_numero = self.generate_facture_number(bon_livraison.entreprise)
        
        # Calculer la date d'échéance (30 jours par défaut)
        date_echeance = timezone.now().date() + timedelta(days=30)
        
        # Créer la facture
        facture = Facture.objects.create(
            entreprise=bon_livraison.entreprise,
            client=bon_livraison.commande.client,
            bon_livraison=bon_livraison,
            commande=bon_livraison.commande,
            devis=bon_livraison.commande.devis if hasattr(bon_livraison.commande, 'devis') else None,
            numero=facture_numero,
            date_facture=timezone.now().date(),
            date_echeance=date_echeance,
            statut='brouillon',
            total_ht=bon_livraison.total_ht or Decimal('0.00'),
            total_tva=bon_livraison.total_tva or Decimal('0.00'),
            total_ttc=bon_livraison.total_ttc or Decimal('0.00'),
            montant_restant=bon_livraison.total_ttc or Decimal('0.00'),
            notes=self.build_facture_notes(bon_livraison),
            created_by=user,
        )
        
        # Copier les lignes du BL vers la facture
        self.copy_items_to_facture(bon_livraison, facture)
        
        # Mettre à jour les totaux de la facture
        facture.calculate_totals()
        facture.save()
        
        # Log d'audit pour la facture
        FactureAuditLog.objects.create(
            facture=facture,
            action='creation_par_conversion',
            description=f"Facture créée à partir du bon de livraison #{bon_livraison.numero}",
            performed_by=user,
            details={
                'bon_livraison_id': bon_livraison.pk,
                'bon_livraison_numero': bon_livraison.numero
            }
        )
        
        # Log d'audit pour le BL
        BonLivraisonAuditLog.objects.create(
            bon_livraison=bon_livraison,
            action='conversion_en_facture',
            description=f"Bon de livraison converti en facture #{facture.numero}",
            performed_by=user,
            details={
                'facture_id': facture.pk,
                'facture_numero': facture.numero
            }
        )
        
        return facture

    def generate_facture_number(self, entreprise):
        """Génère un numéro de facture unique"""
        today = timezone.now().date()
        prefix = f"FAC-{today.year}-"
        
        last_facture = Facture.objects.filter(
            entreprise=entreprise,
            numero__startswith=prefix
        ).order_by('-numero').first()

        if last_facture and last_facture.numero:
            try:
                num_part = int(last_facture.numero.split('-')[-1])
                next_num = num_part + 1
            except (ValueError, IndexError):
                next_num = 1
        else:
            next_num = 1
        
        return f"{prefix}{next_num:04d}"

    def copy_items_to_facture(self, bon_livraison, facture):
        """Copie les items du BL vers la facture"""
        for ligne_bl in bon_livraison.items.all():
            LigneFacture.objects.create(
                facture=facture,
                produit=ligne_bl.produit,
                description=f"{ligne_bl.produit.nom} - BL #{bon_livraison.numero}",
                quantite=ligne_bl.quantite,
                prix_unitaire=ligne_bl.prix_unitaire,
                taux_tva=ligne_bl.taux_tva,
                montant_ht=ligne_bl.montant_ht or Decimal('0.00'),
                montant_tva=ligne_bl.montant_tva or Decimal('0.00'),
            )

    def build_facture_notes(self, bon_livraison):
        """Construit les notes de la facture"""
        notes = f"Facture générée à partir du bon de livraison #{bon_livraison.numero}\n"
        
        if bon_livraison.notes:
            notes += f"\nNotes du bon de livraison:\n{bon_livraison.notes}"
            
        if bon_livraison.commande and bon_livraison.commande.notes:
            notes += f"\nNotes de la commande:\n{bon_livraison.commande.notes}"
            
        if bon_livraison.commande.devis and bon_livraison.commande.devis.notes:
            notes += f"\nNotes du devis:\n{bon_livraison.commande.devis.notes}"
            
        return notes.strip()    
    
    
    
    
    
    
class FactureDetailView(LoginRequiredMixin, EntrepriseAccessMixin, DetailView):
    model = Facture
    template_name = 'ventes/factures/detail.html'
    context_object_name = 'facture'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        facture = self.object
        
        # Données pour le template
        context['lignes_facture'] = facture.items.all()
        context['paiements'] = facture.paiements.all()
        context['historique_statuts'] = facture.status_history.all().order_by('-changed_at')
        context['audit_logs'] = facture.audit_logs.all().order_by('-performed_at')
        
        # Informations supplémentaires
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.entreprise)
            context['devise_symbole'] = config_saas.devise_principale.symbole if config_saas.devise_principale else '€'
        except ConfigurationSAAS.DoesNotExist:
            context['devise_symbole'] = '€'
            
        return context

class FactureUpdateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, UpdateView):
    model = Facture
    form_class = FactureForm
    template_name = 'ventes/factures/form.html'
    permission_required = 'ventes.change_facture'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['entreprise'] = self.request.entreprise
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.POST:
            context['formset'] = LigneFactureFormSet(
                self.request.POST,
                instance=self.object,
                prefix='items',
                entreprise=self.request.entreprise
            )
        else:
            context['formset'] = LigneFactureFormSet(
                instance=self.object,
                prefix='items',
                entreprise=self.request.entreprise
            )
        
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.entreprise)
            context['devise_principale_symbole'] = config_saas.devise_principale.symbole if config_saas.devise_principale else ''
        except ConfigurationSAAS.DoesNotExist:
            context['devise_principale_symbole'] = ''
            
        return context

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        formset = context['formset']
        old_status = self.object.statut

        if not formset.is_valid():
            messages.error(self.request, "Veuillez corriger les erreurs dans les lignes de facture.")
            return self.render_to_response(context)

        with transaction.atomic():
            self.object = form.save()
            formset.instance = self.object
            formset.save()

            # Recalculate totals
            self.object.total_ht_stored = self.object.total_ht
            self.object.total_tva_stored = self.object.total_tva
            self.object.total_ttc_stored = self.object.total_ttc
            self.object.save(update_fields=['total_ht_stored', 'total_tva_stored', 'total_ttc_stored', 'updated_at'])

            # Update status if needed
            if self.object.statut != old_status:
                self.object.update_statut()
                create_facture_status_history(
                    facture=self.object,
                    old_status=old_status,
                    new_status=self.object.statut,
                    changed_by=self.request.user,
                    comment="Statut mis à jour via modification de la facture"
                )

            # Audit logging
            create_facture_audit_log(
                action='modification',
                description=f"Facture #{self.object.numero} modifiée.",
                facture_instance=self.object,
                performed_by=self.request.user,
                details={'changed_fields': form.changed_data}
            )

            messages.success(self.request, f"Facture {self.object.numero} mise à jour avec succès.")
            return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy('ventes:facture_detail', kwargs={'pk': self.object.pk})

class FactureDeleteView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DeleteView):
    model = Facture
    template_name = 'ventes/factures/confirm_delete.html'
    permission_required = 'ventes.delete_facture'
    success_url = reverse_lazy('ventes:facture_list')

    def form_valid(self, form):
        facture_numero = self.object.numero
        facture_pk = self.object.pk
        
        with transaction.atomic():
            # Create audit log before deletion
            create_facture_audit_log(
                action='suppression',
                description=f"Facture #{facture_numero} supprimée.",
                facture_instance=None,
                performed_by=self.request.user,
                details={'facture_id': facture_pk, 'facture_numero': facture_numero}
            )
            
            response = super().form_valid(form)
            messages.success(self.request, f"Facture {facture_numero} supprimée avec succès.")
            return response

class FactureStatutUpdateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, UpdateView):
    model = Facture
    form_class = FactureStatutForm
    template_name = 'ventes/factures/change_status.html'
    permission_required = 'ventes.change_facture'

    def form_valid(self, form):
        old_status = self.object.statut
        new_status = form.cleaned_data['statut']
        comment = form.cleaned_data['commentaire']
        
        if old_status != new_status:
            with transaction.atomic():
                self.object.statut = new_status
                self.object.save(update_fields=['statut'])
                
                create_facture_status_history(
                    facture=self.object,
                    old_status=old_status,
                    new_status=new_status,
                    changed_by=self.request.user,
                    comment=comment
                )
                
                create_facture_audit_log(
                    action='changement_statut',
                    description=f"Statut de la facture #{self.object.numero} changé de '{old_status}' à '{new_status}'.",
                    facture_instance=self.object,
                    performed_by=self.request.user,
                    details={'old_status': old_status, 'new_status': new_status, 'comment': comment}
                )
                
                messages.success(self.request, f"Statut de la facture #{self.object.numero} mis à jour à '{self.object.get_statut_display()}'.")
        else:
            messages.info(self.request, f"Le statut de la facture #{self.object.numero} était déjà '{self.object.get_statut_display()}'. Aucun changement effectué.")
        
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('ventes:facture_detail', kwargs={'pk': self.object.pk})
    
class FacturePrintView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DetailView):
    model = Facture
    template_name = 'ventes/factures/print.html'
    permission_required = 'ventes.view_facture'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.entreprise)
            context['devise_principale_symbole'] = config_saas.devise_principale.symbole if config_saas.devise_principale else ''
        except ConfigurationSAAS.DoesNotExist:
            context['devise_principale_symbole'] = ''
            
        context['current_date'] = timezone.now()
        context['entreprise_info'] = self.request.entreprise
        
        # Récupérer la signature de l'utilisateur connecté
        context['user_signature'] = self.get_user_signature()
        context['user_full_name'] = self.request.user.get_full_name() or self.request.user.username
        context['user_position'] = self.get_user_position()
        
        # Log the print action
        create_facture_audit_log(
            action='impression',
            description=f"Facture #{self.object.numero} imprimée.",
            facture_instance=self.object,
            performed_by=self.request.user
        )
        
        return context

    def get_user_signature(self):
        """
        Récupère la signature de l'utilisateur connecté
        Retourne l'URL de la signature ou None si non disponible
        """
        try:
            # Vérifier si l'utilisateur a un profil avec signature
            if hasattr(self.request.user, 'profil'):
                profil = self.request.user.profil
                # Priorité à la signature PNG, puis SVG
                if profil.signature:
                    return profil.signature.url
                elif profil.signature_svg:
                    # Convertir SVG en data URL pour l'affichage direct
                    return self.convert_svg_to_data_url(profil.signature_svg)
            return None
        except Exception as e:
            logger.error(f"Erreur récupération signature utilisateur {self.request.user}: {e}")
            return None

    def convert_svg_to_data_url(self, svg_content):
        """
        Convertit le contenu SVG en data URL pour l'affichage direct dans le HTML
        """
        try:
            if svg_content.startswith('data:image/svg+xml;base64,'):
                return svg_content  # Déjà au format data URL
            else:
                # Encoder en base64
                encoded_svg = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
                return f"data:image/svg+xml;base64,{encoded_svg}"
        except Exception as e:
            logger.error(f"Erreur conversion SVG: {e}")
            return None

    def get_user_position(self):
        """
        Récupère le poste de l'utilisateur
        """
        try:
            if hasattr(self.request.user, 'profil') and self.request.user.profil.poste:
                return self.request.user.profil.poste
            # Fallback: utiliser le rôle de l'utilisateur
            if hasattr(self.request.user, 'get_role_display'):
                return self.request.user.get_role_display()
            return "Responsable"
        except Exception:
            return "Responsable"
        
        
from xhtml2pdf import pisa
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

class FactureSendEmailView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'ventes.change_facture'

    def post(self, request, pk, *args, **kwargs):
        facture = get_object_or_404(Facture, pk=pk, entreprise=request.entreprise)
        
        try:
            if not facture.client or not facture.client.email:
                messages.error(request, "Le client n'a pas d'adresse email valide.")
                return redirect('ventes:facture_detail', pk=facture.pk)

            # Générer le contexte
            context = self.get_email_context(facture, request)
            
            # Générer le PDF avec xhtml2pdf
            pdf_content = self.generate_pdf_with_xhtml2pdf(request, context)
            
            if not pdf_content:
                messages.error(request, "Erreur lors de la génération du PDF.")
                return redirect('ventes:facture_detail', pk=facture.pk)

            # Envoyer l'email
            self.send_facture_email(facture, pdf_content, request.user.email)
            
            messages.success(request, f"Facture envoyée à {facture.client.email}")
            
        except Exception as e:
            logger.error(f"Erreur envoi email: {e}")
            messages.error(request, f"Erreur: {str(e)}")
        
        return redirect('ventes:facture_detail', pk=facture.pk)

    def get_email_context(self, facture, request):
        """Prépare le contexte pour l'email"""
        return {
            'facture': facture,
            'devise_principale_symbole': self.get_devise_symbol(request.entreprise),
            'user_full_name': request.user.get_full_name() or request.user.username,
            'user_position': self.get_user_position(request.user),
            'current_date': timezone.now(),
        }

    def generate_pdf_with_xhtml2pdf(self, request, context):
        """Génère le PDF avec xhtml2pdf (alternative à WeasyPrint)"""
        try:
            # Rendre le template HTML
            html_string = render_to_string('ventes/factures/print_simple.html', context)
            
            # Créer un buffer pour le PDF
            pdf_buffer = BytesIO()
            
            # Convertir HTML en PDF
            pisa_status = pisa.CreatePDF(
                html_string,
                dest=pdf_buffer,
                encoding='UTF-8'
            )
            
            # Vérifier si la conversion a réussi
            if pisa_status.err:
                logger.error(f"Erreur xhtml2pdf: {pisa_status.err}")
                return None
            
            # Retourner le contenu PDF
            pdf_buffer.seek(0)
            return pdf_buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Erreur génération PDF xhtml2pdf: {e}")
            return None

    def send_facture_email(self, facture, pdf_content, from_email):
        """Envoie l'email avec la facture"""
        subject = f"Facture {facture.numero} - {facture.entreprise.nom}"
        
        message = self.build_email_message(facture)
        
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=from_email,
            to=[facture.client.email],
        )
        
        email.attach(
            f"facture_{facture.numero}.pdf",
            pdf_content,
            "application/pdf"
        )
        
        email.send()

    def build_email_message(self, facture):
        """Construit le message email"""
        return f"""Madame, Monsieur,

Veuillez trouver ci-joint votre facture n°{facture.numero}.

DÉTAILS DE LA FACTURE :
• Numéro : {facture.numero}
• Date : {facture.date.strftime('%d/%m/%Y')}
• Client : {facture.client.nom}
• Total TTC : {facture.total_ttc} {self.get_devise_symbol(facture.entreprise)}

Pour toute question, n'hésitez pas à nous contacter.

Cordialement,
{facture.entreprise.nom}
"""

    def get_devise_symbol(self, entreprise):
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            return config_saas.devise_principale.symbole if config_saas.devise_principale else '€'
        except:
            return '€'

    def get_user_position(self, user):
        try:
            if hasattr(user, 'profil') and user.profil.poste:
                return user.profil.poste
            return "Responsable"
        except:
            return "Responsable"

from django.db import transaction
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.db.models import Sum
import decimal
import logging

logger = logging.getLogger(__name__)

class PaiementCreateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, CreateView):
    model = Paiement
    form_class = PaiementForm
    template_name = 'ventes/paiements/form.html'
    permission_required = 'ventes.add_paiement'

    def dispatch(self, request, *args, **kwargs):
        self.facture = get_object_or_404(
            Facture, 
            pk=self.kwargs['facture_pk'], 
            entreprise=self.request.user.entreprise
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['facture'] = self.facture
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial['facture'] = self.facture
        initial['montant'] = self.facture.montant_restant
        initial['date'] = timezone.now().date()
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['facture'] = self.facture
        
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            context['devise_symbole'] = config_saas.devise_principale.symbole if config_saas.devise_principale else ''
        except ConfigurationSAAS.DoesNotExist:
            context['devise_symbole'] = ''
            
        return context

    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Définir les champs obligatoires
                form.instance.facture = self.facture
                form.instance.entreprise = self.request.user.entreprise
                form.instance.created_by = self.request.user
                
                # Sauvegarder le paiement
                self.object = form.save()
                
                # Mettre à jour le statut de la facture
                old_status = self.facture.statut
                self.facture.update_statut()
                
                if self.facture.statut != old_status:
                    self.create_facture_status_history(
                        facture=self.facture,
                        old_status=old_status,
                        new_status=self.facture.statut,
                        changed_by=self.request.user,
                        comment=f"Statut mis à jour après paiement de {form.instance.montant:.2f}"
                    )
                
                # Créer l'écriture comptable (si demandé dans le formulaire)
                create_ecriture = self.request.POST.get('create_ecriture', 'off') == 'on'
                if create_ecriture:
                    self.create_ecriture_comptable(self.object)
                
                # Audit logging
                self.create_facture_audit_log(
                    action='paiement_enregistre',
                    description=f"Paiement de {form.instance.montant:.2f} enregistré pour la facture #{self.facture.numero}.",
                    facture_instance=self.facture,
                    performed_by=self.request.user,
                    details={
                        'paiement_id': form.instance.pk,
                        'mode_paiement': form.instance.mode_paiement,
                        'montant': str(form.instance.montant),
                        'ecriture_comptable_creée': create_ecriture
                    }
                )
                
                messages.success(self.request, f"Paiement de {form.instance.montant:.2f} enregistré avec succès.")
                if create_ecriture:
                    messages.info(self.request, "Écriture comptable créée avec succès.")
            
            return HttpResponseRedirect(self.get_success_url())
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement du paiement: {e}")
            messages.error(self.request, f"Erreur lors de l'enregistrement du paiement: {str(e)}")
            return self.form_invalid(form)

    def create_ecriture_comptable(self, paiement):
        """
        Crée une écriture comptable pour le paiement
        """
        try:
            from comptabilite.models import JournalComptable, PlanComptableOHADA, EcritureComptable, LigneEcriture
            
            entreprise = self.request.user.entreprise
            
            # Déterminer le journal en fonction du mode de paiement
            if paiement.mode_paiement == 'espece':
                journal_code = 'CA'
                journal_libelle = 'Caisse'
                compte_tresorerie_numero = '531000'  # Caisse
            elif paiement.mode_paiement == 'cheque':
                journal_code = 'BQ'
                journal_libelle = 'Banque'
                compte_tresorerie_numero = '512000'  # Banque
            elif paiement.mode_paiement == 'virement':
                journal_code = 'BQ'
                journal_libelle = 'Banque'
                compte_tresorerie_numero = '512000'  # Banque
            elif paiement.mode_paiement == 'carte':
                journal_code = 'BQ'
                journal_libelle = 'Banque'
                compte_tresorerie_numero = '512000'  # Banque
            else:
                journal_code = 'OD'
                journal_libelle = 'Opérations Diverses'
                compte_tresorerie_numero = '531000'  # Caisse par défaut
            
            # Récupérer ou créer le journal
            journal, created = JournalComptable.objects.get_or_create(
                code=journal_code,
                entreprise=entreprise,
                defaults={
                    'intitule': journal_libelle,
                    'type_journal': 'banque' if journal_code == 'BQ' else 'caisse'
                }
            )
            
            # Récupérer les comptes
            compte_tresorerie = PlanComptableOHADA.objects.get(
                numero=compte_tresorerie_numero,
                entreprise=entreprise
            )
            
            compte_client = PlanComptableOHADA.objects.get(
                numero='411100',  # Clients - Ventes de biens ou prestations de services
                entreprise=entreprise
            )
            
            # Générer un numéro d'écriture
            today = timezone.now().date()
            last_ecriture = EcritureComptable.objects.filter(
                journal=journal,
                date_ecriture=today
            ).order_by('-numero').first()
            
            sequence = 1
            if last_ecriture:
                try:
                    sequence = int(last_ecriture.numero.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    pass
            
            numero_ecriture = f"{journal.code}-{today.strftime('%Y%m%d')}-{sequence:04d}"
            
            # Créer l'écriture comptable
            ecriture = EcritureComptable.objects.create(
                journal=journal,
                numero=numero_ecriture,
                date_ecriture=paiement.date,
                date_comptable=paiement.date,
                libelle=f"Paiement Facture {paiement.facture.numero} - {paiement.facture.client.nom}",
                piece_justificative=paiement.reference or f"PAY{paiement.id}",
                montant_devise=paiement.montant,
                entreprise=entreprise,
                created_by=self.request.user
            )
            
            # Ligne au débit : Trésorerie
            LigneEcriture.objects.create(
                ecriture=ecriture,
                compte=compte_tresorerie,
                libelle=f"Encaissement Facture {paiement.facture.numero}",
                debit=paiement.montant,
                credit=0,
                entreprise=entreprise
            )
            
            # Ligne au crédit : Clients
            LigneEcriture.objects.create(
                ecriture=ecriture,
                compte=compte_client,
                libelle=f"Règlement Client {paiement.facture.client.nom}",
                debit=0,
                credit=paiement.montant,
                entreprise=entreprise
            )
            
            logger.info(f"Écriture comptable {numero_ecriture} créée pour le paiement {paiement.id}")
            return ecriture
            
        except ImportError:
            logger.warning("Module comptabilité non installé - écriture non créée")
            return None
        except PlanComptableOHADA.DoesNotExist:
            logger.error("Comptes comptables non trouvés pour l'entreprise")
            return None
        except Exception as e:
            logger.error(f"Erreur création écriture comptable: {e}")
            return None

    def create_facture_status_history(self, facture, old_status, new_status, changed_by, comment=''):
        """Créer un historique de changement de statut"""
        try:
            FactureStatutHistory.objects.create(
                facture=facture,
                ancien_statut=old_status,
                nouveau_statut=new_status,
                changed_by=changed_by,
                commentaire=comment,
                changed_at=timezone.now()
            )
        except Exception as e:
            logger.error(f"Erreur création historique statut facture: {e}")

    def create_facture_audit_log(self, action, description, facture_instance, performed_by, details=None):
        """Créer un log d'audit"""
        try:
            FactureAuditLog.objects.create(
                facture=facture_instance,
                action=action,
                description=description,
                performed_by=performed_by,
                details=details or {},
                performed_at=timezone.now()
            )
        except Exception as e:
            logger.error(f"Erreur création log audit facture: {e}")

    def get_success_url(self):
        return reverse_lazy('ventes:facture_detail', kwargs={'pk': self.kwargs['facture_pk']})
    
class PaiementDeleteView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DeleteView):
    model = Paiement
    template_name = 'ventes/paiements/confirm_delete.html'
    permission_required = 'ventes.delete_paiement'

    def form_valid(self, form):
        facture = self.object.facture
        paiement_montant = self.object.montant
        
        with transaction.atomic():
            # Supprimer les écritures comptables associées
            self.delete_ecritures_comptables(self.object)
            
            response = super().form_valid(form)
            
            # Mettre à jour le statut de la facture
            old_status = facture.statut
            facture.update_statut()
            
            if facture.statut != old_status:
                self.create_facture_status_history(
                    facture=facture,
                    old_status=old_status,
                    new_status=facture.statut,
                    changed_by=self.request.user,
                    comment=f"Statut mis à jour après suppression du paiement de {paiement_montant:.2f}"
                )
            
            # Audit logging
            self.create_facture_audit_log(
                action='paiement_supprime',
                description=f"Paiement de {paiement_montant:.2f} supprimé pour la facture #{facture.numero}.",
                facture_instance=facture,
                performed_by=self.request.user,
                details={
                    'paiement_id': self.object.pk,
                    'mode_paiement': self.object.mode_paiement,
                    'montant': str(paiement_montant)
                }
            )
            
            messages.success(self.request, f"Paiement de {paiement_montant:.2f} supprimé avec succès.")
            return response

    def delete_ecritures_comptables(self, paiement):
        """Supprime les écritures comptables associées au paiement"""
        try:
            from comptabilite.models import EcritureComptable
            
            # Trouver les écritures liées à ce paiement
            ecritures = EcritureComptable.objects.filter(
                piece_justificative__icontains=f"PAY{paiement.id}",
                entreprise=self.request.user.entreprise
            )
            
            count = ecritures.count()
            ecritures.delete()
            
            logger.info(f"{count} écriture(s) comptable(s) supprimée(s) pour le paiement {paiement.id}")
            
        except ImportError:
            logger.warning("Module comptabilité non installé - aucune écriture à supprimer")
        except Exception as e:
            logger.error(f"Erreur suppression écritures comptables: {e}")

    def create_facture_status_history(self, facture, old_status, new_status, changed_by, comment=''):
        """Créer un historique de changement de statut"""
        try:
            FactureStatutHistory.objects.create(
                facture=facture,
                ancien_statut=old_status,
                nouveau_statut=new_status,
                changed_by=changed_by,
                commentaire=comment,
                changed_at=timezone.now()
            )
        except Exception as e:
            logger.error(f"Erreur création historique statut facture: {e}")

    def create_facture_audit_log(self, action, description, facture_instance, performed_by, details=None):
        """Créer un log d'audit"""
        try:
            FactureAuditLog.objects.create(
                facture=facture_instance,
                action=action,
                description=description,
                performed_by=performed_by,
                details=details or {},
                performed_at=timezone.now()
            )
        except Exception as e:
            logger.error(f"Erreur création log audit facture: {e}")

    def get_success_url(self):
        return reverse_lazy('ventes:facture_detail', kwargs={'pk': self.object.facture.pk})
    
    
    
import decimal
import logging

# ventes/views.py
# (Keep all your existing imports)

# --- NOUVEL IMPORT ---
from .filters import CommandeFilter, DevisFilter # Import both filters

# ... (your other views and helper functions) ...

# ==================== VUES DE GESTION DES DEVIS ====================
class DevisListView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, ListView):
    model = Devis
    template_name = 'ventes/devis/liste.html'
    context_object_name = 'devis_list' # Changed context_object_name for clarity
    permission_required = 'ventes.view_devis'
    paginate_by = 10 # Add pagination here

    def get_queryset(self):
        # 1. Filter by the user's entreprise first
        queryset = super().get_queryset().filter(entreprise=self.request.entreprise).order_by('-date', '-created_at')

        # 2. Apply the advanced filters using DevisFilter
        self.filterset = DevisFilter(self.request.GET, queryset=queryset, request=self.request)
        return self.filterset.qs # Return the filtered queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter'] = self.filterset # Pass the filter object to the template
        
        entreprise = self.request.entreprise

        devise_principale_symbole = ''
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            if config_saas.devise_principale:
                devise_principale_symbole = config_saas.devise_principale.symbole
        except ConfigurationSAAS.DoesNotExist:
            logger.warning(f"ConfigurationSAAS non trouvée pour l'entreprise {entreprise.nom}")
        except Devise.DoesNotExist: # This Devise is the model, not the one from .models
            logger.warning(f"Devise principale non trouvée dans ConfigurationSAAS pour l'entreprise {entreprise.nom}")

        context['devise_principale_symbole'] = devise_principale_symbole
        context['entreprise_courante'] = entreprise 
        return context

# ... (rest of your views) ...


# --- IMPORT DE VOTRE UTILITAIRE PDF ---
import logging
import datetime
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    UpdateView,
    DeleteView,
    DetailView,
    ListView,
    View,
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.core.mail import EmailMessage, send_mail
from django.conf import settings
from django.utils import timezone
from .forms import DevisForm, LigneDevisFormSet
from .utils import render_to_pdf

logger = logging.getLogger(__name__)

# ==================== MIXIN DE BASE POUR LA GESTION DES DEVIS ====================


class DevisBaseMixin:
    """
    Mixin de base pour les vues de gestion des devis.
    Contient les méthodes partagées pour l'audit, l'historique et la logique de business.
    """

    def get_devise_symbol(self, entreprise):
        """
        Récupère le symbole de la devise principale pour l'entreprise donnée.
        """
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            if config_saas.devise_principale:
                return config_saas.devise_principale.symbole
        except (ConfigurationSAAS.DoesNotExist, Devise.DoesNotExist) as e:
            logger.warning(
                f"ConfigurationSAAS ou Devise principale non trouvée pour l'entreprise {entreprise.nom}: {e}"
            )
        except Exception as e:
            logger.error(
                f"Erreur inattendue lors de la récupération de la devise pour l'entreprise {entreprise.nom}: {e}",
                exc_info=True,
            )
        return ""

    def log_formset_errors(self, form, formset):
        """
        Enregistre les erreurs du formulaire principal et du formset dans les logs.
        """
        logger.error("Le formset n'est PAS valide lors de l'opération sur le devis.")
        if form.errors:
            logger.error(f"Erreurs du formulaire Devis principal : {form.errors.as_json()}")
        for i, line_form in enumerate(formset):
            if line_form.errors:
                logger.error(f"Erreurs de la ligne de formset {i} : {line_form.errors.as_json()}")
            if line_form.non_field_errors():
                logger.error(f"Erreurs non-champ de la ligne de formset {i} : {line_form.non_field_errors()}")
            if line_form.cleaned_data.get("DELETE") and line_form.errors:
                logger.warning(
                    f"Ligne de formset {i} marquée pour suppression a toujours des erreurs : {line_form.errors.as_json()}"
                )

    def create_status_history(self, old_status, new_status, comment):
        """
        Crée une entrée dans l'historique des statuts du devis.
        """
        try:
            DevisStatutHistory.objects.create(
                devis=self.object,
                ancien_statut=old_status,
                nouveau_statut=new_status,
                changed_by=self.request.user,
                commentaire=comment,
            )
            logger.info(
                f"Historique de statut créé pour Devis {self.object.numero}: {old_status or 'N/A'} -> {new_status}"
            )
        except Exception as e:
            logger.error(
                f"Erreur lors de la création de l'historique de statut pour Devis {self.object.numero}: {e}",
                exc_info=True,
            )

    def create_audit_log(self, action, description, devis_instance=None, details=None):
        """
        Crée une entrée dans le journal d'audit pour les actions sur les devis.
        """
        try:
            DevisAuditLog.objects.create(
                devis=devis_instance,
                action=action,
                description=description,
                performed_by=self.request.user,
                details=details,
            )
            logger.info(
                f"Audit log enregistré: Action '{action}' sur Devis {devis_instance.numero if devis_instance else 'N/A'}"
            )
        except Exception as e:
            logger.error(
                f"Erreur lors de la création du journal d'audit pour action '{action}' sur Devis {devis_instance.numero if devis_instance else 'N/A'}: {e}",
                exc_info=True,
            )

    def generate_devis_number(self):

        if not self.object.numero:
            today_str = date.today().strftime("%Y%m%d")  # ← Utilisez date.today()
            last_devis = (
                Devis.objects.filter(
                    entreprise=self.request.entreprise, 
                    created_at__date=date.today()  # ← Et ici
                )
                .order_by("-numero")
                .first()
            )

            sequence = 1
            if last_devis:
                try:
                    parts = last_devis.numero.split("-")
                    if len(parts) == 3 and parts[1] == today_str:
                        last_sequence = int(parts[2])
                        sequence = last_sequence + 1
                except (ValueError, IndexError):
                    pass

            self.object.numero = f"DEV-{today_str}-{sequence:03d}"

            # S'assurer que le numéro est unique
            while Devis.objects.filter(numero=self.object.numero).exists():
                sequence += 1
                self.object.numero = f"DEV-{today_str}-{sequence:03d}"

    def send_devis_email(self):
        """
        Génère le PDF du devis et l'envoie par e-mail au client.
        """
        try:
            # Vérifications préalables
            if not hasattr(self.object, 'client') or not self.object.client:
                logger.warning(f"Devis {getattr(self.object, 'numero', 'N/A')} n'a pas de client associé")
                return False
                
            if not self.object.client.email:
                logger.warning(f"Client {self.object.client.nom} n'a pas d'email valide")
                return False

            # Préparation du contexte PDF
            pdf_context = {
                "devis": self.object,
                "entreprise": self.object.entreprise,
                "client": self.object.client,
                "devise_principale_symbole": self.get_devise_symbol(self.object.entreprise),
            }

            # Génération du PDF
            pdf = render_to_pdf("ventes/devis/print.html", pdf_context)
            if not pdf:
                logger.error(f"Échec de génération du PDF pour le devis {self.object.numero}")
                return False

            # Gestion de la date - plusieurs options selon votre modèle
            date_field = getattr(self.object, 'date', None)
            if not date_field:
                date_field = getattr(self.object, 'date_creation', None)
            if not date_field:
                date_field = getattr(self.object, 'created_at', None)
            
            date_str = date_field.strftime('%d/%m/%Y') if date_field else "Date non spécifiée"

            # Construction du message
            subject = f"Votre devis #{self.object.numero} - {self.object.entreprise.nom}"
            message = f"""Cher(e) {self.object.client.nom},

    Veuillez trouver ci-joint votre devis numéro {self.object.numero}.

    Date : {date_str}
    Montant total : {self.object.total_ttc} {pdf_context['devise_principale_symbole']}

    Pour toute question, contactez-nous.

    Cordialement,
    {self.object.entreprise.nom}
    """

            # Envoi de l'email
            email = EmailMessage(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.object.client.email],
            )
            email.attach(f"devis_{self.object.numero}.pdf", pdf, "application/pdf")
            email.send()
            
            logger.info(f"Email envoyé avec succès à {self.object.client.email}")
            return True

        except Exception as e:
            logger.error(f"Erreur d'envoi d'email pour le devis {getattr(self.object, 'numero', 'N/A')}: {str(e)}", exc_info=True)
            return False


# ==================== VUES DE GESTION DES DEVIS ====================
import logging
import smtplib
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from django.db import transaction
from io import BytesIO
from xhtml2pdf import pisa
from parametres.models import ConfigurationSAAS

logger = logging.getLogger(__name__)

class DevisCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DevisBaseMixin, CreateView
):
    model = Devis
    form_class = DevisForm
    template_name = "ventes/devis/form.html"
    permission_required = "ventes.add_devis"
    success_url = reverse_lazy('ventes:devis_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["entreprise"] = self.request.user.entreprise
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.user.entreprise

        formset_kwargs = {"prefix": "form", "entreprise": entreprise}

        if self.request.POST:
            context["formset"] = LigneDevisFormSet(
                self.request.POST,
                instance=self.object if hasattr(self, "object") else None,
                **formset_kwargs,
            )
        else:
            context["formset"] = LigneDevisFormSet(
                instance=self.object if hasattr(self, "object") else None,
                **formset_kwargs,
            )

        # Récupérer la devise principale
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            devise_symbole = "€"

        context["devise_principale_symbole"] = devise_symbole
        context["debug_info"] = {
            "entreprise": entreprise,
            "clients_count": Client.objects.filter(entreprise=entreprise).count(),
            "produits_count": Produit.objects.filter(entreprise=entreprise).count(),
        }
        return context

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        formset = context["formset"]

        if not formset.is_valid():
            self.log_formset_errors(form, formset)
            messages.error(self.request, "Veuillez corriger les erreurs dans les articles du devis.")
            return self.render_to_response(context)

        with transaction.atomic():
            self.object = form.save(commit=False)
            self.object.entreprise = self.request.user.entreprise
            self.object.created_by = self.request.user
            self.object.statut = "envoye"
            self.generate_devis_number()
            self.object.save()
            formset.instance = self.object
            formset.save()

            self.create_status_history(
                old_status=None,
                new_status=self.object.statut,
                comment="Devis créé et statut initial défini.",
            )
            self.create_audit_log(
                action="creation",
                description=f"Devis #{self.object.numero} créé.",
                devis_instance=self.object,
            )

            # Envoi direct de l'email ici
            email_sent = self.send_devis_email_with_pdf()

            if email_sent:
                messages.success(self.request, "Devis créé avec succès et envoyé au client.")
                self.create_audit_log(
                    action="envoi_email",
                    description=f"Devis #{self.object.numero} envoyé par email au client {self.object.client.email}.",
                    devis_instance=self.object,
                )
            else:
                messages.warning(
                    self.request,
                    "Devis créé, mais l'envoi de l'e-mail a échoué. Vérifiez les logs.",
                )
                self.create_audit_log(
                    action="envoi_email",
                    description=f"Tentative d'envoi d'email pour Devis #{self.object.numero} a échoué.",
                    devis_instance=self.object,
                    details={"error": "Voir les logs pour plus de détails."},
                )

            return redirect(self.get_success_url())

    def send_devis_email_with_pdf(self):
        """Envoi du devis en PDF avec la devise principale - CORRIGÉ"""
        try:
            # Vérifications de base
            if not hasattr(self, 'object') or not self.object:
                logger.error("Aucun objet devis pour l'envoi d'email")
                return False
                
            if not hasattr(self.object, 'client') or not self.object.client:
                logger.error(f"Client manquant pour le devis #{getattr(self.object, 'numero', 'N/A')}")
                return False
                
            if not hasattr(self.object.client, 'email') or not self.object.client.email:
                logger.error(f"Email manquant pour le client {getattr(self.object.client, 'nom', 'N/A')}")
                return False

            # Récupérer la devise principale
            try:
                config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
                devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
            except ConfigurationSAAS.DoesNotExist:
                devise_symbole = "€"

            # Générer le PDF
            pdf_buffer = self.generate_devis_pdf(devise_symbole)
            if not pdf_buffer:
                logger.error("Échec de la génération du PDF")
                return False

            # Préparer l'email
            subject = f"Devis {self.object.numero} - {self.request.user.entreprise.nom}"
            recipient_email = self.object.client.email

            # Context pour le template email
            context = {
                'devis': self.object,
                'entreprise': self.request.user.entreprise,
                'client': self.object.client,
                'devise_symbole': devise_symbole,
                'lignes': self.get_lignes_devis(),
            }

            # Rendu des templates
            html_message = render_to_string('ventes/emails/devis_email.html', context)
            plain_message = strip_tags(html_message)

            # CORRECTION: Utiliser EmailMultiAlternatives au lieu de EmailMessage
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email],
            )
            
            # Ajouter la version HTML
            email.attach_alternative(html_message, "text/html")
            
            # Attacher le PDF
            pdf_name = f"devis_{self.object.numero}.pdf"
            email.attach(pdf_name, pdf_buffer.getvalue(), 'application/pdf')

            # Envoyer l'email
            email.send(fail_silently=False)
            
            logger.info(f"Email avec PDF envoyé avec succès pour le devis #{self.object.numero}")
            return True
            
        except smtplib.SMTPException as e:
            logger.error(f"Erreur SMTP lors de l'envoi de l'email: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Erreur générale lors de l'envoi de l'email: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def generate_devis_pdf(self, devise_symbole):
        """Génère le PDF du devis"""
        try:
            # Context pour le template PDF
            context = {
                'devis': self.object,
                'entreprise': self.request.user.entreprise,
                'client': self.object.client,
                'lignes': self.get_lignes_devis(),
                'devise_symbole': devise_symbole,
            }

            # Rendu du template HTML pour le PDF
            html_string = render_to_string('ventes/devis/devis_pdf.html', context)
            
            # Création du PDF
            pdf_buffer = BytesIO()
            pisa_status = pisa.CreatePDF(
                html_string, 
                dest=pdf_buffer,
                encoding='UTF-8'
            )
            
            if pisa_status.err:
                logger.error("Erreur lors de la génération du PDF avec xhtml2pdf")
                # Fallback: générer un PDF simple
                return self.generate_simple_pdf(devise_symbole)
            
            pdf_buffer.seek(0)
            return pdf_buffer
            
        except Exception as e:
            logger.error(f"Erreur génération PDF: {str(e)}")
            return self.generate_simple_pdf(devise_symbole)

    def generate_simple_pdf(self, devise_symbole):
        """Génère un PDF simple en cas d'erreur avec xhtml2pdf"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.units import mm
            
            pdf_buffer = BytesIO()
            c = canvas.Canvas(pdf_buffer, pagesize=A4)
            width, height = A4
            
            # En-tête
            c.setFont("Helvetica-Bold", 16)
            c.drawString(20*mm, height-20*mm, f"DEVIS N° {self.object.numero}")
            c.setFont("Helvetica-Bold", 14)
            c.drawString(20*mm, height-30*mm, self.request.user.entreprise.nom)
            
            # Informations entreprise
            c.setFont("Helvetica", 10)
            c.drawString(20*mm, height-45*mm, f"Adresse: {self.request.user.entreprise.adresse}")
            c.drawString(20*mm, height-50*mm, f"Tél: {self.request.user.entreprise.telephone}")
            
            # Informations client
            c.setFont("Helvetica-Bold", 12)
            c.drawString(20*mm, height-70*mm, "CLIENT:")
            c.setFont("Helvetica", 10)
            c.drawString(20*mm, height-80*mm, f"{self.object.client.nom_complet}")
            c.drawString(20*mm, height-85*mm, f"{self.object.client.adresse}")
            c.drawString(20*mm, height-90*mm, f"Tél: {self.object.client.telephone}")
            
            # Détails du devis
            c.setFont("Helvetica-Bold", 12)
            c.drawString(20*mm, height-110*mm, "DÉTAILS DU DEVIS:")
            c.setFont("Helvetica", 10)
            c.drawString(20*mm, height-120*mm, f"Date: {self.object.date_creation.strftime('%d/%m/%Y')}")
            c.drawString(20*mm, height-125*mm, f"Validité: {self.object.date_validite.strftime('%d/%m/%Y')}")
            
            # Total
            c.setFont("Helvetica-Bold", 14)
            c.drawString(20*mm, height-145*mm, f"TOTAL TTC: {self.object.total_ttc} {devise_symbole}")
            
            c.showPage()
            c.save()
            pdf_buffer.seek(0)
            return pdf_buffer
            
        except Exception as e:
            logger.error(f"Erreur génération PDF simple: {str(e)}")
            return None

    def get_lignes_devis(self):
        """Récupère les lignes du devis"""
        # Essayer différents noms de relation
        related_names = ['lignes', 'items', 'lignedevis_set', 'lignesdevis', 'ligne_devis']
        
        for name in related_names:
            if hasattr(self.object, name):
                return getattr(self.object, name).all()
        
        logger.warning("Aucun related_name trouvé pour les lignes du devis")
        return []

    def get_success_url(self):
        """URL de redirection après succès"""
        if hasattr(self, 'object') and self.object:
            return reverse_lazy("ventes:devis_detail", kwargs={"pk": self.object.pk})
        return reverse_lazy("ventes:devis_list")

    def test_email_configuration(self):
        """Méthode de test pour diagnostiquer la configuration email"""
        print("=== TEST CONFIGURATION EMAIL ===")
        
        # Vérifier les paramètres SMTP
        smtp_settings = ['EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD', 'DEFAULT_FROM_EMAIL']
        for setting in smtp_settings:
            value = getattr(settings, setting, 'NON DÉFINI')
            print(f"{setting}: {value}")
        
        # Tester la connexion SMTP
        try:
            import smtplib
            server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=10)
            server.ehlo()
            if getattr(settings, 'EMAIL_USE_TLS', False):
                server.starttls()
                print("✅ TLS activé")
            server.quit()
            print("✅ Connexion SMTP réussie")
            return True
        except Exception as e:
            print(f"❌ Erreur connexion SMTP: {e}")
            return False

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View

@method_decorator(csrf_exempt, name='dispatch')
class GetPrixProduitView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        produit_id = request.GET.get('produit_id')
        
        try:
            produit = Produit.objects.get(
                id=produit_id, 
                entreprise=request.entreprise
            )
            return JsonResponse({
                'success': True,
                'prix_unitaire': float(produit.prix_vente),
                'taux_tva': float(produit.taux_tva) if produit.taux_tva else 0.0
            })
        except Produit.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Produit non trouvé'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })



class DevisUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DevisBaseMixin, UpdateView
):
    model = Devis
    form_class = DevisForm
    template_name = "ventes/devis/form.html"
    permission_required = "ventes.change_devis"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["entreprise"] = self.request.entreprise
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.entreprise
        formset_kwargs = {"prefix": "form", "entreprise": entreprise}

        if self.request.POST:
            context["formset"] = LigneDevisFormSet(
                self.request.POST,
                instance=self.object,
                **formset_kwargs,
            )
        else:
            context["formset"] = LigneDevisFormSet(
                instance=self.object,
                **formset_kwargs,
            )

        context["devise_principale_symbole"] = self.get_devise_symbol(entreprise)
        return context

    def form_valid(self, form):
        context = self.get_context_data(form=form)
        formset = context["formset"]
        old_status = self.object.statut

        if not formset.is_valid():
            self.log_formset_errors(form, formset)
            messages.error(self.request, "Veuillez corriger les erreurs dans les articles du devis.")
            return self.render_to_response(context)

        with transaction.atomic():
            self.object = form.save(commit=False)
            self.object.save()
            formset.instance = self.object
            formset.save()

            self.create_audit_log(
                action="modification",
                description=f"Devis #{self.object.numero} modifié.",
                devis_instance=self.object,
            )

            if self.object.statut != old_status:
                self.create_status_history(
                    old_status=old_status,
                    new_status=self.object.statut,
                    comment="Statut modifié via le formulaire d'édition.",
                )
                self.create_audit_log(
                    action="changement_statut",
                    description=f"Statut de Devis #{self.object.numero} changé de '{old_status}' à '{self.object.statut}'.",
                    devis_instance=self.object,
                    details={"old_status": old_status, "new_status": self.object.statut},
                )

            messages.success(self.request, "Devis modifié avec succès.")
            return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("ventes:devis_detail", kwargs={"pk": self.object.pk})


class DevisDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DeleteView
):
    model = Devis
    template_name = "ventes/devis/confirm_delete.html"
    success_url = reverse_lazy("ventes:devis_list")
    permission_required = "ventes.delete_devis"

    def form_valid(self, form):
        devis_numero = self.object.numero
        devis_pk = self.object.pk

        with transaction.atomic():
            response = super().form_valid(form)
            # Créer l'audit log après la suppression
            DevisAuditLog.objects.create(
                devis=None,
                action="suppression",
                description=f"Devis #{devis_numero} (ID: {devis_pk}) supprimé.",
                performed_by=self.request.user,
                details={"devis_id": devis_pk, "devis_numero": devis_numero},
            )
            messages.success(self.request, f"Devis #{devis_numero} supprimé avec succès.")
            return response

class DevisAcceptView(LoginRequiredMixin, EntrepriseAccessMixin, View):
    def post(self, request, pk):
        devis = get_object_or_404(Devis, pk=pk, entreprise=request.entreprise)

        if devis.statut not in ["envoye", "brouillon"]:
            messages.error(
                request,
                f"Le devis doit être envoyé pour pouvoir être accepté. Statut actuel: {devis.get_statut_display()}",
            )
            return redirect(reverse("ventes:devis_detail", kwargs={"pk": pk}))

        ancien_statut = devis.statut
        devis.statut = "accepte"
        devis.updated_at = timezone.now()
        devis.save()

        DevisStatutHistory.objects.create(
            devis=devis,
            ancien_statut=ancien_statut,
            nouveau_statut="accepte",
            changed_by=request.user,
            commentaire="Devis accepté par le client",
        )

        DevisAuditLog.objects.create(
            devis=devis,
            action="changement_statut",
            description=f"Devis #{devis.numero} accepté par le client",
            performed_by=request.user,
            details={
                "ancien_statut": ancien_statut,
                "nouveau_statut": "accepte",
                "methode": "Interface client",
            },
        )

        messages.success(request, f"Le devis #{devis.numero} a été marqué comme accepté avec succès.")
        
        # Envoi de la notification d'acceptation
        email_sent = self.send_acceptance_notification(devis)
        
        if not email_sent:
            messages.warning(
                request,
                "Le devis a été accepté, mais l'envoi de la notification par email a échoué."
            )
            
        return redirect(reverse("ventes:devis_detail", kwargs={"pk": pk}))

    def send_acceptance_notification(self, devis):
        """
        Envoie une notification par email lorsque le devis est accepté
        """
        try:
            # Vérifications préalables
            if not devis.created_by or not devis.created_by.email:
                logger.warning(
                    f"Impossible d'envoyer la notification d'acceptation pour le devis {devis.numero}: "
                    f"Créateur du devis non trouvé ou sans email"
                )
                return False

            subject = f"✅ Devis #{devis.numero} accepté par le client"
            
            # Construction du message avec plus de détails
            message = f"""Bonjour,

Nous avons une bonne nouvelle ! Le devis suivant a été accepté par le client :

📋 **Détails du devis :**
- Numéro : {devis.numero}
- Client : {devis.client.nom if devis.client else 'Non spécifié'}
- Montant TTC : {devis.total_ttc if devis.total_ttc else '0.00'} {self.get_devise_symbol(devis.entreprise)}
- Date d'acceptation : {timezone.now().strftime('%d/%m/%Y à %H:%M')}

👤 **Informations client :**
- Nom : {devis.client.nom if devis.client else 'Non spécifié'}
- Email : {devis.client.email if devis.client and devis.client.email else 'Non spécifié'}
- Téléphone : {devis.client.telephone if devis.client and devis.client.telephone else 'Non spécifié'}

🚀 **Prochaine étape :**
Créez la facture associée à ce devis depuis l'interface de gestion des factures.

Cordialement,
Système de gestion {devis.entreprise.nom if devis.entreprise else ''}
"""

            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [devis.created_by.email]
            
            # Ajouter l'email de support si configuré
            if hasattr(settings, 'SUPPORT_EMAIL') and settings.SUPPORT_EMAIL:
                recipient_list.append(settings.SUPPORT_EMAIL)
            
            # Ajouter les administrateurs si nécessaire
            if hasattr(settings, 'ADMIN_EMAILS') and settings.ADMIN_EMAILS:
                recipient_list.extend(settings.ADMIN_EMAILS)

            # Utiliser EmailMessage pour plus de flexibilité
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=from_email,
                to=recipient_list,
                reply_to=[from_email],
            )
            
            # Optionnel : Ajouter le PDF du devis en pièce jointe
            try:
                pdf_context = {
                    "devis": devis,
                    "entreprise": devis.entreprise,
                    "client": devis.client,
                    "devise_principale_symbole": self.get_devise_symbol(devis.entreprise),
                }
                pdf = render_to_pdf("ventes/devis/print.html", pdf_context)
                if pdf:
                    email.attach(
                        f"devis_{devis.numero}_accepte.pdf",
                        pdf,
                        "application/pdf"
                    )
            except Exception as pdf_error:
                logger.warning(
                    f"Impossible de joindre le PDF pour la notification d'acceptation du devis {devis.numero}: {pdf_error}"
                )

            # Envoyer l'email
            email.send(fail_silently=False)
            
            logger.info(
                f"Notification d'acceptation envoyée avec succès pour le devis {devis.numero} "
                f"à {recipient_list}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Erreur critique lors de l'envoi de la notification d'acceptation pour le devis {devis.numero}: {str(e)}",
                exc_info=True
            )
            return False

    def get_devise_symbol(self, entreprise):
        """
        Méthode utilitaire pour récupérer le symbole de la devise
        """
        try:
            # Adaptez cette méthode selon votre implémentation
            if hasattr(entreprise, 'devise_principale') and entreprise.devise_principale:
                return entreprise.devise_principale.symbole
            return "€"  # Devise par défaut
        except:
            return "€"

# ==================== VUES POUR L'AFFICHAGE ====================


class DevisDetailView(
    LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DetailView
):
    model = Devis
    template_name = "ventes/devis/detail.html"
    permission_required = "ventes.view_devis"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_history"] = self.object.status_history.all()
        context["audit_logs"] = self.object.audit_logs.all()
        return context


class DevisAuditLogListView(
    LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, ListView
):
    model = DevisAuditLog
    template_name = "ventes/devis/audit_log_list.html"
    context_object_name = "audit_logs"
    permission_required = "ventes.view_audit_log"
    paginate_by = 25

    def get_queryset(self):
        return DevisAuditLog.objects.filter(devis__entreprise=self.request.entreprise).order_by(
            "-performed_at"
        )


class DevisPrintView(
    LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DetailView
):
    model = Devis
    template_name = "ventes/devis/print.html"
    permission_required = "ventes.view_devis"

    def get_queryset(self):
        return super().get_queryset().filter(entreprise=self.request.entreprise)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.entreprise
        devise_principale_symbole = ""
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            if config_saas.devise_principale:
                devise_principale_symbole = config_saas.devise_principale.symbole
        except ConfigurationSAAS.DoesNotExist:
            logger.warning(f"ConfigurationSAAS non trouvée pour l'entreprise {entreprise.nom}")
        except Devise.DoesNotExist:
            logger.warning(f"Devise principale non trouvée dans ConfigurationSAAS pour l'entreprise {entreprise.nom}")

        context["devise_principale_symbole"] = devise_principale_symbole
        return context

# Commandes, BonLivraison, Factures, Paiements (similar structure as Devis)

# ventes/views.py

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views import View
from django.shortcuts import render, get_object_or_404

# Importez les modèles nécessaires
from .models import PointDeVente, SessionPOS, VentePOS
from parametres.models import ConfigurationSAAS # <-- Importation ajoutée
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views import View
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField
from datetime import datetime

# Importez vos modèles
from .models import PointDeVente, SessionPOS, VentePOS, LigneVentePOS
from parametres.models import ConfigurationSAAS # Assurez-vous d'importer ConfigurationSAAS
from django.utils.translation import gettext_lazy as _


class POSDashboardView(LoginRequiredMixin, PermissionRequiredMixin, View):
    template_name = 'ventes/pos/dashboard.html'
    permission_required = 'ventes.view_pointdevente'
    
    def get(self, request, *args, **kwargs):
        point_de_vente = get_object_or_404(
            PointDeVente, 
            pk=kwargs.get('pk'), 
            entreprise=request.user.entreprise
        )
        
        session_ouverte = SessionPOS.objects.filter(
            point_de_vente=point_de_vente, 
            statut='ouverte'
        ).first()
        
        # Récupérer la devise principale de l'entreprise
        devise_principale = None
        devise_symbole = "" # Symbole par défaut si non trouvé
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=request.user.entreprise)
            if config_saas.devise_principale:
                devise_principale = config_saas.devise_principale
                devise_symbole = config_saas.devise_principale.symbole # Supposons que votre modèle Devise a un champ 'symbole'
        except ConfigurationSAAS.DoesNotExist:
            messages.warning(request, _("La configuration SAAS pour cette entreprise n'a pas été trouvée. La devise principale ne peut pas être affichée."))
        
        # --- Calcul des statistiques pour les cartes générales (_stats_cards.html) ---
        aujourdhui = datetime.now().date()

        # Expression pour calculer le total TTC d'une vente (utilisée pour les agrégations)
        total_ttc_expression_vente = ExpressionWrapper(
            Sum('items__montant_ht') + Sum('items__montant_tva') - F('remise'),
            output_field=DecimalField()
        )

        # Queryset des ventes du jour pour ce point de vente
        ventes_du_jour_qs = VentePOS.objects.filter(
            session__point_de_vente=point_de_vente,
            date__date=aujourdhui
        )

        # 1. Chiffre d'affaires du jour (CA Aujourd'hui)
        ca_aujourdhui_agg = ventes_du_jour_qs.annotate(
            # Annote chaque vente avec son total TTC calculé
            total_ttc_calc=total_ttc_expression_vente
        ).aggregate(
            chiffre_affaires=Sum('total_ttc_calc') # Puis somme ces totaux TTC
        )
        chiffre_affaires_jour = ca_aujourdhui_agg['chiffre_affaires'] or 0 

        # 2. Nombre de Ventes Aujourd'hui
        nombre_ventes_jour = ventes_du_jour_qs.count()

        # 3. Articles Vendus Aujourd'hui
        articles_vendus_agg = LigneVentePOS.objects.filter(
            vente__session__point_de_vente=point_de_vente,
            vente__date__date=aujourdhui
        ).aggregate(
            total_quantite=Sum('quantite')
        )
        articles_vendus_jour = articles_vendus_agg['total_quantite'] or 0


        # --- Performance de l'utilisateur pour la session active ---
        # Ces statistiques sont pertinentes seulement si une session est ouverte
        performance_utilisateur_session = {
            'ca_session': 0,
            'nombre_ventes_session': 0,
            'articles_vendus_session': 0,
        }
        if session_ouverte:
            # Filtrer les ventes spécifiquement pour la session ouverte
            ventes_session_utilisateur_qs = VentePOS.objects.filter(
                session=session_ouverte,
                # L'utilisateur est implicitement celui de la session_ouverte
            )

            ca_session_agg = ventes_session_utilisateur_qs.annotate(
                total_ttc_calc=total_ttc_expression_vente
            ).aggregate(
                chiffre_affaires=Sum('total_ttc_calc')
            )
            performance_utilisateur_session['ca_session'] = ca_session_agg['chiffre_affaires'] or 0

            performance_utilisateur_session['nombre_ventes_session'] = ventes_session_utilisateur_qs.count()

            articles_vendus_session_agg = LigneVentePOS.objects.filter(
                vente__session=session_ouverte
            ).aggregate(
                total_quantite=Sum('quantite')
            )
            performance_utilisateur_session['articles_vendus_session'] = articles_vendus_session_agg['total_quantite'] or 0


        # Ventes récentes (dernières 5 ventes - cette partie était déjà fonctionnelle)
        recent_ventes = VentePOS.objects.filter(
            session__point_de_vente=point_de_vente
        ).select_related('session', 'client').order_by('-date')[:5]
        
        context = {
            'point_de_vente': point_de_vente,
            'session_ouverte': session_ouverte,
            'recent_ventes': recent_ventes,
            'devise_principale': devise_principale, # L'objet Devise complet
            'devise_principale_symbole': devise_symbole, # Le symbole seul pour plus de facilité dans le template
            
            # Statistiques passées au template
            'ca_aujourdhui': chiffre_affaires_jour,
            'nombre_ventes_jour': nombre_ventes_jour,
            'articles_vendus_jour': articles_vendus_jour,

            'performance_utilisateur_session': performance_utilisateur_session, # Nouvelle variable pour la performance
        }
        return render(request, self.template_name, context)


    
class OuvrirSessionPOSView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'ventes.add_sessionpos'
    
    def post(self, request, *args, **kwargs):
        point_de_vente = get_object_or_404(
            PointDeVente, 
            pk=kwargs.get('pk'), 
            entreprise=request.user.entreprise
        )
        
        # Vérifier s'il y a déjà une session ouverte
        if SessionPOS.objects.filter(point_de_vente=point_de_vente, statut='ouverte').exists():
            messages.error(request, "Une session est déjà ouverte pour ce point de vente.")
            return redirect('ventes:pos_dashboard', pk=point_de_vente.pk)  # Retirer le point-virgule
        
        fonds_ouverture = request.POST.get('fonds_ouverture', 0)
        try:
            fonds_ouverture = float(fonds_ouverture)
        except ValueError:
            messages.error(request, "Montant invalide pour le fonds d'ouverture.")
            return redirect('ventes:pos_dashboard', pk=point_de_vente.pk)
        
        session = SessionPOS.objects.create(
            point_de_vente=point_de_vente,
            utilisateur=request.user,
            fonds_ouverture=fonds_ouverture,
            statut='ouverte'
        )
        
        messages.success(request, "Session ouverte avec succès.")
        return redirect('ventes:pos_dashboard', pk=point_de_vente.pk)
# ventes/views.py
from django.utils import timezone
from decimal import Decimal, InvalidOperation

# ventes/views.py

from django.views.generic import View, DetailView
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from decimal import Decimal, InvalidOperation # Assurez-vous d'importer InvalidOperation

from parametres.models import ConfigurationSAAS # <-- Ajouté
# Vous pourriez aussi avoir besoin de :
# from .models import VentePOS, PaiementPOS, LigneVentePOS # Si non déjà importé


# --- Vue de fermeture de session POS ---
class FermerSessionPOSView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'ventes.change_sessionpos'
    
    def post(self, request, *args, **kwargs):
        session = get_object_or_404(
            SessionPOS, 
            pk=kwargs.get('session_pk'),
            point_de_vente__entreprise=request.user.entreprise,
            statut='ouverte'
        )
        
        fonds_fermeture = request.POST.get('fonds_fermeture', 0)
        try:
            fonds_fermeture = Decimal(fonds_fermeture)
        except (ValueError, InvalidOperation):
            messages.error(request, "Montant invalide pour le fonds de fermeture.")
            return redirect('ventes:pos_dashboard', pk=session.point_de_vente.pk)
        
        # --- Récupération du symbole de la devise ---
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=request.user.entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            devise_symbole = "€"
        # ---------------------------------------------

        # Calcul théorique de ce qui devrait être en caisse
        fonds_theorique = session.fonds_ouverture + session.total_especes
        
        # Calcul de l'écart
        ecart = fonds_fermeture - fonds_theorique
        
        # Enregistrement de la session
        session.fonds_fermeture = fonds_fermeture
        session.date_fermeture = timezone.now()
        session.statut = 'fermee'
        session.save()
        
        # Création automatique de l'écart de caisse si nécessaire
        if ecart != 0:
            type_ecart = 'excedent' if ecart > 0 else 'manquant'
            
            EcartCaisse.objects.create(
                session=session,
                caissier=session.utilisateur,
                type_ecart=type_ecart,
                montant=abs(ecart),
                motif=f"Écart automatique lors de la fermeture de session. "
                      f"Fonds théorique: {fonds_theorique}{devise_symbole}, " # <-- Utilisation de devise_symbole
                      f"Fonds réel: {fonds_fermeture}{devise_symbole}",     # <-- Utilisation de devise_symbole
                created_by=request.user
            )
            
            messages.info(request, 
                f"Session fermée avec un écart de {abs(ecart)}{devise_symbole} ({type_ecart}).") # <-- Utilisation de devise_symbole
        else:
            messages.success(request, "Session fermée avec succès. Aucun écart détecté.")
        
        return redirect('ventes:pos_dashboard', pk=session.point_de_vente.pk)
   

# --- Vue du résumé de session POS ---
class ResumeSessionView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    template_name = 'ventes/pos/resume_fermeture.html'
    permission_required = 'ventes.view_sessionpos'
    context_object_name = 'session'
    
    def get_queryset(self):
        return SessionPOS.objects.filter(
            point_de_vente__entreprise=self.request.user.entreprise
        ).select_related(
            'point_de_vente', 'utilisateur'
        ).prefetch_related(
            'ventes', 'ventes__client', 'ventes__paiementpos_set',
            'ecarts_caisse', 'ecarts_caisse__created_by'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # --- Récupération du symbole de la devise ---
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            devise_symbole = "€"
        # ---------------------------------------------

        context['devise_symbole'] = devise_symbole # <-- Ajout au contexte
        return context 
   
   
   
    
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views import View
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.db.models import F
from datetime import datetime

from ventes.models import VentePOS, LigneVentePOS, SessionPOS, PointDeVente
from ventes.forms import VentePOSForm, LigneVentePOSFormSet
from parametres.models import ConfigurationSAAS

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views import View
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.db.models import F
from datetime import datetime
from django.utils import timezone

from ventes.models import VentePOS, LigneVentePOS, SessionPOS, PointDeVente
from ventes.forms import VentePOSForm, LigneVentePOSFormSet
from parametres.models import ConfigurationSAAS

from django.db import transaction
from django.db.models import F
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from decimal import Decimal
from datetime import datetime

from ventes.models import VentePOS, LigneVentePOS, SessionPOS, PointDeVente, PaiementPOS
from ventes.forms import VentePOSForm, LigneVentePOSFormSet, PaiementPOSForm
from parametres.models import ConfigurationSAAS, Devise


from django.db import transaction
from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class NouvelleVentePOSView(LoginRequiredMixin, PermissionRequiredMixin, View):
    template_name = 'ventes/pos/nouvelle_vente.html'
    permission_required = 'ventes.add_ventepos'
    
    def get_context_data(self, request, pk, session_pk):
        point_de_vente = get_object_or_404(
            PointDeVente, 
            pk=pk,
            entreprise=request.user.entreprise
        )
        
        session = get_object_or_404(
            SessionPOS, 
            pk=session_pk,
            point_de_vente=point_de_vente,
            statut='ouverte'
        )
        
        try:
            config_saas = ConfigurationSAAS.objects.filter(entreprise=request.user.entreprise).first()
            devise_principale = config_saas.devise_principale if config_saas else None
            devise_principale_symbole = devise_principale.symbole if devise_principale else "€"
        except (ConfigurationSAAS.DoesNotExist, Devise.DoesNotExist):
            devise_principale = None
            devise_principale_symbole = "€"
        
        form = VentePOSForm(entreprise=request.user.entreprise)
        formset = LigneVentePOSFormSet(queryset=LigneVentePOS.objects.none(), entreprise=request.user.entreprise)
        
        context = {
            'point_de_vente': point_de_vente,
            'session': session,
            'form': form,
            'formset': formset,
            'devise_principale': devise_principale,
            'devise_principale_symbole': devise_principale_symbole,
        }
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(request, kwargs.get('pk'), kwargs.get('session_pk'))
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        point_de_vente = get_object_or_404(
            PointDeVente, 
            pk=kwargs.get('pk'),
            entreprise=request.user.entreprise
        )
        
        session = get_object_or_404(
            SessionPOS, 
            pk=kwargs.get('session_pk'),
            point_de_vente=point_de_vente,
            statut='ouverte'
        )
        
        try:
            config_saas = ConfigurationSAAS.objects.filter(entreprise=request.user.entreprise).first()
            devise_principale = config_saas.devise_principale if config_saas else None
        except ConfigurationSAAS.DoesNotExist:
            devise_principale = None
        
        form = VentePOSForm(request.POST, entreprise=request.user.entreprise)
        formset = LigneVentePOSFormSet(request.POST, entreprise=request.user.entreprise)
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Calcul des totaux
                    total_vente = Decimal('0.00')
                    for ligne_form in formset:
                        cleaned_data = ligne_form.cleaned_data
                        if not cleaned_data.get('DELETE', False) and cleaned_data.get('quantite', 0) > 0:
                            prix_unitaire = cleaned_data.get('prix_unitaire', Decimal('0.00'))
                            quantite = cleaned_data.get('quantite', 0)
                            total_ligne = prix_unitaire * quantite
                            total_vente += total_ligne

                    # Vérifier les stocks
                    produits_insuffisants = []
                    for ligne_form in formset:
                        cleaned_data = ligne_form.cleaned_data
                        if (cleaned_data.get('produit') and 
                            not cleaned_data.get('DELETE', False) and 
                            cleaned_data.get('quantite', 0) > 0):
                            
                            produit = cleaned_data['produit']
                            quantite_demandee = cleaned_data['quantite']
                            produit_actualise = Produit.objects.get(pk=produit.pk)
                            
                            if produit_actualise.stock < quantite_demandee:
                                produits_insuffisants.append(
                                    f"{produit.nom} (Stock: {produit_actualise.stock}, Demandé: {quantite_demandee})"
                                )
                    
                    if produits_insuffisants:
                        raise Exception(
                            _("Stock insuffisant pour: ") + ", ".join(produits_insuffisants)
                        )
                    
                    # Sauvegarde de la vente
                    vente = form.save(commit=False)
                    vente.session = session
                    vente.numero = f"V{timezone.now().strftime('%Y%m%d%H%M%S')}"
                    vente.devise = devise_principale
                    vente.save()
                    
                    # Enregistrer les lignes de vente
                    for ligne_form in formset:
                        cleaned_data = ligne_form.cleaned_data
                        if (cleaned_data.get('produit') and 
                            not cleaned_data.get('DELETE', False) and 
                            cleaned_data.get('quantite', 0) > 0):
                            
                            produit = cleaned_data['produit']
                            quantite_demandee = cleaned_data['quantite']
                            prix_unitaire = cleaned_data.get('prix_unitaire', Decimal('0.00'))
                            
                            ligne = ligne_form.save(commit=False)
                            ligne.vente = vente
                            ligne.prix_unitaire = prix_unitaire
                            ligne.quantite = quantite_demandee
                            
                            # Sauvegarder pour déclencher le calcul automatique
                            ligne.save()
                            
                            # Mettre à jour le stock
                            Produit.objects.filter(pk=produit.pk).update(
                                stock=F('stock') - quantite_demandee
                            )

                    # Recalculer le total après sauvegarde de toutes les lignes
                    vente.refresh_from_db()
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({
                            'success': True,
                            'vente_id': vente.id,
                            'numero': vente.numero,
                            'total_vente': float(vente.total_ht),
                            'message': _("Vente enregistrée avec succès"),
                            'redirect_url': reverse('ventes:paiement_vente', kwargs={'vente_id': vente.id})
                        })
                    else:
                        return HttpResponseRedirect(reverse('ventes:paiement_vente', kwargs={'vente_id': vente.id}))
                    
            except Exception as e:
                logger.error(f"Erreur création vente: {str(e)}")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': str(e)
                    })
                else:
                    messages.error(request, str(e))
                    context = self.get_context_data(request, kwargs.get('pk'), kwargs.get('session_pk'))
                    context['form'] = form
                    context['formset'] = formset
                    return render(request, self.template_name, context)

        else:
            errors = []
            if form.errors:
                for field, error_list in form.errors.items():
                    for error in error_list:
                        errors.append(f"{field}: {error}")
            
            if formset.errors:
                for i, form_errors in enumerate(formset.errors):
                    if form_errors:
                        for field, error in form_errors.items():
                            errors.append(f"Ligne {i+1} - {field}: {error}")
            
            error_message = '; '.join(errors)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': error_message
                })
            else:
                messages.error(request, error_message)
                context = self.get_context_data(request, kwargs.get('pk'), kwargs.get('session_pk'))
                context['form'] = form
                context['formset'] = formset
                return render(request, self.template_name, context)
            
# ventes/views.py
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
# ventes/views.py
class NouvelleVenteSimpleView(LoginRequiredMixin, PermissionRequiredMixin, View):
    permission_required = 'ventes.add_ventepos'
    
    def get(self, request, pk):
        point_de_vente = get_object_or_404(
            PointDeVente, 
            pk=pk,
            entreprise=request.user.entreprise
        )
        
        # Vérifier que l'utilisateur a accès à ce POS
        if not request.user.can_access_pos(point_de_vente):
            raise PermissionDenied("Accès refusé à ce point de vente")
        
        # Trouver ou créer une session ouverte - CORRECTION: utiliser 'utilisateur'
        session, created = SessionPOS.objects.get_or_create(
            point_de_vente=point_de_vente,
            utilisateur=request.user,  # ← CORRECTION ICI
            statut='ouverte',
            defaults={
                'date_ouverture': timezone.now(),
                'fonds_ouverture': Decimal('0.00')
            }
        )
        
        # Rediriger vers la page de vente avec la session
        return redirect('ventes:nouvelle_vente_pos', pk=point_de_vente.pk, session_pk=session.pk)
# ventes/views.py
import logging
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Q
import json
logger = logging.getLogger(__name__)
# ventes/views.py (version étendue)
@require_GET
@csrf_exempt
@login_required
def api_search_by_barcode(request):
    """API pour rechercher un produit par code-barres ou par nom"""
    search_term = request.GET.get('barcode', '').strip()
    logger.info(f"Recherche: {search_term}")
    
    if not search_term:
        logger.warning("Terme de recherche vide reçu")
        return JsonResponse({
            'success': False,
            'message': 'Terme de recherche requis'
        }, status=400)
    
    try:
        from STOCK.models import Produit
        
        # Vérification de l'entreprise
        if not hasattr(request.user, 'entreprise') or not request.user.entreprise:
            logger.error(f"Utilisateur {request.user} n'a pas d'entreprise associée")
            return JsonResponse({
                'success': False,
                'message': 'Aucune entreprise associée à cet utilisateur'
            }, status=400)
        
        logger.info(f"Recherche dans l'entreprise: {request.user.entreprise}")
        
        # Recherche d'abord par code-barre
        produits = Produit.objects.filter(
            Q(code_barre_numero=search_term),
            entreprise=request.user.entreprise,
            actif=True
        )
        
        # Si aucun résultat par code-barre, recherche par nom
        if not produits.exists():
            produits = Produit.objects.filter(
                Q(nom__icontains=search_term),
                entreprise=request.user.entreprise,
                actif=True
            )[:5]  # Limiter à 5 résultats pour la recherche par nom
        
        logger.info(f"{produits.count()} produit(s) trouvé(s) pour: {search_term}")
        
        if produits.exists():
            # Si recherche par nom, retourner tous les résultats
            if produits.count() > 1:
                product_list = []
                for produit in produits:
                    photo_url = ''
                    if produit.photo and hasattr(produit.photo, 'url'):
                        photo_url = request.build_absolute_uri(produit.photo.url)
                    
                    product_list.append({
                        'id': produit.id,
                        'nom': produit.nom,
                        'code_barre': produit.code_barre_numero or '',
                        'prix_vente': float(produit.prix_vente) if produit.prix_vente else 0.0,
                        'taux_tva': float(produit.taux_tva) if produit.taux_tva else 20.0,
                        'stock': produit.stock,
                        'photo_url': photo_url,
                        'unite_mesure': produit.libelle or ''
                    })
                
                return JsonResponse({
                    'success': True,
                    'multiple': True,
                    'products': product_list,
                    'message': f'{len(product_list)} produits trouvés'
                })
            else:
                # Un seul produit trouvé
                produit = produits.first()
                photo_url = ''
                if produit.photo and hasattr(produit.photo, 'url'):
                    photo_url = request.build_absolute_uri(produit.photo.url)
                
                logger.info(f"Produit trouvé: {produit.nom} (ID: {produit.id})")
                
                return JsonResponse({
                    'success': True,
                    'multiple': False,
                    'product': {
                        'id': produit.id,
                        'nom': produit.nom,
                        'code_barre': produit.code_barre_numero or '',
                        'prix_vente': float(produit.prix_vente) if produit.prix_vente else 0.0,
                        'taux_tva': float(produit.taux_tva) if produit.taux_tva else 20.0,
                        'stock': produit.stock,
                        'photo_url': photo_url,
                        'unite_mesure': produit.libelle or ''
                    }
                })
        else:
            logger.warning(f"Aucun produit trouvé pour: {search_term}")
            return JsonResponse({
                'success': False,
                'message': 'Produit non trouvé'
            }, status=404)
            
    except ImportError as e:
        logger.error(f"Erreur d'importation: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur: Module STOCK non trouvé'
        }, status=500)
    except Exception as e:
        logger.error(f"Erreur inattendue: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Erreur serveur: {str(e)}'
        }, status=500)
        
class PaiementVenteView(LoginRequiredMixin, View):
    """Vue pour le paiement de la vente"""
    template_name = 'ventes/pos/paiement.html'
    
    def get(self, request, *args, **kwargs):
        vente = get_object_or_404(
            VentePOS, 
            pk=kwargs.get('vente_id'),
            session__point_de_vente__entreprise=request.user.entreprise
        )
        
        # DEBUG: Vérifier le calcul du total
        logger.info(f"Paiement - Vente {vente.numero}")
        logger.info(f"Paiement - Nombre d'items: {vente.items.count()}")
        logger.info(f"Paiement - Total HT: {vente.total_ht}")
        
        # Calculer le montant déjà payé
        montant_deja_paye = vente.paiementpos_set.aggregate(
            total=Sum('montant')
        )['total'] or 0
        
        # Utiliser le total HT comme base pour les paiements
        montant_restant = vente.total_ht - montant_deja_paye
        
        # Récupérer la devise
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=request.user.entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            devise_symbole = "€"
        
        # Obtenir le nom du client
        nom_client = "NON RENSEIGNÉ"
        if vente.client:
            nom_client = vente.client.nom
            if hasattr(vente.client, 'get_full_name') and callable(getattr(vente.client, 'get_full_name')):
                nom_client = vente.client.get_full_name()
            elif hasattr(vente.client, 'nom_complet'):
                nom_client = vente.client.nom_complet
            elif hasattr(vente.client, 'full_name'):
                nom_client = vente.client.full_name
        
        form = PaiementPOSForm()
        
        context = {
            'vente': vente,
            'form': form,
            'montant_deja_paye': montant_deja_paye,
            'montant_restant': montant_restant,
            'devise_symbole': devise_symbole,
            'nom_client': nom_client,
        }
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        vente = get_object_or_404(
            VentePOS, 
            pk=kwargs.get('vente_id'),
            session__point_de_vente__entreprise=request.user.entreprise
        )
        
        form = PaiementPOSForm(request.POST)
        
        if form.is_valid():
            with transaction.atomic():
                paiement = form.save(commit=False)
                paiement.vente = vente
                paiement.session = vente.session
                paiement.save()
                
                # Enregistrement comptable
                try:
                    ecriture = paiement.enregistrer_ecriture_comptable()
                    if ecriture:
                        messages.success(request, _("Paiement et écriture comptable enregistrés avec succès."))
                    else:
                        messages.warning(request, _("Paiement enregistré mais erreur lors de l'écriture comptable."))
                except Exception as e:
                    messages.warning(request, _("Paiement enregistré mais erreur comptable: {}").format(str(e)))
                
                # Vérifier si la vente est complètement payée
                montant_total_paye = vente.paiementpos_set.aggregate(
                    total=Sum('montant')
                )['total'] or 0
                
                if montant_total_paye >= vente.total_ht:
                    vente.est_payee = True
                    vente.save()
                    messages.success(request, _("Vente complètement payée."))
                else:
                    messages.success(request, _("Paiement partiel enregistré."))
                
                # Générer le ticket si demandé
                if request.POST.get('imprimer_ticket'):
                    return redirect('ventes:impression_ticket', vente_id=vente.id)
                
                return redirect('ventes:pos_dashboard', pk=vente.session.point_de_vente.id)
        
        # En cas d'erreur du formulaire
        montant_deja_paye = vente.paiementpos_set.aggregate(
            total=Sum('montant')
        )['total'] or 0
        montant_restant = vente.total_ht - montant_deja_paye
        
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=request.user.entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            devise_symbole = "€"
        
        nom_client = "NON RENSEIGNÉ"
        if vente.client:
            nom_client = vente.client.nom
            if hasattr(vente.client, 'get_full_name') and callable(getattr(vente.client, 'get_full_name')):
                nom_client = vente.client.get_full_name()
            elif hasattr(vente.client, 'nom_complet'):
                nom_client = vente.client.nom_complet
            elif hasattr(vente.client, 'full_name'):
                nom_client = vente.client.full_name
        
        context = {
            'vente': vente,
            'form': form,
            'montant_deja_paye': montant_deja_paye,
            'montant_restant': montant_restant,
            'devise_symbole': devise_symbole,
            'nom_client': nom_client,
        }
        return render(request, self.template_name, context)

class ImpressionTicketView(LoginRequiredMixin, View):
    """Générer le HTML du ticket pour impression automatique"""
    
    def get(self, request, *args, **kwargs):
        vente = get_object_or_404(
            VentePOS, 
            pk=kwargs.get('vente_id'),
            session__point_de_vente__entreprise=request.user.entreprise
        )
        
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=request.user.entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            devise_symbole = "€"
        
        # Récupérer les lignes de vente
        try:
            if hasattr(vente, 'lignes'):
                lignes_vente = vente.lignes.all()
            elif hasattr(vente, 'items'):
                lignes_vente = vente.items.all()
            elif hasattr(vente, 'ligneventepos_set'):
                lignes_vente = vente.ligneventepos_set.all()
            else:
                from ventes.models import LigneVentePOS
                lignes_vente = LigneVentePOS.objects.filter(vente=vente)
        except:
            lignes_vente = []
        
        # Récupérer les paiements
        try:
            if hasattr(vente, 'paiements'):
                paiements = vente.paiements.all()
            elif hasattr(vente, 'paiementpos_set'):
                paiements = vente.paiementpos_set.all()
            else:
                from ventes.models import PaiementPOS
                paiements = PaiementPOS.objects.filter(vente=vente)
        except:
            paiements = []
        
        # Obtenir le nom du client de manière sécurisée
        nom_client = "NON RENSEIGNÉ"
        if vente.client:
            nom_client = vente.client.nom
            if hasattr(vente.client, 'get_full_name') and callable(getattr(vente.client, 'get_full_name')):
                nom_client = vente.client.get_full_name()
            elif hasattr(vente.client, 'nom_complet'):
                nom_client = vente.client.nom_complet
            elif hasattr(vente.client, 'full_name'):
                nom_client = vente.client.full_name
        
        # Récupérer la session ouverte actuelle pour le point de vente
        session_ouverte = None
        point_de_vente = vente.session.point_de_vente
        
        try:
            session_ouverte = SessionPOS.objects.filter(
                point_de_vente=point_de_vente,
                statut='ouverte',
                utilisateur=request.user
            ).first()
        except:
            pass
        
        context = {
            'vente': vente,
            'lignes_vente': lignes_vente,
            'paiements': paiements,
            'devise_symbole': devise_symbole,
            'date_impression': timezone.now(),
            'entreprise': request.user.entreprise,
            'nom_client': nom_client,
            'point_de_vente': point_de_vente,  # Ajout du point de vente
            'session_ouverte': session_ouverte,  # Ajout de la session ouverte
        }
        
        response = render(request, 'ventes/pos/ticket_impression.html', context)
        
        # Ajouter un script pour l'impression automatique
        if 'print' in request.GET:
            response['Refresh'] = '2; url=javascript:window.print()'
        
        return response


class GenererTicketPDFView(LoginRequiredMixin, View):
    """Générer un ticket PDF pour une vente"""
    
    def get(self, request, *args, **kwargs):
        vente = get_object_or_404(
            VentePOS, 
            pk=kwargs.get('vente_id'),
            session__point_de_vente__entreprise=request.user.entreprise
        )
        
        # Récupérer la devise
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=request.user.entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            devise_symbole = "€"
        
        context = {
            'vente': vente,
            'lignes_vente': vente.ligneventepos_set.all(),
            'paiements': vente.paiementpos_set.all(),
            'devise_symbole': devise_symbole,
            'date_impression': timezone.now(),
            'entreprise': request.user.entreprise,
        }
        
        # Rendre le template HTML
        html_string = render_to_string('ventes/pos/ticket_pdf.html', context)
        
        # Générer le PDF
        html = HTML(string=html_string)
        result = html.write_pdf()
        
        # Créer la réponse HTTP
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="ticket_vente_{vente.numero}.pdf"'
        response.write(result)
        
        return response

# ventes/views.py
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.contrib import messages
from django.db.models import Sum, Count, F, Q, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import datetime, timedelta  # ← Ajouter timedelta
from decimal import Decimal
import json

class StatistiquesVentesView(LoginRequiredMixin, View):
    template_name = 'ventes/statistiques/ventes.html'

    def get(self, request, *args, **kwargs):
        # Récupérer les paramètres de filtre
        date_debut = request.GET.get('date_debut')
        date_fin = request.GET.get('date_fin')
        point_de_vente_id = request.GET.get('point_de_vente')
        caissier_id = request.GET.get('caissier')
        
        # Dates par défaut
        aujourdhui = timezone.now().date()  # ← Utiliser timezone
        debut_mois = aujourdhui.replace(day=1)
        debut_annee = aujourdhui.replace(month=1, day=1)
        
        # Définir la période de filtrage
        if date_debut and date_fin:
            try:
                date_debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
                date_fin = datetime.strptime(date_fin, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, "Format de date invalide")
                date_debut = debut_mois
                date_fin = aujourdhui
        else:
            date_debut = debut_mois
            date_fin = aujourdhui

        # Récupérer la devise principale
        devise_symbole = "€"
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=request.user.entreprise)
            if config_saas.devise_principale:
                devise_symbole = config_saas.devise_principale.symbole
        except ConfigurationSAAS.DoesNotExist:
            messages.warning(request, "Configuration de devise non trouvée")

        # Filtre de base
        filtre_base = {
            'session__point_de_vente__entreprise': request.user.entreprise,
            'date__date__range': [date_debut, date_fin]
        }

        # Appliquer les filtres supplémentaires
        if point_de_vente_id:
            filtre_base['session__point_de_vente_id'] = point_de_vente_id
        
        if caissier_id:
            filtre_base['session__utilisateur_id'] = caissier_id

        # --- Statistiques globales ---
        def get_stats_ventes(filtre_supp=None):
            filtre_complet = filtre_base.copy()
            if filtre_supp:
                filtre_complet.update(filtre_supp)
            
            agg = VentePOS.objects.filter(**filtre_complet).aggregate(
                total_ventes=Coalesce(
                    Sum(F('items__montant_ht') + F('items__montant_tva') - F('remise')),
                    Decimal('0.00'),
                    output_field=DecimalField(max_digits=12, decimal_places=2)
                ),
                nombre_ventes=Count('id', distinct=True),
                nombre_clients=Count('client', distinct=True)
            )
            
            total = agg['total_ventes'] or Decimal('0')
            count = agg['nombre_ventes'] or 0
            clients = agg['nombre_clients'] or 0
            panier_moyen = total / count if count > 0 else Decimal('0')
            
            return {
                'total_ventes': total,
                'nombre_ventes': count,
                'nombre_clients': clients,
                'panier_moyen': panier_moyen
            }

        # Statistiques pour différentes périodes
        stats_periode = get_stats_ventes()
        stats_jour = get_stats_ventes({'date__date': aujourdhui})
        stats_mois = get_stats_ventes({'date__date__gte': debut_mois})
        stats_annee = get_stats_ventes({'date__date__gte': debut_annee})

        # --- Statistiques par Point de Vente ---
        stats_par_pos = VentePOS.objects.filter(**filtre_base).values(
            'session__point_de_vente__id',
            'session__point_de_vente__nom',
            'session__point_de_vente__code'
        ).annotate(
            total_ventes=Coalesce(
                Sum(F('items__montant_ht') + F('items__montant_tva') - F('remise')),
                Decimal('0.00'),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            ),
            nombre_ventes=Count('id', distinct=True),
            caissiers_distincts=Count('session__utilisateur', distinct=True)
        ).order_by('-total_ventes')

        # Calculer le panier moyen pour chaque POS
        for pos in stats_par_pos:
            if pos['nombre_ventes'] > 0:
                pos['panier_moyen'] = pos['total_ventes'] / pos['nombre_ventes']
            else:
                pos['panier_moyen'] = Decimal('0.00')

        # --- Statistiques par Caissier ---
        stats_par_caissier = VentePOS.objects.filter(**filtre_base).values(
            'session__utilisateur__id',
            'session__utilisateur__first_name',
            'session__utilisateur__last_name',
            'session__utilisateur__username',
            'session__point_de_vente__nom'
        ).annotate(
            total_ventes=Coalesce(
                Sum(F('items__montant_ht') + F('items__montant_tva') - F('remise')),
                Decimal('0.00'),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            ),
            nombre_ventes=Count('id', distinct=True)
        ).order_by('-total_ventes')

        # Calculer le panier moyen pour chaque caissier
        for caissier in stats_par_caissier:
            if caissier['nombre_ventes'] > 0:
                caissier['panier_moyen'] = caissier['total_ventes'] / caissier['nombre_ventes']
            else:
                caissier['panier_moyen'] = Decimal('0.00')

        # --- Meilleurs articles avec affichage combiné ---
        meilleurs_articles = LigneVentePOS.objects.filter(
            vente__session__point_de_vente__entreprise=request.user.entreprise,
            vente__date__date__range=[date_debut, date_fin]
        ).values(
            'produit__nom',
            'produit__libelle'
        ).annotate(
            quantite_vendue=Sum('quantite'),
            montant_total=Sum(F('montant_ht') + F('montant_tva')),
            nombre_ventes=Count('vente', distinct=True)
        ).order_by('-quantite_vendue')[:20]

        # Ajouter un champ combiné pour l'affichage
        for article in meilleurs_articles:
            nom = article['produit__nom'] or ''
            libelle = article['produit__libelle'] or ''
            if nom and libelle:
                article['nom_complet'] = f"{nom} ({libelle})"
            elif nom:
                article['nom_complet'] = nom
            elif libelle:
                article['nom_complet'] = libelle
            else:
                article['nom_complet'] = "Article sans nom"

        # --- Évolution des ventes (30 derniers jours) ---
        evolution_data = []
        for i in range(30, -1, -1):
            date_courante = aujourdhui - timedelta(days=i)
            stats_jour = VentePOS.objects.filter(
                session__point_de_vente__entreprise=request.user.entreprise,
                date__date=date_courante
            ).aggregate(
                total=Coalesce(
                    Sum(F('items__montant_ht') + F('items__montant_tva') - F('remise')),
                    Decimal('0.00')
                )
            )
            evolution_data.append({
                'date': date_courante.strftime('%Y-%m-%d'),
                'total': float(stats_jour['total'] or 0)
            })

        # --- Données pour les filtres ---
        points_de_vente = PointDeVente.objects.filter(
            entreprise=request.user.entreprise,
            actif=True
        )
        
        caissiers = User.objects.filter(
            entreprise=request.user.entreprise,
            role='CAISSIER',
            est_actif=True
        )

        # Préparer les données pour les graphiques
        chart_data = {
            'evolution': evolution_data,
            'par_pos': [
                {
                    'nom': f"{pos['session__point_de_vente__code']} - {pos['session__point_de_vente__nom']}",
                    'total': float(pos['total_ventes'] or 0)
                } for pos in stats_par_pos
            ],
            'par_caissier': [
                {
                    'nom': f"{c['session__utilisateur__first_name']} {c['session__utilisateur__last_name']}",
                    'total': float(c['total_ventes'] or 0),
                    'pos': c['session__point_de_vente__nom']
                } for c in stats_par_caissier
            ]
        }

        context = {
            # Filtres
            'date_debut': date_debut.strftime('%Y-%m-%d') if hasattr(date_debut, 'strftime') else date_debut,
            'date_fin': date_fin.strftime('%Y-%m-%d') if hasattr(date_fin, 'strftime') else date_fin,
            'point_de_vente_id': point_de_vente_id,
            'caissier_id': caissier_id,
            'points_de_vente': points_de_vente,
            'caissiers': caissiers,
            
            # Statistiques
            'stats_periode': stats_periode,
            'stats_jour': stats_jour,
            'stats_mois': stats_mois,
            'stats_annee': stats_annee,
            'stats_par_pos': stats_par_pos,
            'stats_par_caissier': stats_par_caissier,
            'meilleurs_articles': meilleurs_articles,
            'devise_symbole': devise_symbole,
            
            # Données pour graphiques
            'chart_data_json': json.dumps(chart_data),
            'evolution_data_json': json.dumps(evolution_data),
        }
        
        return render(request, self.template_name, context)

class StatistiquesFacturationView(LoginRequiredMixin, PermissionRequiredMixin, View):
    template_name = 'ventes/statistiques/facturation.html'
    permission_required = 'ventes.view_statistiques'
    
    def get(self, request, *args, **kwargs):
        # Statistiques de facturation
        aujourdhui = datetime.now().date()
        debut_mois = aujourdhui.replace(day=1)
        debut_annee = aujourdhui.replace(month=1, day=1)
        
        # Factures impayées
        factures_impayees = Facture.objects.filter(
            entreprise=request.user.entreprise,
            statut__in=['valide', 'paye_partiel']
        ).aggregate(
            montant_total=Sum('total_ttc'),
            reste_a_payer=Sum('reste_a_payer'),
            nombre_factures=Count('id')
        )
        
        # Factures par statut
        factures_par_statut = Facture.objects.filter(
            entreprise=request.user.entreprise,
            date__gte=debut_annee
        ).values('statut').annotate(
            nombre=Count('id'),
            montant=Sum('total_ttc')
        )
        
        # Factures par mois
        factures_par_mois = Facture.objects.filter(
            entreprise=request.user.entreprise,
            date__gte=debut_annee
        ).annotate(
            mois=TruncMonth('date')
        ).values('mois').annotate(
            nombre=Count('id'),
            montant=Sum('total_ttc')
        ).order_by('mois')
        
        context = {
            'factures_impayees': factures_impayees,
            'factures_par_statut': factures_par_statut,
            'factures_par_mois': factures_par_mois,
        }
        return render(request, self.template_name, context)

# API pour le POS
class APISearchArticleView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '')
        article_id = request.GET.get('id', '')
        
        articles = Produit.objects.filter(entreprise=request.user.entreprise)
        
        if article_id:
            # Recherche par ID exact
            articles = articles.filter(id=article_id)
        elif query:
            # Recherche par texte (nom ou code)
            articles = articles.filter(
                Q(nom__icontains=query) | Q(code_barre_numero__icontains=query)
            )[:10]
        else:
            articles = articles.none()
        
        results = []
        for article in articles:
            results.append({
                'id': article.id,
                'code': article.code_barre_numero or '',
                'nom': article.nom,
                'prix_vente': float(article.prix_vente),
                'taux_tva': float(article.taux_tva),
                'photo_url': article.photo.url if article.photo else '',
                'stock': article.stock
            })
        
        return JsonResponse(results, safe=False)

class APIClientInfoView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        client_id = request.GET.get('client_id')
        
        client = get_object_or_404(
            Client, 
            pk=client_id,
            entreprise=request.user.entreprise
        )
        
        data = {
            'id': client.id,
            'nom': client.nom,
            'adresse': client.adresse,
            'solde': client.solde,
        }
        
        return JsonResponse(data)
    
# ventes/views.py
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum, Count, Q, F, DecimalField, IntegerField
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json
import csv
from openpyxl import Workbook

class RapportsPOSView(LoginRequiredMixin, PermissionRequiredMixin, View):
    template_name = 'ventes/pos/rapports.html'
    permission_required = 'ventes.view_ventepos'

    def get(self, request, *args, **kwargs):
        point_de_vente = get_object_or_404(
            PointDeVente, 
            pk=kwargs.get('pk'),
            entreprise=request.user.entreprise
        )
        
        # Paramètres de filtre
        date_debut = request.GET.get('date_debut')
        date_fin = request.GET.get('date_fin')
        periode = request.GET.get('periode', 'jour')
        caissier_id = request.GET.get('caissier')
        
        # Dates par défaut (30 derniers jours)
        if not date_debut:
            date_debut = (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        if not date_fin:
            date_fin = timezone.now().strftime('%Y-%m-%d')
        
        # Conversion des dates
        try:
            date_debut_obj = datetime.strptime(date_debut, '%Y-%m-%d').date()
            date_fin_obj = datetime.strptime(date_fin, '%Y-%m-%d').date()
        except:
            date_debut_obj = timezone.now().date() - timedelta(days=30)
            date_fin_obj = timezone.now().date()
        
        # Filtre de base
        filtres = Q(
            session__point_de_vente=point_de_vente,
            date__date__gte=date_debut_obj,
            date__date__lte=date_fin_obj
        )
        
        # Filtre par caissier
        if caissier_id:
            filtres &= Q(session__utilisateur_id=caissier_id)
        
        # Données pour les graphiques
        donnees_ventes = self.get_donnees_ventes(filtres, periode)
        donnees_categories = self.get_donnees_categories(filtres)
        donnees_paiements = self.get_donnees_paiements(filtres)
        donnees_heure = self.get_donnees_heure(filtres)
        
        # Statistiques principales
        stats = self.get_statistiques(filtres)
        
        # Données pour les filtres
        caissiers = User.objects.filter(
            entreprise=request.user.entreprise,
            role='CAISSIER',
            est_actif=True
        )
        
        context = {
            'point_de_vente': point_de_vente,
            'date_debut': date_debut_obj.strftime('%Y-%m-%d'),
            'date_fin': date_fin_obj.strftime('%Y-%m-%d'),
            'periode': periode,
            'caissier_id': caissier_id,
            'caissiers': caissiers,
            'donnees_ventes': donnees_ventes,
            'donnees_categories': donnees_categories,
            'donnees_paiements': donnees_paiements,
            'donnees_heure': donnees_heure,
            'stats': stats,
        }
        
        return render(request, self.template_name, context)
    
    def get_donnees_ventes(self, filtres, periode):
        """Données pour le graphique des ventes"""
        # Calcul manuel pour éviter les problèmes d'agrégation
        ventes = VentePOS.objects.filter(filtres).prefetch_related('items')
        
        donnees = {}
        for vente in ventes:
            if periode == 'jour':
                cle = vente.date.date()
            elif periode == 'mois':
                cle = vente.date.date().replace(day=1)
            else:  # heure
                cle = vente.date.replace(minute=0, second=0, microsecond=0)
            
            if cle not in donnees:
                donnees[cle] = {'total_ttc': Decimal('0'), 'nombre_ventes': 0}
            
            # Calcul manuel du total TTC
            total_ht = sum(item.montant_ht for item in vente.items.all())
            total_tva = sum(item.montant_tva for item in vente.items.all())
            total_ttc = total_ht + total_tva - (vente.remise or Decimal('0'))
            
            donnees[cle]['total_ttc'] += total_ttc
            donnees[cle]['nombre_ventes'] += 1
        
        # Conversion en format attendu par le template
        result = []
        for cle, valeurs in sorted(donnees.items()):
            result.append({
                'periode': cle, 
                'total_ttc': float(valeurs['total_ttc']),
                'nombre_ventes': valeurs['nombre_ventes']
            })
        return result
    
    def get_donnees_categories(self, filtres):
        """Données pour le graphique des catégories - CORRIGÉ"""
        return (
            LigneVentePOS.objects.filter(vente__in=VentePOS.objects.filter(filtres))
            .values('produit__categorie__nom')
            .annotate(
                total=Coalesce(
                    Sum(F('quantite') * F('prix_unitaire')),
                    Decimal('0.00'),
                    output_field=DecimalField(max_digits=12, decimal_places=2)
                ),
                quantite=Coalesce(Sum('quantite'), 0, output_field=IntegerField())
            )
            .order_by('-total')
        )
    
    def get_donnees_paiements(self, filtres):
        """Données pour le graphique des modes de paiement - CORRIGÉ"""
        return (
            PaiementPOS.objects.filter(vente__in=VentePOS.objects.filter(filtres))
            .values('mode_paiement')
            .annotate(
                total=Coalesce(
                    Sum('montant'),
                    Decimal('0.00'),
                    output_field=DecimalField(max_digits=12, decimal_places=2)
                ),
                count=Count('id')
            )
            .order_by('-total')
        )
    
    def get_donnees_heure(self, filtres):
        """Données pour le graphique par heure"""
        # Agrégation manuelle par heure
        ventes = VentePOS.objects.filter(filtres).prefetch_related('items')
        
        donnees_heure = {}
        for vente in ventes:
            heure = vente.date.replace(minute=0, second=0, microsecond=0)
            
            if heure not in donnees_heure:
                donnees_heure[heure] = {'total_ttc': Decimal('0'), 'nombre_ventes': 0}
            
            # Calcul manuel du total TTC
            total_ht = sum(item.montant_ht for item in vente.items.all())
            total_tva = sum(item.montant_tva for item in vente.items.all())
            total_ttc = total_ht + total_tva - (vente.remise or Decimal('0'))
            
            donnees_heure[heure]['total_ttc'] += total_ttc
            donnees_heure[heure]['nombre_ventes'] += 1
        
        # Conversion en format attendu par le template
        result = []
        for cle, valeurs in sorted(donnees_heure.items()):
            result.append({
                'heure': cle, 
                'total_ttc': float(valeurs['total_ttc']),
                'nombre_ventes': valeurs['nombre_ventes']
            })
        return result
    
    def get_statistiques(self, filtres):
        """Calcul des statistiques principales"""
        ventes = VentePOS.objects.filter(filtres).prefetch_related('items')
        lignes = LigneVentePOS.objects.filter(vente__in=ventes)
        paiements = PaiementPOS.objects.filter(vente__in=ventes)
        
        # Calcul manuel du total TTC pour toutes les ventes
        total_ttc = Decimal('0')
        total_ventes = Decimal('0')
        nombre_ventes = ventes.count()
        
        for vente in ventes:
            total_ht = sum(item.montant_ht for item in vente.items.all())
            total_tva = sum(item.montant_tva for item in vente.items.all())
            total_vente = total_ht + total_tva - (vente.remise or Decimal('0'))
            total_ttc += total_vente
        
        # Meilleur produit
        meilleur_produit = (
            lignes.values('produit__nom')
            .annotate(total=Coalesce(
                Sum(F('quantite') * F('prix_unitaire')),
                Decimal('0.00'),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            ))
            .order_by('-total').first()
        )
        
        return {
            'total_ventes': float(total_ttc),
            'nombre_ventes': nombre_ventes,
            'moyenne_vente': float(total_ttc / Decimal(nombre_ventes)) if nombre_ventes > 0 else 0,
            'total_articles': lignes.aggregate(total=Coalesce(Sum('quantite'), 0, output_field=IntegerField()))['total'],
            'meilleur_produit': meilleur_produit,
            'total_paiements': paiements.aggregate(total=Coalesce(Sum('montant'), Decimal('0.00')))['total'],
        }


class ExportRapportPOSView(LoginRequiredMixin, View):
    """Export des rapports en CSV ou Excel"""
    
    def get(self, request, *args, **kwargs):
        point_de_vente = get_object_or_404(
            PointDeVente, 
            pk=kwargs.get('pk'),
            entreprise=request.user.entreprise
        )
        
        format_export = request.GET.get('format', 'csv')
        type_rapport = request.GET.get('type', 'ventes')
        
        # Paramètres de filtre
        date_debut = request.GET.get('date_debut')
        date_fin = request.GET.get('date_fin')
        caissier_id = request.GET.get('caissier')
        
        # Filtre de base
        filtres = Q(session__point_de_vente=point_de_vente)
        if date_debut:
            filtres &= Q(date__date__gte=date_debut)
        if date_fin:
            filtres &= Q(date__date__lte=date_fin)
        if caissier_id:
            filtres &= Q(session__utilisateur_id=caissier_id)
        
        if type_rapport == 'ventes':
            return self.export_ventes(filtres, format_export, point_de_vente)
        elif type_rapport == 'produits':
            return self.export_produits(filtres, format_export, point_de_vente)
        elif type_rapport == 'paiements':
            return self.export_paiements(filtres, format_export, point_de_vente)
        elif type_rapport == 'caissiers':
            return self.export_caissiers(filtres, format_export, point_de_vente)
    
    def export_ventes(self, filtres, format_export, point_de_vente):
        ventes = VentePOS.objects.filter(filtres).select_related('client', 'session').prefetch_related('items', 'paiementpos_set')
        
        if format_export == 'excel':
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="rapport_ventes_{point_de_vente.nom}_{timezone.now().date()}.xlsx"'
            
            wb = Workbook()
            ws = wb.active
            ws.title = "Ventes"
            
            # En-têtes
            headers = ['Date', 'N° Vente', 'Client', 'Total HT', 'TVA', 'Remise', 'Total TTC', 'Mode Paiement', 'Caissier']
            ws.append(headers)
            
            for vente in ventes:
                # Calcul manuel des totaux
                total_ht = sum(item.montant_ht for item in vente.items.all())
                total_tva = sum(item.montant_tva for item in vente.items.all())
                total_ttc = total_ht + total_tva - (vente.remise or Decimal('0'))
                
                mode_paiement = ", ".join([p.get_mode_paiement_display() for p in vente.paiementpos_set.all()])
                caissier = f"{vente.session.utilisateur.first_name} {vente.session.utilisateur.last_name}"
                
                ws.append([
                    vente.date.strftime('%d/%m/%Y %H:%M'),
                    vente.numero,
                    vente.client.nom if vente.client else 'Non renseigné',
                    float(total_ht),
                    float(total_tva),
                    float(vente.remise or Decimal('0')),
                    float(total_ttc),
                    mode_paiement,
                    caissier
                ])
            
            wb.save(response)
            return response
        
        else:  # CSV
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="rapport_ventes_{point_de_vente.nom}_{timezone.now().date()}.csv"'
            
            writer = csv.writer(response)
            headers = ['Date', 'N° Vente', 'Client', 'Total HT', 'TVA', 'Remise', 'Total TTC', 'Mode Paiement', 'Caissier']
            writer.writerow(headers)
            
            for vente in ventes:
                total_ht = sum(item.montant_ht for item in vente.items.all())
                total_tva = sum(item.montant_tva for item in vente.items.all())
                total_ttc = total_ht + total_tva - (vente.remise or Decimal('0'))
                
                mode_paiement = ", ".join([p.get_mode_paiement_display() for p in vente.paiementpos_set.all()])
                caissier = f"{vente.session.utilisateur.first_name} {vente.session.utilisateur.last_name}"
                
                writer.writerow([
                    vente.date.strftime('%d/%m/%Y %H:%M'),
                    vente.numero,
                    vente.client.nom if vente.client else 'Non renseigné',
                    float(total_ht),
                    float(total_tva),
                    float(vente.remise or Decimal('0')),
                    float(total_ttc),
                    mode_paiement,
                    caissier
                ])
            
            return response
    
    def export_produits(self, filtres, format_export, point_de_vente):
        produits = (
            LigneVentePOS.objects.filter(vente__in=VentePOS.objects.filter(filtres))
            .values('produit__nom', 'produit__libelle')
            .annotate(
                quantite=Coalesce(Sum('quantite'), 0),
                total=Coalesce(Sum(F('quantite') * F('prix_unitaire')), Decimal('0.00'))
            )
            .order_by('-total')
        )
        
        if format_export == 'excel':
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="rapport_produits_{point_de_vente.nom}_{timezone.now().date()}.xlsx"'
            
            wb = Workbook()
            ws = wb.active
            ws.title = "Produits"
            
            ws.append(['Produit', 'Libellé', 'Quantité Vendue', 'Chiffre d\'Affaires'])
            
            for produit in produits:
                ws.append([
                    produit['produit__nom'],
                    produit['produit__libelle'],
                    produit['quantite'],
                    float(produit['total'])
                ])
            
            wb.save(response)
            return response
        
        else:  # CSV
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="rapport_produits_{point_de_vente.nom}_{timezone.now().date()}.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['Produit', 'Libellé', 'Quantité Vendue', 'Chiffre d\'Affaires'])
            
            for produit in produits:
                writer.writerow([
                    produit['produit__nom'],
                    produit['produit__libelle'],
                    produit['quantite'],
                    float(produit['total'])
                ])
            
            return response
    
    # Méthodes export_produits et export_paiements similaires...
    
  # ventes/views.py

from django.views.generic import ListView, DetailView
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth import get_user_model
from datetime import timedelta
from decimal import Decimal



# --- Vue de l'historique des ventes ---
class HistoriquePOSView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'ventes/pos/historique.html'
    permission_required = 'ventes.view_ventepos'
    context_object_name = 'ventes'
    paginate_by = 20

    def get_queryset(self):
        point_de_vente = get_object_or_404(
            PointDeVente, 
            pk=self.kwargs.get('pk'),
            entreprise=self.request.user.entreprise
        )
        
        # Filtrer les ventes du point de vente
        queryset = VentePOS.objects.filter(
            session__point_de_vente=point_de_vente
        ).select_related(
            'session', 'client', 'session__utilisateur'
        ).prefetch_related(
            'items', 'paiementpos_set'
        ).order_by('-date')
        
        # Filtres
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        client_id = self.request.GET.get('client')
        utilisateur_id = self.request.GET.get('utilisateur')
        
        # Filtre par date
        if date_debut:
            queryset = queryset.filter(date__date__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date__date__lte=date_fin)
        
        # Filtre par client
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        
        # Filtre par utilisateur (caissier)
        if utilisateur_id:
            queryset = queryset.filter(session__utilisateur_id=utilisateur_id)
        
        # Recherche par numéro de vente
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(numero__icontains=search_query)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        point_de_vente = get_object_or_404(
            PointDeVente, 
            pk=self.kwargs.get('pk'),
            entreprise=self.request.user.entreprise
        )
        
        # --- Récupération de la devise principale ---
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            devise_symbole = "€"
        # ---------------------------------------------
        
        # Dates par défaut (7 derniers jours)
        date_debut_default = (timezone.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        date_fin_default = timezone.now().strftime('%Y-%m-%d')
        
        context.update({
            'point_de_vente': point_de_vente,
            'date_debut': self.request.GET.get('date_debut', date_debut_default),
            'date_fin': self.request.GET.get('date_fin', date_fin_default),
            'clients': Client.objects.filter(entreprise=self.request.user.entreprise),
            'utilisateurs': self.get_utilisateurs_point_de_vente(point_de_vente),
            'stats': self.get_statistiques(),
            'devise_symbole': devise_symbole, # Ajout de la devise au contexte
        })
        
        return context
    
    def get_utilisateurs_point_de_vente(self, point_de_vente):
        """Récupère les utilisateurs qui ont travaillé sur ce point de vente"""
        user_ids = SessionPOS.objects.filter(
            point_de_vente=point_de_vente
        ).values_list('utilisateur', flat=True).distinct()
        
        return get_user_model().objects.filter(id__in=user_ids)
    
    def get_statistiques(self):
        """Calcule les statistiques pour les ventes filtrées"""
        queryset = self.get_queryset()
        
        # Calcul manuel des totaux
        total_ttc = Decimal('0')
        total_ventes = queryset.count()
        total_articles = 0
        
        for vente in queryset:
            total_ht = sum(item.montant_ht for item in vente.items.all())
            total_tva = sum(item.montant_tva for item in vente.items.all())
            total_ttc += total_ht + total_tva - vente.remise
            total_articles += sum(item.quantite for item in vente.items.all())
        
        return {
            'total_ttc': total_ttc,
            'total_ventes': total_ventes,
            'total_articles': total_articles,
            'moyenne_vente': total_ttc / total_ventes if total_ventes > 0 else 0,
        }
from .forms import EcartCaisseForm
# --- Vue du détail d'une vente ---
class DetailVentePOSView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    template_name = 'ventes/pos/detail_vente.html'
    permission_required = 'ventes.view_ventepos'
    context_object_name = 'vente'
    
    def get_queryset(self):
        return VentePOS.objects.filter(
            session__point_de_vente__entreprise=self.request.user.entreprise
        ).select_related(
            'session', 'client', 'session__utilisateur', 'session__point_de_vente'
        ).prefetch_related(
            'items', 'items__produit', 'paiementpos_set'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        vente = self.object
        
        # --- Récupération de la devise principale ---
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            devise_symbole = "€"
        # ---------------------------------------------
        
        # Calcul des totaux
        total_ht = sum(item.montant_ht for item in vente.items.all())
        total_tva = sum(item.montant_tva for item in vente.items.all())
        total_ttc = total_ht + total_tva - vente.remise
        
        # Calcul du total payé
        total_paye = sum(p.montant for p in vente.paiementpos_set.all())
        
        context.update({
            'total_ht': total_ht,
            'total_tva': total_tva,
            'total_ttc': total_ttc,
            'total_paye': total_paye,
            'devise_symbole': devise_symbole, # Ajout de la devise au contexte
        })
        
        return context
    
    
  # ventes/views.py

from django.views.generic import ListView, CreateView, View
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Sum
from django.contrib.auth import get_user_model
from django.contrib import messages
from datetime import timedelta
from django.utils import timezone
from .forms import EcartCaisseForm
from django.core.paginator import Paginator


from parametres.models import ConfigurationSAAS # <-- Ajouté

# --- Vue de la liste des écarts de caisse ---
class EcartsCaisseView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    template_name = 'ventes/pos/ecarts_caisse.html'
    permission_required = 'ventes.view_ecartcaisse'
    context_object_name = 'ecarts'
    paginate_by = 20

    def get_queryset(self):
        point_de_vente = get_object_or_404(
            PointDeVente, 
            pk=self.kwargs.get('pk'),
            entreprise=self.request.user.entreprise
        )
        
        queryset = EcartCaisse.objects.filter(
            session__point_de_vente=point_de_vente
        ).select_related(
            'caissier', 'session', 'created_by'
        ).order_by('-date_creation')
        
        # Filtres
        caissier_id = self.request.GET.get('caissier')
        type_ecart = self.request.GET.get('type_ecart')
        date_debut = self.request.GET.get('date_debut')
        date_fin = self.request.GET.get('date_fin')
        
        if caissier_id:
            queryset = queryset.filter(caissier_id=caissier_id)
        
        if type_ecart:
            queryset = queryset.filter(type_ecart=type_ecart)
        
        if date_debut:
            queryset = queryset.filter(date_creation__date__gte=date_debut)
        
        if date_fin:
            queryset = queryset.filter(date_creation__date__lte=date_fin)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        point_de_vente = get_object_or_404(
            PointDeVente, 
            pk=self.kwargs.get('pk'),
            entreprise=self.request.user.entreprise
        )
        
        # Statistiques
        ecarts = self.get_queryset()
        total_excedent = ecarts.filter(type_ecart='excedent').aggregate(Sum('montant'))['montant__sum'] or 0
        total_manquant = ecarts.filter(type_ecart='manquant').aggregate(Sum('montant'))['montant__sum'] or 0
        solde_ecarts = total_excedent - total_manquant

        # Récupération du symbole de la devise
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            devise_symbole = "€"
        
        context.update({
            'point_de_vente': point_de_vente,
            'caissiers': self.get_caissiers_point_de_vente(point_de_vente),
            'total_excedent': total_excedent,
            'total_manquant': total_manquant,
            'solde_ecarts': solde_ecarts,
            'types_ecart': EcartCaisse.TYPE_ECART_CHOICES,
            'devise_symbole': devise_symbole, # <-- Ajout au contexte
        })
        
        return context
    
    def get_caissiers_point_de_vente(self, point_de_vente):
        """Récupère les caissiers du point de vente"""
        user_ids = SessionPOS.objects.filter(
            point_de_vente=point_de_vente
        ).values_list('utilisateur', flat=True).distinct()
        
        return get_user_model().objects.filter(id__in=user_ids)



# --- Vue de création d'un écart de caisse ---
class CreerEcartCaisseView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    template_name = 'ventes/pos/creer_ecart_caisse.html'
    permission_required = 'ventes.add_ecartcaisse'
    form_class = EcartCaisseForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        point_de_vente = get_object_or_404(
            PointDeVente, 
            pk=self.kwargs.get('pk'),
            entreprise=self.request.user.entreprise
        )
        
        session = get_object_or_404(
            SessionPOS,
            pk=self.kwargs.get('session_pk'),
            point_de_vente=point_de_vente
        )

        # Récupération du symbole de la devise
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            devise_symbole = "€"
        
        context.update({
            'point_de_vente': point_de_vente,
            'session': session,
            'devise_symbole': devise_symbole, # <-- Ajout au contexte
        })
        
        return context
    
    def form_valid(self, form):
        point_de_vente = get_object_or_404(
            PointDeVente, 
            pk=self.kwargs.get('pk'),
            entreprise=self.request.user.entreprise
        )
        
        session = get_object_or_404(
            SessionPOS,
            pk=self.kwargs.get('session_pk'),
            point_de_vente=point_de_vente
        )
        
        ecart = form.save(commit=False)
        ecart.session = session
        ecart.caissier = session.utilisateur
        ecart.created_by = self.request.user
        ecart.save()
        
        messages.success(self.request, "Écart de caisse enregistré avec succès.")
        return redirect('ventes:ecarts_caisse', pk=point_de_vente.id)


# ventes/views.py
class RapportEcartsCaisseView(LoginRequiredMixin, PermissionRequiredMixin, View):
    template_name = 'ventes/pos/rapport_ecarts_caisse.html'
    permission_required = 'ventes.view_ecartcaisse'
    
    def get(self, request, *args, **kwargs):
        point_de_vente = get_object_or_404(
            PointDeVente, 
            pk=kwargs.get('pk'),
            entreprise=request.user.entreprise
        )
        
        # Période par défaut (30 derniers jours)
        date_debut = request.GET.get('date_debut', (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_fin = request.GET.get('date_fin', timezone.now().strftime('%Y-%m-%d'))
        caissier_id = request.GET.get('caissier')
        
        # Écarts de la période avec filtres
        ecarts = EcartCaisse.objects.filter(
            session__point_de_vente=point_de_vente,
            date_creation__date__gte=date_debut,
            date_creation__date__lte=date_fin
        ).select_related('caissier', 'session', 'created_by')
        
        # Filtre par caissier
        if caissier_id:
            ecarts = ecarts.filter(caissier_id=caissier_id)
        
        # Pagination
        paginator = Paginator(ecarts, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # SIMPLIFICATION: Récupérer les caissiers à partir des écarts existants
        caissier_ids = ecarts.values_list('caissier', flat=True).distinct()
        caissiers = get_user_model().objects.filter(id__in=caissier_ids)
        
        # Statistiques par caissier
        stats_caissiers = []
        
        for caissier in caissiers:
            ecarts_caissier = ecarts.filter(caissier=caissier)
            
            total_excedent = ecarts_caissier.filter(type_ecart='excedent').aggregate(
                Sum('montant'))['montant__sum'] or 0
            total_manquant = ecarts_caissier.filter(type_ecart='manquant').aggregate(
                Sum('montant'))['montant__sum'] or 0
            total_regularisation = ecarts_caissier.filter(type_ecart='regularisation').aggregate(
                Sum('montant'))['montant__sum'] or 0
            
            solde = total_excedent - total_manquant
            nombre_ecarts = ecarts_caissier.count()
            
            # Simplification: on ne calcule pas le nombre de sessions pour éviter l'erreur
            nombre_sessions = 1  # Valeur par défaut
            moyenne_session = solde
            
            stats_caissiers.append({
                'caissier': caissier,
                'total_excedent': total_excedent,
                'total_manquant': total_manquant,
                'total_regularisation': total_regularisation,
                'solde': solde,
                'nombre_ecarts': nombre_ecarts,
                'nombre_sessions': nombre_sessions,
                'moyenne_session': moyenne_session,
            })
        
        # Tri par solde
        stats_caissiers.sort(key=lambda x: x['solde'])
        
        # Statistiques globales
        total_excedent_global = ecarts.filter(type_ecart='excedent').aggregate(
            Sum('montant'))['montant__sum'] or 0
        total_manquant_global = ecarts.filter(type_ecart='manquant').aggregate(
            Sum('montant'))['montant__sum'] or 0
        total_regularisation_global = ecarts.filter(type_ecart='regularisation').aggregate(
            Sum('montant'))['montant__sum'] or 0
        
        solde_total = total_excedent_global - total_manquant_global
        total_ecarts = ecarts.count()
        moyenne_generale = solde_total / len(stats_caissiers) if stats_caissiers else 0
        
        # Récupération du symbole de la devise
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=request.user.entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            devise_symbole = "€"
        
        context = {
            'point_de_vente': point_de_vente,
            'date_debut': date_debut,
            'date_fin': date_fin,
            'ecarts': page_obj,
            'page_obj': page_obj,
            'is_paginated': page_obj.has_other_pages(),
            'caissiers': caissiers,
            'stats_caissiers': stats_caissiers,
            'total_excedent': total_excedent_global,
            'total_manquant': total_manquant_global,
            'total_regularisation': total_regularisation_global,
            'solde_total': solde_total,
            'total_ecarts': total_ecarts,
            'moyenne_generale': moyenne_generale,
            'devise_symbole': devise_symbole,
        }
        
        return render(request, self.template_name, context)