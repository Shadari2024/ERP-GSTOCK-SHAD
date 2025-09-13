from django.urls import path
from . import views

app_name = 'bi'

urlpatterns = [
     path('', views.AccueilView.as_view(), name='accueil'),
    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # KPIs
    path('kpis/', views.KPIListView.as_view(), name='kpi_list'),
    path('kpis/ajouter/', views.KPICreateView.as_view(), name='kpi_create'),
    path('kpis/<int:pk>/modifier/', views.KPIUpdateView.as_view(), name='kpi_update'),
    path('kpis/<int:pk>/supprimer/', views.KPIDeleteView.as_view(), name='kpi_delete'),
    
    # Rapports
    path('rapports/', views.ReportListView.as_view(), name='report_list'),
    path('rapports/ajouter/', views.ReportCreateView.as_view(), name='report_create'),
    path('rapports/<int:pk>/', views.ReportDetailView.as_view(), name='report_detail'),
    
    # Export/Import
    path('export/', views.DataExportView.as_view(), name='data_export'),
    path('import/', views.DataImportView.as_view(), name='data_import'),
    
    # API
    path('api/dashboard-data/', views.APIDashboardData.as_view(), name='api_dashboard_data'),
]