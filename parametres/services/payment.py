import stripe
from django.conf import settings
from django.urls import reverse
from decimal import Decimal
import logging
import json

logger = logging.getLogger(__name__)

# Configuration Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentService:
    @staticmethod
    def create_stripe_payment(abonnement, request):
        """Crée un paiement Stripe pour un abonnement"""
        try:
            # Création du produit et prix dans Stripe
            product = stripe.Product.create(
                name=f"Abonnement {abonnement.plan_actuel.nom}",
                description=f"Abonnement pour {abonnement.entreprise.nom}"
            )
            
            price = stripe.Price.create(
                product=product.id,
                unit_amount=int(abonnement.plan_actuel.prix_mensuel * 100),
                currency='eur',
                recurring={
                    'interval': 'month',
                    'interval_count': abonnement.plan_actuel.duree_mois
                } if abonnement.plan_actuel.duree_mois else None
            )
            
            # Création de la session de checkout
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price.id,
                    'quantity': 1,
                }],
                mode='subscription' if abonnement.plan_actuel.duree_mois else 'payment',
                success_url=request.build_absolute_uri(
                    reverse('payment:success') + f'?session_id={{CHECKOUT_SESSION_ID}}'
                ),
                cancel_url=request.build_absolute_uri(
                    reverse('payment:cancel')
                ),
                customer_email=request.user.email,
                metadata={
                    'abonnement_id': abonnement.id,
                    'entreprise_id': abonnement.entreprise.id,
                    'user_id': request.user.id
                }
            )
            
            return session
        except Exception as e:
            logger.error(f"Erreur création paiement Stripe: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def create_paypal_payment(abonnement, request):
        """Crée un paiement PayPal pour un abonnement"""
        try:
            # Solution alternative si le SDK PayPal n'est pas installé
            import requests
            
            auth_response = requests.post(
                f"{settings.PAYPAL_API_BASE}/v1/oauth2/token",
                auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET),
                data={"grant_type": "client_credentials"},
                headers={"Accept": "application/json"}
            )
            access_token = auth_response.json()['access_token']
            
            order_data = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "reference_id": str(abonnement.id),
                    "amount": {
                        "currency_code": "EUR",
                        "value": str(abonnement.plan_actuel.prix_mensuel),
                        "breakdown": {
                            "item_total": {
                                "currency_code": "EUR",
                                "value": str(abonnement.plan_actuel.prix_mensuel)
                            }
                        }
                    },
                    "items": [{
                        "name": f"Abonnement {abonnement.plan_actuel.nom}",
                        "description": f"Abonnement {abonnement.plan_actuel.get_niveau_display()}",
                        "quantity": "1",
                        "unit_amount": {
                            "currency_code": "EUR",
                            "value": str(abonnement.plan_actuel.prix_mensuel)
                        }
                    }],
                    "custom_id": str(abonnement.id),
                }],
                "application_context": {
                    "brand_name": settings.PAYPAL_BRAND_NAME,
                    "user_action": "PAY_NOW",
                    "return_url": request.build_absolute_uri(reverse('payment:success')),
                    "cancel_url": request.build_absolute_uri(reverse('payment:cancel')),
                }
            }
            
            response = requests.post(
                f"{settings.PAYPAL_API_BASE}/v2/checkout/orders",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}"
                },
                data=json.dumps(order_data)
            )
            
            if response.status_code != 201:
                raise Exception(f"Erreur PayPal: {response.text}")
                
            return response.json()
            
        except Exception as e:
            logger.error(f"Erreur création paiement PayPal: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def verifier_paiement_stripe(session_id):
        """Vérifie le statut d'un paiement Stripe"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            payment_intent = stripe.PaymentIntent.retrieve(session.payment_intent) if session.payment_intent else None
            
            return {
                'status': session.payment_status,
                'amount': session.amount_total / 100,
                'payment_method': session.payment_method_types[0] if session.payment_method_types else None,
                'metadata': session.metadata,
                'payment_intent': payment_intent
            }
        except Exception as e:
            logger.error(f"Erreur vérification paiement Stripe: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def capturer_paiement_paypal(order_id):
        """Capture un paiement PayPal"""
        try:
            import requests
            
            auth_response = requests.post(
                f"{settings.PAYPAL_API_BASE}/v1/oauth2/token",
                auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET),
                data={"grant_type": "client_credentials"},
                headers={"Accept": "application/json"}
            )
            access_token = auth_response.json()['access_token']
            
            response = requests.post(
                f"{settings.PAYPAL_API_BASE}/v2/checkout/orders/{order_id}/capture",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}"
                }
            )
            
            if response.status_code != 201:
                raise Exception(f"Erreur capture PayPal: {response.text}")
                
            return {
                'status': response.json()['status'],
                'amount': float(response.json()['purchase_units'][0]['payments']['captures'][0]['amount']['value']),
                'payment_method': 'paypal',
                'reference_id': response.json()['purchase_units'][0]['reference_id']
            }
            
        except Exception as e:
            logger.error(f"Erreur capture PayPal: {str(e)}", exc_info=True)
            raise