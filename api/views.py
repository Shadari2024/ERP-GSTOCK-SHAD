from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.db.models import Q, Sum, F
from django.utils import timezone
from datetime import datetime, timedelta

from STOCK.models import Produit, Categorie, Client
from ventes.models import VentePOS, LigneVentePOS, PointDeVente, SessionPOS
from parametres.models import ConfigurationSAAS
from security.models import UtilisateurPersonnalise
from .serializers import (
    ProduitSerializer, ClientSerializer, PointDeVenteSerializer,
    SessionPOSSerializer, VentePOSSerializer, UserSerializer, LoginSerializer
)
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def custom_login(request):
    """
    Vue personnalisée pour l'authentification API
    Évite les redirections de session Django
    """
    from .serializers import LoginSerializer
    
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        
        user = authenticate(username=username, password=password)
        if user and user.est_actif:
            # Créer ou récupérer le token
            token, created = Token.objects.get_or_create(user=user)
            
            # Récupérer les informations de l'entreprise et de la devise
            try:
                from parametres.models import ConfigurationSAAS
                config_saas = ConfigurationSAAS.objects.get(entreprise=user.entreprise)
                devise = {
                    'id': config_saas.devise_principale.id,
                    'code': config_saas.devise_principale.code,
                    'nom': config_saas.devise_principale.nom,
                    'symbole': config_saas.devise_principale.symbole
                } if config_saas.devise_principale else None
            except ConfigurationSAAS.DoesNotExist:
                devise = None
            
            from .serializers import UserSerializer
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data,
                'entreprise': {
                    'id': user.entreprise.id,
                    'nom': user.entreprise.nom,
                    'code': user.entreprise.code
                },
                'devise': devise
            })
        
        return Response(
            {'error': 'Identifiants invalides ou compte désactivé'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def custom_logout(request):
    """Déconnexion personnalisée"""
    try:
        request.user.auth_token.delete()
    except:
        pass
    return Response({'detail': 'Déconnexion réussie'})
class ProduitViewSet(viewsets.ModelViewSet):
    serializer_class = ProduitSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Produit.objects.filter(
            entreprise=self.request.user.entreprise,
            actif=True
        ).select_related('categorie')
        
        # Filtres
        search = self.request.query_params.get('search', None)
        categorie_id = self.request.query_params.get('categorie', None)
        code_barre = self.request.query_params.get('code_barre', None)
        
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) | 
                Q(description__icontains=search) |
                Q(code_barre_numero__icontains=search)
            )
        
        if categorie_id:
            queryset = queryset.filter(categorie_id=categorie_id)
        
        if code_barre:
            queryset = queryset.filter(code_barre_numero=code_barre)
        
        return queryset.order_by('nom')
    
    @action(detail=False, methods=['get'])
    def search_by_barcode(self, request):
        code_barre = request.query_params.get('barcode', '')
        if not code_barre:
            return Response({'error': 'Code barre requis'}, status=400)
        
        try:
            produit = Produit.objects.get(
                code_barre_numero=code_barre,
                entreprise=request.user.entreprise,
                actif=True
            )
            serializer = self.get_serializer(produit)
            return Response(serializer.data)
        except Produit.DoesNotExist:
            return Response({'error': 'Produit non trouvé'}, status=404)



from .serializers import ClientSerializer

class ClientViewSet(viewsets.ModelViewSet):
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Client.objects.filter(
            entreprise=self.request.user.entreprise
        ).order_by('nom')
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        clients = Client.objects.filter(
            entreprise=request.user.entreprise
        ).filter(
            Q(nom__icontains=query) | 
            Q(telephone__icontains=query) |
            Q(email__icontains=query)
        )[:10]  # La tranche [:10] doit être à la fin de la requête
        
        serializer = self.get_serializer(clients, many=True)
        return Response(serializer.data)
        
        serializer = self.get_serializer(clients, many=True)
        return Response(serializer.data)

class PointDeVenteViewSet(viewsets.ModelViewSet):
    serializer_class = PointDeVenteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return PointDeVente.objects.filter(
            entreprise=self.request.user.entreprise,
            actif=True
        ).order_by('nom')

class SessionPOSViewSet(viewsets.ModelViewSet):
    serializer_class = SessionPOSSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SessionPOS.objects.filter(
            point_de_vente__entreprise=self.request.user.entreprise
        ).select_related('point_de_vente', 'utilisateur').order_by('-date_ouverture')
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Récupère la session en cours pour l'utilisateur"""
        session = SessionPOS.objects.filter(
            utilisateur=request.user,
            statut='ouverte'
        ).select_related('point_de_vente').first()
        
        if session:
            serializer = self.get_serializer(session)
            return Response(serializer.data)
        return Response({'detail': 'Aucune session ouverte'}, status=404)
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Ferme une session"""
        session = self.get_object()
        if session.statut != 'ouverte':
            return Response({'error': 'Session déjà fermée'}, status=400)
        
        fonds_fermeture = request.data.get('fonds_fermeture', 0)
        try:
            # Méthode simplifiée pour fermer la session
            session.fonds_fermeture = fonds_fermeture
            session.statut = 'fermee'
            session.date_fermeture = timezone.now()
            session.save()
            
            serializer = self.get_serializer(session)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

class VentePOSViewSet(viewsets.ModelViewSet):
    serializer_class = VentePOSSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return VentePOS.objects.filter(
            session__point_de_vente__entreprise=self.request.user.entreprise
        ).select_related('session', 'client').prefetch_related('lignes').order_by('-date')
    
    def perform_create(self, serializer):
        # Récupérer la session en cours
        session = SessionPOS.objects.filter(
            utilisateur=self.request.user,
            statut='ouverte'
        ).first()
        
        if not session:
            raise serializers.ValidationError('Aucune session ouverte')
        
        vente = serializer.save(session=session)
        
        # Créer les lignes de vente
        lignes_data = self.request.data.get('lignes', [])
        for ligne_data in lignes_data:
            LigneVentePOS.objects.create(
                vente=vente,
                produit_id=ligne_data['produit_id'],
                quantite=ligne_data['quantite'],
                prix_unitaire=ligne_data['prix_unitaire'],
                taux_tva=ligne_data.get('taux_tva', 0)
            )
        
        # Mettre à jour les stocks
        for ligne_data in lignes_data:
            produit = Produit.objects.get(id=ligne_data['produit_id'])
            produit.stock -= ligne_data['quantite']
            produit.save()

class AuthViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            user = authenticate(username=username, password=password)
            if user and user.est_actif:
                # Créer ou récupérer le token
                token, created = Token.objects.get_or_create(user=user)
                
                # Récupérer les informations de l'entreprise et de la devise
                try:
                    config_saas = ConfigurationSAAS.objects.get(entreprise=user.entreprise)
                    devise = {
                        'id': config_saas.devise_principale.id,
                        'code': config_saas.devise_principale.code,
                        'nom': config_saas.devise_principale.nom,
                        'symbole': config_saas.devise_principale.symbole
                    } if config_saas.devise_principale else None
                except ConfigurationSAAS.DoesNotExist:
                    devise = None
                
                return Response({
                    'token': token.key,
                    'user': UserSerializer(user).data,
                    'entreprise': {
                        'id': user.entreprise.id,
                        'nom': user.entreprise.nom,
                        'code': user.entreprise.code
                    },
                    'devise': devise
                })
            
            return Response({'error': 'Identifiants invalides'}, status=400)
        
        return Response(serializer.errors, status=400)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        try:
            request.user.auth_token.delete()
        except:
            pass
        return Response({'detail': 'Déconnexion réussie'})