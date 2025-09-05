from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import Group, Permission
from .models import UtilisateurPersonnalise

class SecuriteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Créer des groupes de test
        cls.groupe_admin = Group.objects.create(name='Admin')
        cls.groupe_caissier = Group.objects.create(name='Caissier')
        
        # Créer des utilisateurs de test
        cls.admin = UtilisateurPersonnalise.objects.create_user(
            username='admin',
            password='adminpass',
            type_utilisateur='admin',
            est_actif=True
        )
        cls.admin.groups.add(cls.groupe_admin)
        
        cls.caissier = UtilisateurPersonnalise.objects.create_user(
            username='caissier',
            password='caissierpass',
            type_utilisateur='caissier',
            est_actif=True
        )
        cls.caissier.groups.add(cls.groupe_caissier)
    
    def test_acces_admin(self):
        client = Client()
        client.login(username='admin', password='adminpass')
        response = client.get(reverse('liste_utilisateurs'))
        self.assertEqual(response.status_code, 200)
    
    def test_acces_interdit_caissier(self):
        client = Client()
        client.login(username='caissier', password='caissierpass')
        response = client.get(reverse('liste_utilisateurs'))
        self.assertEqual(response.status_code, 403)
    
    def test_utilisateur_inactif(self):
        self.admin.est_actif = False
        self.admin.save()
        client = Client()
        response = client.login(username='admin', password='adminpass')
        self.assertFalse(response)
    
    def test_changement_mdp_obligatoire(self):
        self.admin.doit_changer_mdp = True
        self.admin.save()
        client = Client()
        client.login(username='admin', password='adminpass')
        response = client.get(reverse('tableau_de_bord'))
        self.assertRedirects(response, reverse('changement_mdp'))