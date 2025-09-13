from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView,View
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db import connection
from django.core.exceptions import PermissionDenied
import pandas as pd
import json
from datetime import datetime, timedelta

from .models import KPI, KPIValue, Report, DataExport, DataImport, AIIntegration
from .forms import KPIForm, ReportForm, ExportForm, ImportForm, AIForm
from parametres.mixins import EntrepriseAccessMixin
from parametres.models import ConfigurationSAAS

from ventes.models import Facture, Devis, Commande
from achats.models import FactureFournisseur, CommandeAchat, BonReception
from STOCK.models import Produit, MouvementStock
from comptabilite.models import EcritureComptable, JournalComptable
from grh.models import Employe
from crm.models import *



class AccueilView(LoginRequiredMixin, EntrepriseAccessMixin, TemplateView):
    """Page d'accueil du module BI"""
    template_name = "bi/accueil.html"
    permission_required = "bi.view_kpi_dashboard"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.user.entreprise
        
        # Statistiques pour la page d'accueil
        context['kpis_actifs'] = KPI.objects.filter(entreprise=entreprise, actif=True).count()
        context['rapports_count'] = Report.objects.filter(entreprise=entreprise).count()
        context['exports_mois'] = DataExport.objects.filter(
            entreprise=entreprise,
            created_at__month=timezone.now().month
        ).count()
        context['ia_actifs'] = AIIntegration.objects.filter(entreprise=entreprise, actif=True).count()
        
        # KPIs récents
        context['kpis_recents'] = KPI.objects.filter(entreprise=entreprise).order_by('-created_at')[:5]
        
        # Informations système
        context['derniere_maj'] = timezone.now()
        context['donnees_disponibles'] = "12 mois"
        context['ia_connecte'] = True  # À remplacer par une vérification réelle
        
        return context
from .models import KPI, KPIValue, Report, DataExport, DataImport, AIIntegration
from .forms import KPIForm, ReportForm, ExportForm, ImportForm, AIForm
from parametres.models import ConfigurationSAAS

# Import des modèles de vos autres applications
try:
    from ventes.models import Devis, Facture, LigneDevis, LigneFacture
    from achats.models import BonReception, FactureFournisseur, LigneBonReception
    from STOCK.models import  *
    from comptabilite.models import EcritureComptable, JournalComptable
    from grh.models import Employe, Departement, Contrat
    from crm.models import Client, Opportunite, Ticket
except ImportError as e:
    print(f"Warning: Some modules not available - {e}")

def calculer_productivite_rh(self, entreprise):
    """Calcule la productivité RH (CA / nombre d'employés)"""
    try:
        from grh.models import Employe
        from ventes.models import Facture
        
        nb_employes = Employe.objects.filter(entreprise=entreprise, actif=True).count()
        ca_annuel = Facture.objects.filter(
            entreprise=entreprise,
            date_creation__year=timezone.now().year,
            statut='payee'
        ).aggregate(total=Sum('montant_total'))['total'] or 0
        
        if nb_employes > 0:
            return round(float(ca_annuel) / nb_employes, 2)
        return 0
    except:
        return 0

def calculer_taux_conversion_crm(self, entreprise):
    """Calcule le taux de conversion CRM"""
    try:
        from crm.models import Opportunite
        
        opportunites = Opportunite.objects.filter(entreprise=entreprise)
        total = opportunites.count()
        gagnees = opportunites.filter(statut='gagnee').count()
        
        if total > 0:
            return round((gagnees / total) * 100, 2)
        return 0
    except:
        return 0

def calculer_cout_acquisition_client(self, entreprise):
    """Calcule le coût d'acquisition client"""
    try:
        from crm.models import Client
        # from marketing.models import Campagne  # Si vous avez un module marketing
        
        couts_marketing = 0  # À remplacer par les coûts réels
        nouveaux_clients = Client.objects.filter(
            entreprise=entreprise,
            date_creation__year=timezone.now().year
        ).count()
        
        if nouveaux_clients > 0:
            return round(couts_marketing / nouveaux_clients, 2)
        return 0
    except:
        return 0
logger = logging.getLogger(__name__)

class DashboardView(LoginRequiredMixin, EntrepriseAccessMixin, TemplateView):
    """Vue du tableau de bord BI avec intégration réelle"""
    template_name = "bi/dashboard.html"
    permission_required = "bi.view_kpi_dashboard"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.user.entreprise
        
        # Récupérer la devise principale
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            devise_symbole = "€"
        
        context['devise_symbole'] = devise_symbole
        
        # Récupérer les KPIs principaux
        kpis = KPI.objects.filter(entreprise=entreprise, actif=True)[:12]
        
        # Calculer les valeurs des KPIs avec intégration réelle
        kpi_values = {}
        kpi_details = {}
        
        for kpi in kpis:
            try:
                valeur, details = self.calculer_kpi(kpi, entreprise)
                kpi_values[kpi.id] = valeur
                kpi_details[kpi.id] = details
            except Exception as e:
                kpi_values[kpi.id] = None
                kpi_details[kpi.id] = f"Erreur: {str(e)}"
        
        context['kpis'] = kpis
        context['kpi_values'] = kpi_values
        context['kpi_details'] = kpi_details
        context['rapports'] = Report.objects.filter(entreprise=entreprise, public=True)[:5]
        
        # Données pour les graphiques
        context['ventes_data'] = self.get_ventes_chart_data(entreprise)
        context['stocks_data'] = self.get_stocks_chart_data(entreprise)
        context['finances_data'] = self.get_finances_chart_data(entreprise)
        
        # Diagnostic des données
        context['diagnostic'] = self.get_diagnostic_data(entreprise)
        
        return context
    
    def get_diagnostic_data(self, entreprise):
        """Retourne des informations de diagnostic sur les données disponibles"""
        diagnostic = {}
        
        try:
            # Vérifier les ventes
            Facture = self.get_model_by_app_label('Facture', 'ventes')
            if Facture:
                diagnostic['ventes_count'] = Facture.objects.filter(entreprise=entreprise).count()
                diagnostic['ventes_mois'] = Facture.objects.filter(
                    entreprise=entreprise,
                    date_creation__month=timezone.now().month,
                    date_creation__year=timezone.now().year
                ).count()
            else:
                diagnostic['ventes_count'] = 0
                diagnostic['ventes_mois'] = 0
            
            # Vérifier les achats
            FactureFournisseur = self.get_model_by_app_label('FactureFournisseur', 'achats')
            if FactureFournisseur:
                diagnostic['achats_count'] = FactureFournisseur.objects.filter(entreprise=entreprise).count()
            else:
                diagnostic['achats_count'] = 0
            
            # Vérifier les stocks
            Produit = self.get_model_by_app_label('Produit', 'STOCK')
            if Produit:
                diagnostic['produits_count'] = Produit.objects.filter(entreprise=entreprise).count()
            else:
                diagnostic['produits_count'] = 0
            
            # Vérifier les commandes
            CommandeAchat = self.get_model_by_app_label('CommandeAchat', 'achats')
            if CommandeAchat:
                diagnostic['commandes_count'] = CommandeAchat.objects.filter(entreprise=entreprise).count()
            else:
                diagnostic['commandes_count'] = 0
                
        except Exception as e:
            diagnostic['erreur'] = str(e)
            diagnostic['ventes_count'] = 0
            diagnostic['ventes_mois'] = 0
            diagnostic['achats_count'] = 0
            diagnostic['produits_count'] = 0
            diagnostic['commandes_count'] = 0
        
        return diagnostic
    
    def get_model_by_app_label(self, model_name, app_label):
        """Retourne un modèle par son app_label et son nom - Version robuste"""
        from django.apps import apps
        
        try:
            # Essayer plusieurs variations de noms d'applications
            app_variations = [
                app_label.lower(),
                app_label.upper(),
                app_label.capitalize(),
            ]
            
            for app_variation in app_variations:
                try:
                    model = apps.get_model(app_variation, model_name)
                    if model:
                        print(f"Modèle trouvé: {app_variation}.{model_name}")
                        return model
                except LookupError:
                    continue
            
            # Si aucune variation ne fonctionne, essayer sans app_label précis
            try:
                # Chercher le modèle dans toutes les applications
                for app_config in apps.get_app_configs():
                    try:
                        model = apps.get_model(app_config.label, model_name)
                        if model:
                            print(f"Modèle trouvé globalement: {app_config.label}.{model_name}")
                            return model
                    except LookupError:
                        continue
            except:
                pass
                
            print(f"Modèle NON TROUVÉ: {app_label}.{model_name}")
            return None
            
        except Exception as e:
            print(f"Erreur recherche modèle {app_label}.{model_name}: {e}")
            return None
    
    def calculer_kpi(self, kpi, entreprise):
        """Calcule la valeur réelle d'un KPI en intégrant avec les modules existants"""
        try:
            if kpi.code == 'ca_mensuel':
                valeur = self.calculer_chiffre_affaires_mensuel(entreprise)
                return valeur, f"Chiffre d'affaires du mois en cours ({valeur:,.0f} {self.get_devise_symbole(entreprise)})"
            
            elif kpi.code == 'marge_brute':
                valeur = self.calculer_marge_brute(entreprise)
                return valeur, f"Marge brute en pourcentage ({valeur}%)"
            
            elif kpi.code == 'rotation_stocks':
                valeur = self.calculer_rotation_stocks(entreprise)
                return valeur, f"Rotation des stocks ({valeur} fois)"
            
            elif kpi.code == 'dmp_clients':
                valeur = self.calculer_dmp_clients(entreprise)
                return valeur, f"Délai moyen de paiement clients ({valeur} jours)"
            
            else:
                # KPI personnalisé - tentative d'évaluation basique
                valeur = self.evaluer_formule_personnalisee(kpi.formule, entreprise)
                return valeur, "KPI personnalisé"
                
        except Exception as e:
            logger.error(f"Erreur calcul KPI {kpi.code}: {e}")
            return None, f"Erreur de calcul: {str(e)}"
    
    def get_devise_symbole(self, entreprise):
        """Retourne le symbole de la devise principale"""
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            return config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            return "€"
    
    def calculer_chiffre_d_affaires_mensuel(self, entreprise):
        """Calcule le chiffre d'affaires du mois en cours - Inclut les ventes POS"""
        try:
            Facture = self.get_model_by_app_label('Facture', 'ventes')
            VentePOS = self.get_model_by_app_label('VentePOS', 'ventes')
            
            if not Facture and not VentePOS:
                return 0
            
            debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            total_ca = Decimal('0.00')
            
            # CA des factures classiques
            if Facture:
                ca_factures = Facture.objects.filter(
                    entreprise=entreprise,
                    date_facture__gte=debut_mois,
                    statut__in=['payee', 'payé', 'paid', 'paye_partiel', 'paye_complet']
                ).aggregate(total=Sum('total_ttc'))['total'] or Decimal('0.00')
                total_ca += Decimal(str(ca_factures))
                print(f"💰 CA factures: {ca_factures}")
            
            # CA des ventes POS
            if VentePOS:
                # Essayer différents champs de date pour les ventes POS
                date_fields = ['date', 'created_at', 'date_creation']
                for date_field in date_fields:
                    if hasattr(VentePOS(), date_field):
                        ca_pos = VentePOS.objects.filter(
                            entreprise=entreprise,
                            **{f'{date_field}__gte': debut_mois}
                        ).aggregate(total=Sum('total_ttc'))['total'] or Decimal('0.00')
                        
                        # Si pas de champ total_ttc, calculer manuellement
                        if ca_pos is None:
                            ca_pos = self.calculer_ca_ventes_pos(entreprise, debut_mois)
                        
                        total_ca += Decimal(str(ca_pos))
                        print(f"💰 CA POS: {ca_pos}")
                        break
            
            print(f"💰 CA mensuel total: {total_ca}")
            return float(total_ca)
            
        except Exception as e:
            print(f"❌ Erreur calcul CA: {e}")
            return 0

    def calculer_ca_ventes_pos(self, entreprise, debut_mois):
        """Calcule manuellement le CA des ventes POS si le champ total_ttc n'existe pas"""
        try:
            VentePOS = self.get_model_by_app_label('VentePOS', 'ventes')
            LigneVentePOS = self.get_model_by_app_label('LigneVentePOS', 'ventes')
            
            if not VentePOS or not LigneVentePOS:
                return Decimal('0.00')
            
            # Récupérer toutes les ventes POS du mois
            ventes_pos = VentePOS.objects.filter(
                entreprise=entreprise,
                date__gte=debut_mois
            )
            
            total_ca = Decimal('0.00')
            
            for vente in ventes_pos:
                # Calculer le total TTC de chaque vente
                lignes_vente = LigneVentePOS.objects.filter(vente=vente)
                for ligne in lignes_vente:
                    montant_ligne = Decimal(str(ligne.quantite)) * Decimal(str(ligne.prix_unitaire))
                    montant_tva = montant_ligne * (Decimal(str(ligne.taux_tva or 0)) / Decimal('100'))
                    total_ligne = montant_ligne + montant_tva
                    total_ca += total_ligne
            
            return total_ca
            
        except Exception as e:
            print(f"❌ Erreur calcul CA POS manuel: {e}")
            return Decimal('0.00')

    def get_diagnostic_data(self, entreprise):
        """Retourne des informations de diagnostic sur les données disponibles - Version finale"""
        diagnostic = {}
        
        try:
            print(f"\n=== DIAGNOSTIC POUR ENTREPRISE: {entreprise.nom} ===")
            
            # Vérifier les ventes (factures + POS)
            Facture = self.get_model_by_app_label('Facture', 'ventes')
            VentePOS = self.get_model_by_app_label('VentePOS', 'ventes')
            
            total_ventes = 0
            ventes_mois = 0
            
            if Facture:
                try:
                    total_ventes += Facture.objects.filter(entreprise=entreprise).count()
                    ventes_mois += Facture.objects.filter(
                        entreprise=entreprise,
                        date_facture__month=timezone.now().month,
                        date_facture__year=timezone.now().year
                    ).count()
                    print(f"✅ Factures: {Facture.objects.filter(entreprise=entreprise).count()} total, {ventes_mois} ce mois")
                except Exception as e:
                    print(f"❌ Erreur factures: {e}")
            
            if VentePOS:
                try:
                    total_ventes += VentePOS.objects.filter(entreprise=entreprise).count()
                    # Essayer différents champs de date pour les ventes POS
                    date_fields = ['date', 'created_at', 'date_creation']
                    for date_field in date_fields:
                        if hasattr(VentePOS(), date_field):
                            ventes_mois += VentePOS.objects.filter(
                                entreprise=entreprise,
                                **{f'{date_field}__month': timezone.now().month},
                                **{f'{date_field}__year': timezone.now().year}
                            ).count()
                            break
                    print(f"✅ Ventes POS: {VentePOS.objects.filter(entreprise=entreprise).count()} total")
                except Exception as e:
                    print(f"❌ Erreur ventes POS: {e}")
            
            diagnostic['ventes_count'] = total_ventes
            diagnostic['ventes_mois'] = ventes_mois
            print(f"✅ Ventes totales: {total_ventes} total, {ventes_mois} ce mois")
            
            # Vérifier les achats
            FactureFournisseur = self.get_model_by_app_label('FactureFournisseur', 'achats')
            if FactureFournisseur:
                try:
                    diagnostic['achats_count'] = FactureFournisseur.objects.filter(entreprise=entreprise).count()
                    print(f"✅ Achats: {diagnostic['achats_count']} factures")
                except Exception as e:
                    diagnostic['achats_count'] = 0
                    print(f"❌ Erreur achats: {e}")
            else:
                diagnostic['achats_count'] = 0
                print("❌ Modèle FactureFournisseur non trouvé")
            
            # Vérifier les stocks
            Produit = self.get_model_by_app_label('Produit', 'STOCK')
            if Produit:
                try:
                    diagnostic['produits_count'] = Produit.objects.filter(entreprise=entreprise).count()
                    print(f"✅ Stocks: {diagnostic['produits_count']} produits")
                except Exception as e:
                    diagnostic['produits_count'] = 0
                    print(f"❌ Erreur stocks: {e}")
            else:
                diagnostic['produits_count'] = 0
                print("❌ Modèle Produit non trouvé")
            
            # Vérifier les commandes
            CommandeAchat = self.get_model_by_app_label('CommandeAchat', 'achats')
            if CommandeAchat:
                try:
                    diagnostic['commandes_count'] = CommandeAchat.objects.filter(entreprise=entreprise).count()
                    print(f"✅ Commandes: {diagnostic['commandes_count']} commandes")
                except Exception as e:
                    diagnostic['commandes_count'] = 0
                    print(f"❌ Erreur commandes: {e}")
            else:
                diagnostic['commandes_count'] = 0
                print("❌ Modèle CommandeAchat non trouvé")
                
        except Exception as e:
            diagnostic['erreur'] = str(e)
            diagnostic['ventes_count'] = 0
            diagnostic['ventes_mois'] = 0
            diagnostic['achats_count'] = 0
            diagnostic['produits_count'] = 0
            diagnostic['commandes_count'] = 0
            print(f"❌ Erreur générale diagnostic: {e}")
        
        return diagnostic

    def get_ventes_chart_data(self, entreprise):
        """Données pour le graphique des ventes - Inclut les ventes POS"""
        try:
            Facture = self.get_model_by_app_label('Facture', 'ventes')
            VentePOS = self.get_model_by_app_label('VentePOS', 'ventes')
            
            if not Facture and not VentePOS:
                return self.get_mock_ventes_data()
                
            from django.db.models.functions import TruncMonth
            
            # Ventes des 6 derniers mois (factures + POS)
            six_mois = timezone.now() - timedelta(days=180)
            data_ventes = {}
            
            # Factures classiques
            if Facture:
                ventes_factures = Facture.objects.filter(
                    entreprise=entreprise,
                    date_facture__gte=six_mois,
                    statut__in=['payee', 'payé', 'paid', 'paye_partiel', 'paye_complet']
                ).annotate(mois=TruncMonth('date_facture')).values('mois').annotate(
                    total=Sum('total_ttc')
                ).order_by('mois')
                
                for vente in ventes_factures:
                    mois = vente['mois'].strftime('%b %Y')
                    montant = float(vente['total'] or 0)
                    data_ventes[mois] = data_ventes.get(mois, 0) + montant
            
            # Ventes POS
            if VentePOS:
                # Essayer différents champs de date
                date_fields = ['date', 'created_at', 'date_creation']
                for date_field in date_fields:
                    if hasattr(VentePOS(), date_field):
                        ventes_pos = VentePOS.objects.filter(
                            entreprise=entreprise,
                            **{f'{date_field}__gte': six_mois}
                        ).annotate(mois=TruncMonth(date_field)).values('mois')
                        
                        # Calculer manuellement le total pour chaque mois
                        for vente_mois in ventes_pos:
                            mois = vente_mois['mois'].strftime('%b %Y')
                            ventes_du_mois = VentePOS.objects.filter(
                                entreprise=entreprise,
                                **{f'{date_field}__month': vente_mois['mois'].month},
                                **{f'{date_field}__year': vente_mois['mois'].year}
                            )
                            
                            total_mois = Decimal('0.00')
                            for vente in ventes_du_mois:
                                total_mois += self.calculer_total_vente_pos(vente)
                            
                            data_ventes[mois] = data_ventes.get(mois, 0) + float(total_mois)
                        
                        break
            
            if data_ventes:
                print(f"📈 Données ventes réelles trouvées: {len(data_ventes)} mois")
                labels = sorted(data_ventes.keys())
                data = [data_ventes[mois] for mois in labels]
                return {'labels': labels, 'data': data}
            
            print("ℹ️ Aucune donnée de vente, utilisation des données mockées")
            return self.get_mock_ventes_data()
            
        except Exception as e:
            print(f"❌ Erreur données ventes: {e}")
            return self.get_mock_ventes_data()

    def calculer_total_vente_pos(self, vente_pos):
        """Calcule le total TTC d'une vente POS"""
        try:
            LigneVentePOS = self.get_model_by_app_label('LigneVentePOS', 'ventes')
            if not LigneVentePOS:
                return Decimal('0.00')
            
            total = Decimal('0.00')
            lignes = LigneVentePOS.objects.filter(vente=vente_pos)
            
            for ligne in lignes:
                quantite = Decimal(str(ligne.quantite))
                prix = Decimal(str(ligne.prix_unitaire))
                taux_tva = Decimal(str(ligne.taux_tva or 0))
                
                montant_ht = quantite * prix
                montant_tva = montant_ht * (taux_tva / Decimal('100'))
                total += montant_ht + montant_tva
            
            return total
            
        except Exception as e:
            print(f"❌ Erreur calcul vente POS: {e}")
            return Decimal('0.00')
    
    def calculer_marge_brute(self, entreprise):
        """Calcule la marge brute en pourcentage - Version finale"""
        try:
            Facture = self.get_model_by_app_label('Facture', 'ventes')
            FactureFournisseur = self.get_model_by_app_label('FactureFournisseur', 'achats')
            
            if not Facture or not FactureFournisseur:
                return 0
                
            debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Chiffre d'affaires TTC
            ca = Facture.objects.filter(
                entreprise=entreprise,
                date_facture__gte=debut_mois,
                statut__in=['payee', 'payé', 'paid', 'paye_partiel', 'paye_complet']
            ).aggregate(total=Sum('total_ttc'))['total'] or 0
            
            # Coût des achats HT
            cout_achats = FactureFournisseur.objects.filter(
                entreprise=entreprise,
                date_facture__gte=debut_mois,
                statut__in=['payee', 'payé', 'paid', 'validee']
            ).aggregate(total=Sum('montant_ht'))['total'] or 0
            
            if ca > 0 and cout_achats > 0:
                marge = ((ca - cout_achats) / ca) * 100
                print(f"📊 Marge brute calculée: {marge:.2f}%")
                return round(float(marge), 2)
            
            return 0
        except Exception as e:
            print(f"❌ Erreur calcul marge: {e}")
            return 0

    def get_ventes_chart_data(self, entreprise):
        """Données pour le graphique des ventes - Version finale"""
        try:
            Facture = self.get_model_by_app_label('Facture', 'ventes')
            if not Facture:
                return self.get_mock_ventes_data()
                
            from django.db.models.functions import TruncMonth
            
            # Ventes des 6 derniers mois
            six_mois = timezone.now() - timedelta(days=180)
            ventes = Facture.objects.filter(
                entreprise=entreprise,
                date_facture__gte=six_mois,
                statut__in=['payee', 'payé', 'paid', 'paye_partiel', 'paye_complet']
            ).annotate(mois=TruncMonth('date_facture')).values('mois').annotate(
                total=Sum('total_ttc')
            ).order_by('mois')
            
            if ventes.exists():
                print(f"📈 Données ventes réelles trouvées: {len(ventes)} mois")
                return {
                    'labels': [v['mois'].strftime('%b %Y') for v in ventes],
                    'data': [float(v['total'] or 0) for v in ventes]
                }
            
            print("ℹ️ Aucune donnée de vente, utilisation des données mockées")
            return self.get_mock_ventes_data()
        except Exception as e:
            print(f"❌ Erreur données ventes: {e}")
            return self.get_mock_ventes_data()

    def get_stocks_chart_data(self, entreprise):
        """Données pour le graphique des stocks - Version finale"""
        try:
            Produit = self.get_model_by_app_label('Produit', 'STOCK')
            if not Produit:
                return self.get_mock_stocks_data()
                
            # Top 10 produits par valeur de stock
            produits = Produit.objects.filter(entreprise=entreprise).annotate(
                valeur_stock=F('stock') * F('prix_achat')
            ).order_by('-valeur_stock')[:10]
            
            if produits.exists():
                print(f"📦 Données stocks réelles trouvées: {produits.count()} produits")
                return {
                    'labels': [p.nom[:20] + '...' if len(p.nom) > 20 else p.nom for p in produits],
                    'data': [float(p.valeur_stock) for p in produits]
                }
            
            print("ℹ️ Aucune donnée de stock, utilisation des données mockées")
            return self.get_mock_stocks_data()
        except Exception as e:
            print(f"❌ Erreur données stocks: {e}")
            return self.get_mock_stocks_data()
    
    def calculer_rotation_stocks(self, entreprise):
        """Calcule la rotation des stocks"""
        try:
            Produit = self.get_model_by_app_label('Produit', 'STOCK')
            MouvementStock = self.get_model_by_app_label('MouvementStock', 'STOCK')
            
            if not Produit or not MouvementStock:
                return 0
                
            # Valeur moyenne du stock
            valeur_stock = Produit.objects.filter(
                entreprise=entreprise
            ).aggregate(total=Sum(F('quantite') * F('prix_achat')))['total'] or 0
            
            # Coût des ventes du mois (approximé)
            debut_mois = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            cout_ventes = MouvementStock.objects.filter(
                entreprise=entreprise,
                type_mouvement='sortie',
                date_mouvement__gte=debut_mois
            ).aggregate(total=Sum(F('quantite') * F('prix_unitaire')))['total'] or 0
            
            if valeur_stock > 0:
                rotation = cout_ventes / valeur_stock
                return round(float(rotation), 2)
            return 0
        except Exception as e:
            logger.error(f"Erreur calcul rotation stocks: {e}")
            return 0
    
    def calculer_dmp_clients(self, entreprise):
        """Calcule le délai moyen de paiement clients"""
        try:
            Facture = self.get_model_by_app_label('Facture', 'ventes')
            if not Facture:
                return 0
                
            factures_payees = Facture.objects.filter(
                entreprise=entreprise,
                statut='payee',
                date_paiement__isnull=False
            )
            
            if factures_payees.exists():
                # Calcul approximatif du délai moyen
                delai_moyen = factures_payees.aggregate(
                    moyenne=Avg(F('date_paiement') - F('date_creation'))
                )['moyenne']
                
                if delai_moyen:
                    return delai_moyen.days
            return 0
        except Exception as e:
            logger.error(f"Erreur calcul DMP: {e}")
            return 0
    
    def evaluer_formule_personnalisee(self, formule, entreprise):
        """Tente d'évaluer une formule personnalisée"""
        try:
            # Implémentation basique pour les formules simples
            if 'ventes' in formule and 'montant_total' in formule:
                return self.calculer_chiffre_d_affaires_mensuel(entreprise)
            return 0
        except Exception as e:
            logger.error(f"Erreur évaluation formule: {e}")
            return 0
    
    def get_ventes_chart_data(self, entreprise):
        """Données pour le graphique des ventes"""
        try:
            Facture = self.get_model_by_app_label('Facture', 'ventes')
            if not Facture:
                return self.get_mock_ventes_data()
                
            from django.db.models.functions import TruncMonth
            
            # Ventes des 6 derniers mois
            six_mois = timezone.now() - timedelta(days=180)
            ventes = Facture.objects.filter(
                entreprise=entreprise,
                date_creation__gte=six_mois,
                statut='payee'
            ).annotate(mois=TruncMonth('date_creation')).values('mois').annotate(
                total=Sum('montant_total')
            ).order_by('mois')
            
            if ventes.exists():
                return {
                    'labels': [v['mois'].strftime('%b %Y') for v in ventes],
                    'data': [float(v['total'] or 0) for v in ventes]
                }
            
            return self.get_mock_ventes_data()
        except Exception as e:
            logger.error(f"Erreur données ventes: {e}")
            return self.get_mock_ventes_data()
    
    def get_stocks_chart_data(self, entreprise):
        """Données pour le graphique des stocks"""
        try:
            Produit = self.get_model_by_app_label('Produit', 'STOCK')
            if not Produit:
                return self.get_mock_stocks_data()
                
            # Top 10 produits par valeur
            produits = Produit.objects.filter(entreprise=entreprise).annotate(
                valeur=F('quantite') * F('prix_achat')
            ).order_by('-valeur')[:10]
            
            if produits.exists():
                return {
                    'labels': [p.nom[:20] + '...' if len(p.nom) > 20 else p.nom for p in produits],
                    'data': [float(p.valeur) for p in produits]
                }
            
            return self.get_mock_stocks_data()
        except Exception as e:
            logger.error(f"Erreur données stocks: {e}")
            return self.get_mock_stocks_data()
    
    def get_finances_chart_data(self, entreprise):
        """Données pour le graphique des finances"""
        try:
            EcritureComptable = self.get_model_by_app_label('EcritureComptable', 'comptabilite')
            if not EcritureComptable:
                return self.get_mock_finances_data()
                
            # Répartition des charges et produits du mois
            charges = EcritureComptable.objects.filter(
                entreprise=entreprise,
                compte__type_compte='charge',
                date_comptable__month=timezone.now().month,
                date_comptable__year=timezone.now().year
            ).aggregate(total=Sum('montant_devise'))['total'] or 0
            
            produits = EcritureComptable.objects.filter(
                entreprise=entreprise,
                compte__type_compte='produit',
                date_comptable__month=timezone.now().month,
                date_comptable__year=timezone.now().year
            ).aggregate(total=Sum('montant_devise'))['total'] or 0
            
            return {
                'labels': ['Charges', 'Produits'],
                'data': [float(charges), float(produits)]
            }
        except Exception as e:
            logger.error(f"Erreur données finances: {e}")
            return self.get_mock_finances_data()
    
    def get_mock_ventes_data(self):
        """Retourne des données mockées pour les ventes"""
        from datetime import datetime, timedelta
        import random
        
        labels = []
        data = []
        now = timezone.now()
        
        for i in range(6):
            date = now - timedelta(days=30 * (5 - i))
            labels.append(date.strftime('%b %Y'))
            data.append(random.randint(100000, 500000))
        
        return {'labels': labels, 'data': data}
    
    def get_mock_stocks_data(self):
        """Retourne des données mockées pour les stocks"""
        labels = ['Produit A', 'Produit B', 'Produit C', 'Produit D', 'Produit E']
        data = [250000, 180000, 120000, 80000, 50000]
        return {'labels': labels, 'data': data}
    
    def get_mock_finances_data(self):
        """Retourne des données mockées pour les finances"""
        return {'labels': ['Charges', 'Produits'], 'data': [350000, 750000]}
    def debug_apps_models(self):
        """Debug complet des applications et modèles disponibles"""
        from django.apps import apps
        
        print("=== DEBUG APPLICATIONS ET MODÈLES ===")
        
        # Lister toutes les applications installées
        all_apps = apps.get_app_configs()
        print("Applications installées:")
        for app in all_apps:
            print(f"  - {app.label} ({app.name})")
        
        # Vérifier spécifiquement les applications dont on a besoin
        target_apps = ['ventes', 'achats', 'STOCK', 'comptabilite']
        
        for app_label in target_apps:
            try:
                app_config = apps.get_app_config(app_label)
                print(f"\n=== MODÈLES DE {app_label.upper()} ===")
                
                # Lister tous les modèles de cette application
                for model in app_config.get_models():
                    print(f"  - {model._meta.object_name}")
                    print(f"    Champs: {[f.name for f in model._meta.fields]}")
                    
                    # Afficher quelques instances pour vérifier
                    try:
                        count = model.objects.count()
                        print(f"    Nombre d'instances: {count}")
                        if count > 0:
                            first_instance = model.objects.first()
                            print(f"    Premier instance: {first_instance}")
                    except Exception as e:
                        print(f"    Erreur accès données: {e}")
                        
            except LookupError:
                print(f"\nApplication {app_label} NON TROUVÉE!")
        
        return True
        
        
class KPIListView(LoginRequiredMixin, EntrepriseAccessMixin, ListView):
    """Liste des KPIs"""
    model = KPI
    template_name = "bi/kpi_list.html"
    context_object_name = "kpis"
    permission_required = "bi.view_kpi"

    def get_queryset(self):
        return super().get_queryset().filter(entreprise=self.request.user.entreprise)
    
class KPICreateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, CreateView):
    """Création d'un KPI"""
    model = KPI
    form_class = KPIForm
    template_name = "bi/kpi_form.html"
    permission_required = "bi.add_kpi"
    success_url = reverse_lazy('bi:kpi_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['entreprise'] = self.request.user.entreprise
        return kwargs

    def form_valid(self, form):
        # Assigner l'utilisateur connecté et l'entreprise avant de sauvegarder
        form.instance.created_by = self.request.user
        form.instance.entreprise = self.request.user.entreprise
        
        # Remplacer automatiquement {{devise}} par le symbole de la devise principale
        if '{{devise}}' in form.cleaned_data.get('unite', ''):
            try:
                config_saas = ConfigurationSAAS.objects.get(entreprise=self.request.user.entreprise)
                devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
                form.instance.unite = form.cleaned_data['unite'].replace('{{devise}}', devise_symbole)
            except ConfigurationSAAS.DoesNotExist:
                form.instance.unite = form.cleaned_data['unite'].replace('{{devise}}', '€')
        
        return super().form_valid(form)
    
class KPIUpdateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin,UpdateView):
    """Modification d'un KPI"""
    model = KPI
    form_class = KPIForm
    template_name = "bi/kpi_form.html"
    permission_required = "bi.change_kpi"
    success_url = reverse_lazy('bi:kpi_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['entreprise'] = self.request.user.entreprise
        return kwargs

class KPIDeleteView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DeleteView):
    """Suppression d'un KPI"""
    model = KPI
    template_name = "bi/kpi_confirm_delete.html"
    permission_required = "bi.delete_kpi"
    success_url = reverse_lazy('bi:kpi_list')

class ReportListView(LoginRequiredMixin, EntrepriseAccessMixin, ListView):
    """Liste des rapports"""
    model = Report
    template_name = "bi/report_list.html"
    context_object_name = "rapports"
    permission_required = "bi.view_report"

    def get_queryset(self):
        return super().get_queryset().filter(entreprise=self.request.user.entreprise)

class ReportCreateView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin,CreateView):
    """Création d'un rapport"""
    model = Report
    form_class = ReportForm
    template_name = "bi/report_form.html"
    permission_required = "bi.add_report"
    success_url = reverse_lazy('bi:report_list')

class ReportDetailView(LoginRequiredMixin, PermissionRequiredMixin, EntrepriseAccessMixin, DetailView):
    """Détail d'un rapport"""
    model = Report
    template_name = "bi/report_detail.html"
    permission_required = "bi.view_report"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        entreprise = self.request.user.entreprise
        
        # Récupérer la devise principale
        try:
            config_saas = ConfigurationSAAS.objects.get(entreprise=entreprise)
            devise_symbole = config_saas.devise_principale.symbole if config_saas.devise_principale else "€"
        except ConfigurationSAAS.DoesNotExist:
            devise_symbole = "€"
        
        context['devise_symbole'] = devise_symbole
        
        # Diagnostic des données
        context['diagnostic'] = self.get_diagnostic_data(entreprise)
        
        # Récupérer les KPIs principaux
        kpis = KPI.objects.filter(entreprise=entreprise, actif=True)[:12]
        
        # Calculer les valeurs des KPIs
        kpi_values = {}
        kpi_details = {}
        
        for kpi in kpis:
            try:
                valeur, details = self.calculer_kpi(kpi, entreprise)
                kpi_values[kpi.id] = valeur
                kpi_details[kpi.id] = details
            except Exception as e:
                kpi_values[kpi.id] = None
                kpi_details[kpi.id] = f"Erreur: {str(e)}"
        
        context['kpis'] = kpis
        context['kpi_values'] = kpi_values
        context['kpi_details'] = kpi_details
        context['rapports'] = Report.objects.filter(entreprise=entreprise, public=True)[:5]
        
        # Données pour les graphiques
        context['ventes_data'] = self.get_ventes_chart_data(entreprise)
        context['stocks_data'] = self.get_stocks_chart_data(entreprise)
        context['finances_data'] = self.get_finances_chart_data(entreprise)
        
        return context
    
    def executer_rapport(self, rapport):
        # Exécuter la requête SQL ou le traitement du rapport
        if rapport.requete_sql:
            with connection.cursor() as cursor:
                cursor.execute(rapport.requete_sql)
                columns = [col[0] for col in cursor.description]
                data = [dict(zip(columns, row)) for row in cursor.fetchall()]
                return data
        return []

class DataExportView(LoginRequiredMixin, EntrepriseAccessMixin, CreateView):
    """Export de données"""
    model = DataExport
    form_class = ExportForm
    template_name = "bi/data_export.html"
    permission_required = "bi.export_data"
    success_url = reverse_lazy('bi:export_success')

    def form_valid(self, form):
        # Logique d'export
        response = super().form_valid(form)
        self.exporter_donnees(form.cleaned_data)
        return response
    
    def exporter_donnees(self, data):
        # Implémenter la logique d'export réelle
        pass

class DataImportView(LoginRequiredMixin, EntrepriseAccessMixin, CreateView):
    """Import de données"""
    model = DataImport
    form_class = ImportForm
    template_name = "bi/data_import.html"
    permission_required = "bi.import_data"
    success_url = reverse_lazy('bi:import_success')

    def form_valid(self, form):
        # Logique d'import
        response = super().form_valid(form)
        self.importer_donnees(form.cleaned_data, self.request.FILES['fichier'])
        return response
    
    def importer_donnees(self, data, fichier):
        # Implémenter la logique d'import réelle
        pass

class APIDashboardData(LoginRequiredMixin, View):
    """API pour les données du dashboard"""
    
    def get(self, request):
        entreprise = request.user.entreprise
        periode = request.GET.get('periode', 'month')
        
        data = {
            'ventes': self.get_ventes_data(entreprise, periode),
            'achats': self.get_achats_data(entreprise, periode),
            'stocks': self.get_stocks_data(entreprise),
            'finances': self.get_finances_data(entreprise),
        }
        
        return JsonResponse(data)
    
    def get_ventes_data(self, entreprise, periode):
        # Implémenter la récupération des données de ventes
        return {"total": 1500000, "evolution": 15.5}
    
    def get_achats_data(self, entreprise, periode):
        # Implémenter la récupération des données d'achats
        return {"total": 850000, "evolution": -8.2}
    
    def get_stocks_data(self, entreprise):
        # Implémenter la récupération des données de stocks
        return {"valeur": 450000, "rotation": 2.8}
    
    def get_finances_data(self, entreprise):
        # Implémenter la récupération des données financières
        return {"profit": 250000, "marge": 28.5}