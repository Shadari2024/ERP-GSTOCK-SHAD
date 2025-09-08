from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from security.views import dashboard_redirect

urlpatterns = [
    # path('admin/', admin.site.urls),
    # path('admin/', RedirectView.as_view(url='/dashboard/admin', permanent=True)),
    path('', dashboard_redirect, name='root_redirect'),
    path('', include('security.urls')),
    path('parametres/', include('parametres.urls')),
    path('Achats/', include('achats.urls')),
    path('ventes/', include('ventes.urls')),
    path('STOCK/', include('STOCK.urls')),
    path('Promotion/', include('promotions.urls')),
    path('comptabilite/', include('comptabilite.urls')),
    path('grh/', include('grh.urls', namespace='grh')),
    path('vitrine/', include('vitrine.urls', namespace='vitrine')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)