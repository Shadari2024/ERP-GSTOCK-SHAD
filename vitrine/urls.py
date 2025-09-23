# CORRECTION - urls.py
from django.urls import path
from . import views

app_name = 'vitrine'

urlpatterns = [
    path('', views.AccueilView.as_view(), name='accueil'),
    path('features/', views.FeaturesView.as_view(), name='features'),
    path('pricing/', views.PricingView.as_view(), name='pricing'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('demo/', views.DemandeDemoCreateView.as_view(), name='demo'),
    # 🔥 CORRECTION : Utiliser DemoSuccessView pour la page de succès
    path('demo/success/', views.DemoSuccessView.as_view(), name='demo_success'),
]