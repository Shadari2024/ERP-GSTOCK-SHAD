from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'produits', views.ProduitViewSet, basename='produit')
router.register(r'clients', views.ClientViewSet, basename='client')
router.register(r'points-de-vente', views.PointDeVenteViewSet, basename='pointdevente')
router.register(r'sessions', views.SessionPOSViewSet, basename='sessionpos')
router.register(r'ventes', views.VentePOSViewSet, basename='ventepos')

urlpatterns = [
    path('', include(router.urls)),
    
    # Routes d'authentification personnalisées
    path('auth/login/', views.custom_login, name='api-login'),
    path('auth/logout/', views.custom_logout, name='api-logout'),
]