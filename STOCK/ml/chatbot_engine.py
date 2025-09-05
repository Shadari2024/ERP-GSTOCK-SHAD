from django.db.models import Sum, F, Q
from datetime import timedelta
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from STOCK.models import *
from parametres.models import ConfigurationSAAS  # Import ajouté
import logging

logger = logging.getLogger(__name__)

class ChatbotEngine:
    """Moteur de chatbot SaaS avec gestion de devise"""
    
    def __init__(self, user, enterprise=None, is_saas_admin=False):
        self.user = user
        self.enterprise = enterprise
        self.is_saas_admin = is_saas_admin
        self.context = []
        self._init_enterprise_filter()
        self.devise = self._get_enterprise_currency()  # Récupération de la devise

    def _init_enterprise_filter(self):
        """Initialise le filtre entreprise pour les requêtes"""
        if self.is_saas_admin:
            self.enterprise_filter = Q()
        elif self.enterprise:
            self.enterprise_filter = Q(entreprise=self.enterprise)
        else:
            self.enterprise_filter = Q(pk__isnull=True)

    def _get_enterprise_currency(self):
        """Récupère la devise principale de l'entreprise"""
        if not self.enterprise:
            return "FC"  # Devise par défaut
            
        try:
            config = ConfigurationSAAS.objects.get(entreprise=self.enterprise)
            return config.devise_principale.symbole if config.devise_principale else "FC"
        except ConfigurationSAAS.DoesNotExist:
            return "FC"  # Devise par défaut

    def process_query(self, query):
        """Traitement principal avec gestion SaaS"""
        try:
            query = query.lower().strip()
            self.context.append(query)

            # Vérification des permissions
            if not self._check_permissions(query):
                return f"⛔ Désolé, vous n'avez pas accès à cette information."

            # Questions fonctionnelles avec contexte SaaS
            if any(kw in query for kw in ['stock', 'quantité']):
                return self._handle_stock(query)
            elif any(kw in query for kw in ['vente', 'vendu']):
                return self._handle_sales(query)
            elif any(kw in query for kw in ['rentable', 'marge', 'bénéfice']):
                return self._handle_profit(query)
            elif any(kw in query for kw in ['client fidèle', 'meilleur client']):
                return self._handle_top_clients(query)
            elif any(kw in query for kw in ['retard', 'impayé', 'non payé']):
                return self._handle_unpaid_orders(query)
            elif 'ventes de' in query:
                return self._handle_sales_by_product(query)
            elif 'ventes du client' in query or 'client' in query:
                return self._handle_sales_by_client(query)

            # Base de connaissances avec filtrage entreprise
            reponse = self._handle_knowledge_base(query)
            if reponse:
                return reponse

            return self._handle_fallback()

        except Exception as e:
            logger.error(f"Chatbot error - User: {self.user.id} - Enterprise: {getattr(self.enterprise, 'id', None)} - Error: {str(e)}")
            return "⚠️ Une erreur est survenue. Notre équipe a été notifiée."

    def _format_currency(self, amount):
        """Formate un montant avec la devise de l'entreprise"""
        return f"{amount:.2f} {self.devise}"

    def _handle_sales(self, query):
        """Analyse des ventes avec devise"""
        periode_label, date_filter = self._detect_period(query)
        
        ventes = LigneCommande.objects.filter(
            self.enterprise_filter,
            commande__date_commande__gte=date_filter
        ).values('produit__nom').annotate(
            total=Sum('quantite'),
            revenue=Sum(F('quantite') * F('prix_unitaire'))
        ).order_by('-total')[:5]
        
        if not ventes:
            return f"📊 Aucune vente trouvée pour la période {periode_label}"
            
        response = f"💰 Top ventes ({periode_label}) :\n"
        for v in ventes:
            response += f"- {v['produit__nom']}: {v['total']} unités (CA: {self._format_currency(v['revenue'])}) \n"
            
        return response

    def _handle_profit(self, query):
        """Analyse de rentabilité avec devise"""
        produits = Produit.objects.filter(self.enterprise_filter).annotate(
            total_ventes=Sum('lignecommande__quantite'),
            total_revenue=Sum(F('lignecommande__quantite') * F('lignecommande__prix_unitaire')),
            total_cout=Sum(F('lignecommande__quantite') * F('prix_achat'))
        ).annotate(
            profit=F('total_revenue') - F('total_cout')
        ).order_by('-profit')[:5]
        
        if not produits:
            return "📊 Aucune donnée de rentabilité disponible"
            
        response = "📈 Produits les plus rentables :\n"
        for p in produits:
            marge = (p.profit / p.total_revenue * 100) if p.total_revenue else 0
            response += f"- {p.nom}: {self._format_currency(p.profit)} (marge: {marge:.1f}%)\n"
            
        return response

    def _handle_unpaid_orders(self, query):
        """Commandes impayées avec devise"""
        impayees = Commande.objects.filter(
            self.enterprise_filter,
            statut_paiement='impayé'
        ).select_related('client')[:10]
        
        if not impayees.exists():
            return "✅ Toutes les commandes sont payées."
            
        total = sum(c.montant_total for c in impayees)
        response = f"⚠️ Commandes impayées (Total: {self._format_currency(total)}) :\n"
        for c in impayees:
            response += f"- {c.client.nom}: {self._format_currency(c.montant_total)} depuis {c.date_commande.strftime('%d/%m/%Y')}\n"
            
        return response

    def _handle_sales_by_product(self, query):
        """Ventes par produit avec devise"""
        for produit in Produit.objects.filter(self.enterprise_filter):
            if produit.nom.lower() in query:
                ventes = LigneCommande.objects.filter(
                    self.enterprise_filter,
                    produit=produit
                ).aggregate(
                    total=Sum('quantite'),
                    revenu=Sum(F('quantite') * F('prix_unitaire')))
                
                total = ventes['total'] or 0
                revenu = ventes['revenu'] or 0
                return f"📦 Ventes de {produit.nom}: {total} unités, CA: {self._format_currency(revenu)}"
                
        return "❌ Produit introuvable ou non accessible"

    def _handle_sales_by_client(self, query):
        """Ventes par client avec devise"""
        for client in Client.objects.filter(self.enterprise_filter):
            if client.nom.lower() in query:
                commandes = Commande.objects.filter(
                    self.enterprise_filter,
                    client=client
                )
                
                total = commandes.aggregate(
                    total_qte=Sum('lignecommande__quantite'),
                    total_revenu=Sum(F('lignecommande__quantite') * F('lignecommande__prix_unitaire')))
                
                qte = total['total_qte'] or 0
                revenu = total['total_revenu'] or 0
                return f"🧾 Ventes à {client.nom}: {qte} articles, {self._format_currency(revenu)}"
                
        return "❌ Client introuvable ou non accessible"

    # ... (les autres méthodes restent inchangées)