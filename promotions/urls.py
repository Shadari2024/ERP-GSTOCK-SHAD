from django.urls import path
from django.utils.translation import gettext_lazy as _
from . import views

app_name = "promotions"

urlpatterns = [
    # URLs principales
    path("", views.PromotionDashboardView.as_view(), name="dashboard"),
    path("promotions/", views.PromotionListView.as_view(), name="promotion_list"),
    path("promotions/nouveau/", views.PromotionCreateView.as_view(), name="promotion_create"),
    path("promotions/<int:pk>/", views.PromotionDetailView.as_view(), name="promotion_detail"),
    path("promotions/<int:pk>/modifier/", views.PromotionUpdateView.as_view(), name="promotion_update"),
    path("promotions/<int:pk>/supprimer/", views.PromotionDeleteView.as_view(), name="promotion_delete"),
      path("promotions/<int:pk>/activer/", views.PromotionActivateView.as_view(), name="promotion_activate"),
    path("promotions/<int:pk>/desactiver/", views.PromotionDeactivateView.as_view(), name="promotion_deactivate"),
    # URLs pour les statistiques et rapports
    path("statistiques/", views.PromotionStatsView.as_view(), name="promotion_stats"),
    path("rapports/", views.PromotionReportView.as_view(), name="promotion_report"),
    
    # API endpoints
    path("api/promotions-actives/", views.ActivePromotionsAPIView.as_view(), name="api_active_promotions"),
    path("api/promotions-produit/<int:produit_id>/", views.ProductPromotionsAPIView.as_view(), name="api_product_promotions"),
]