from rest_framework import serializers
from STOCK.models import Produit, Categorie, Client
from ventes.models import VentePOS, LigneVentePOS, PointDeVente, SessionPOS
from parametres.models import ConfigurationSAAS, Devise
from security.models import UtilisateurPersonnalise

class DeviseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Devise
        fields = ['id', 'code', 'nom', 'symbole', 'taux_change']

class ProduitSerializer(serializers.ModelSerializer):
    categorie_nom = serializers.CharField(source='categorie.nom', read_only=True)
    unite_mesure_display = serializers.CharField(source='get_unite_mesure_display', read_only=True)
    
    class Meta:
        model = Produit
        fields = [
            'id', 'nom', 'description', 'code_barre_numero', 'prix_achat', 
            'prix_vente', 'taux_tva', 'stock', 'seuil_alerte', 'categorie',
            'categorie_nom', 'photo', 'unite_mesure', 'unite_mesure_display',
            'actif', 'created_at', 'updated_at'
        ]

class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'nom', 'adresse', 'telephone', 'email', 'solde']

class PointDeVenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PointDeVente
        fields = ['id', 'nom', 'code', 'adresse', 'telephone', 'actif']

class SessionPOSSerializer(serializers.ModelSerializer):
    point_de_vente_nom = serializers.CharField(source='point_de_vente.nom', read_only=True)
    utilisateur_nom = serializers.CharField(source='utilisateur.get_full_name', read_only=True)
    
    class Meta:
        model = SessionPOS
        fields = [
            'id', 'point_de_vente', 'point_de_vente_nom', 'utilisateur', 'utilisateur_nom',
            'fonds_ouverture', 'fonds_fermeture', 'total_ventes', 'statut',
            'date_ouverture', 'date_fermeture'
        ]

class LigneVentePOSSerializer(serializers.ModelSerializer):
    produit_nom = serializers.CharField(source='produit.nom', read_only=True)
    produit_code = serializers.CharField(source='produit.code_barre_numero', read_only=True)
    
    class Meta:
        model = LigneVentePOS
        fields = [
            'id', 'produit', 'produit_nom', 'produit_code', 'quantite',
            'prix_unitaire', 'taux_tva', 'montant_ht', 'montant_tva'
        ]

class VentePOSSerializer(serializers.ModelSerializer):
    lignes = LigneVentePOSSerializer(many=True, read_only=True)
    client_nom = serializers.CharField(source='client.nom', read_only=True)
    session_point_de_vente = serializers.CharField(source='session.point_de_vente.nom', read_only=True)
    
    class Meta:
        model = VentePOS
        fields = [
            'id', 'numero', 'date', 'session', 'session_point_de_vente', 'client', 'client_nom',
            'remise', 'total_ht', 'total_tva', 'total_ttc', 'statut', 'est_payee',
            'lignes', 'created_at', 'updated_at'
        ]

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UtilisateurPersonnalise
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'entreprise']

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()