from django.test import TestCase
from .models import Commande, Facture

class FactureTestCase(TestCase):
    def test_creation_auto(self):
        commande = Commande.objects.create(vente_confirmee=True, montant_total=100)
        facture = Facture.objects.get(commande=commande)
        self.assertEqual(facture.montant_total, 100)
        
        
        
        
# tests.py
from django.test import TestCase
from django.urls import reverse

class FactureViewsTest(TestCase):
    def test_paiement_post(self):
        facture = Facture.objects.create(...)
        response = self.client.post(
            reverse('enregistrer_paiement', args=[facture.id]),
            {'montant': '100', 'methode': 'carte'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(facture.paiement_set.count(), 1)