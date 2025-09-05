# chatbot_utils.py
import openai
from django.conf import settings
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
from STOCK.models import *
import json

class ChatbotAI:
    def __init__(self):
        self.settings = ChatbotSettings.load()
        openai.api_key = self.settings.api_key or settings.OPENAI_API_KEY
        self.system_prompt = """
        Vous êtes un assistant intégré à un système de gestion de stock et de vente. 
        Vous avez accès aux données en temps réel et pouvez effectuer des requêtes précises.
        Répondez de manière concise et utile aux questions des utilisateurs.
        
        Fonctions disponibles:
        - get_stock(product_name): Retourne le stock actuel d'un produit
        - get_sales(product_name, period): Retourne les ventes d'un produit
        - get_product_price(product_name): Retourne le prix d'un produit
        - list_low_stock(): Liste les produits en faible stock
        - get_client_info(client_name): Donne des infos sur un client
        - get_product_sales_comparison(period): Compare les ventes de produits
        
        Exemples de réponses:
        - "Le produit 'X' a 15 unités en stock."
        - "Le prix de 'Y' est de 25.99€."
        - "Voici les produits en faible stock: ..."
        """

    def generate_response(self, conversation, user_message):
        # D'abord vérifier si c'est une requête de données spécifique
        data_response = self._handle_data_queries(user_message)
        if data_response:
            return data_response

        # Ensuite vérifier la base de connaissances
        kb_response = self._check_knowledge_base(user_message)
        if kb_response:
            return kb_response

        # Si rien trouvé, utiliser l'API OpenAI
        return self._generate_ai_response(conversation, user_message)

    def _handle_data_queries(self, query):
        query = query.lower()
        
        # Détection des requêtes sur les stocks
        if "stock" in query or "quantité" in query:
            product_name = self._extract_product_name(query)
            if product_name:
                return self._get_stock_info(product_name)
            elif "faible" in query or "alerte" in query:
                return self._list_low_stock()

        # Requêtes sur les prix
        elif "prix" in query:
            product_name = self._extract_product_name(query)
            if product_name:
                return self._get_product_price(product_name)

        # Requêtes sur les ventes
        elif "vente" in query or "vendu" in query:
            product_name = self._extract_product_name(query)
            period = self._extract_period(query)
            return self._get_sales_info(product_name, period)

        return None

    def _extract_product_name(self, query):
        # Essaye d'extraire un nom de produit de la requête
        products = Produit.objects.all()
        for p in products:
            if p.nom.lower() in query.lower():
                return p.nom
        return None

    def _extract_period(self, query):
        if "mois passé" in query or "dernier mois" in query:
            return "last_month"
        elif "semaine" in query:
            return "last_week"
        elif "année" in query or "an" in query:
            return "last_year"
        return "all_time"

    def _get_stock_info(self, product_name):
        try:
            produit = Produit.objects.get(nom__iexact=product_name)
            return f"Le produit '{produit.nom}' a {produit.stock} unités en stock (seuil d'alerte: {produit.seuil_alerte})."
        except Produit.DoesNotExist:
            return f"Je n'ai pas trouvé de produit nommé '{product_name}'."

    def _get_product_price(self, product_name):
        try:
            produit = Produit.objects.get(nom__iexact=product_name)
            return f"Le prix du produit '{produit.nom}' est de {produit.prix_vente} {produit.devise if hasattr(produit, 'devise') else '€'}."
        except Produit.DoesNotExist:
            return f"Je n'ai pas trouvé de produit nommé '{product_name}'."

    def _list_low_stock(self):
        produits = Produit.objects.filter(stock__lte=F('seuil_alerte')).order_by('stock')
        if not produits.exists():
            return "Aucun produit n'est actuellement en faible stock."
        
        response = "Produits en faible stock:\n"
        for p in produits:
            response += f"- {p.nom}: {p.stock} unités (seuil: {p.seuil_alerte})\n"
        return response

    def _get_sales_info(self, product_name=None, period="last_month"):
        date_filters = {
            'last_week': Q(commande__date_commande__gte=datetime.now()-timedelta(days=7)),
            'last_month': Q(commande__date_commande__gte=datetime.now()-timedelta(days=30)),
            'last_year': Q(commande__date_commande__gte=datetime.now()-timedelta(days=365)),
            'all_time': Q()
        }
        
        filter_q = date_filters.get(period, Q())
        
        if product_name:
            try:
                produit = Produit.objects.get(nom__iexact=product_name)
                total = LigneCommande.objects.filter(
                    produit=produit
                ).filter(
                    filter_q
                ).aggregate(
                    total=Sum('quantite')
                )['total'] or 0
                
                return f"Le produit '{product_name}' a été vendu {total} fois {self._get_period_text(period)}."
            except Produit.DoesNotExist:
                return f"Je n'ai pas trouvé de produit nommé '{product_name}'."
        else:
            # Top 5 des produits vendus
            top_products = LigneCommande.objects.filter(
                filter_q
            ).values(
                'produit__nom'
            ).annotate(
                total=Sum('quantite')
            ).order_by('-total')[:5]
            
            if not top_products:
                return f"Aucune vente enregistrée {self._get_period_text(period)}."
            
            response = f"Top {len(top_products)} produits vendus {self._get_period_text(period)}:\n"
            for item in top_products:
                response += f"- {item['produit__nom']}: {item['total']} ventes\n"
            return response

    def _get_period_text(self, period):
        texts = {
            'last_week': "cette semaine",
            'last_month': "ce mois-ci",
            'last_year': "cette année",
            'all_time': "au total"
        }
        return texts.get(period, "")

    # ... (keep the rest of the methods from previous version)