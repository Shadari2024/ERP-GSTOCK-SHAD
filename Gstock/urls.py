from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.shortcuts import redirect

# 🔥 CORRECTION : Redirection vers la vitrine
def redirect_to_vitrine(request):
    """Redirige explicitement vers la page d'accueil de la vitrine"""
    print("🔍 REDIRECTION: Racine → /vitrine/")
    return redirect('/vitrine/')

urlpatterns = [
    # 🔥 CORRECTION : Redirection de la racine vers la vitrine
    path("", redirect_to_vitrine, name='root_redirect'),
    
    # 🔥 CORRECTION : Inclure les URLs de la vitrine
    path('vitrine/', include('vitrine.urls', namespace='vitrine')),
    
    # Routes dashboard séparées
    path('dashboard/', include('security.urls')),

    # Autres applications
    path('parametres/', include('parametres.urls')),
    path('Achats/', include('achats.urls')),
    path('ventes/', include('ventes.urls')),
    path('STOCK/', include('STOCK.urls')),
    path('Promotion/', include('promotions.urls')),
    path('comptabilite/', include('comptabilite.urls')),
    path('crm/', include('crm.urls')),
    path('grh/', include('grh.urls', namespace='grh')),
    path('bi/', include('bi.urls', namespace='bi')),
    path('api/', include('api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += staticfiles_urlpatterns()