# # STOCK/ml/prophet_utils.py
# from prophet import Prophet
# from prophet.diagnostics import cross_validation, performance_metrics
# import pandas as pd
# import numpy as np
# from STOCK.models import LigneCommande, HistoriquePrevision
# from django.utils import timezone
# import logging
# from datetime import timedelta
# from django.core.cache import cache
# import joblib
# from django.db import transaction

# logger = logging.getLogger(__name__)

# def generate_forecast(produit, period=14):
#     """Version robuste avec gestion des erreurs et historique"""
#     cache_key = f"forecast_{produit.id}_{period}"
    
#     # Vérifier le cache
#     if cached := cache.get(cache_key):
#         logger.info(f"Utilisation du cache pour {produit.nom}")
#         return (
#             pd.DataFrame(cached['history']),
#             pd.DataFrame(cached['forecast']), 
#             cached['performance']
#         )
    
#     try:
#         # Récupération et validation des données
#         commandes = LigneCommande.objects.filter(
#             produit=produit,
#             commande__vente_confirmee=True,
#             quantite__gt=0
#         ).order_by('commande__date_commande')
        
#         if commandes.count() < 3:
#             logger.info(f"Données insuffisantes pour {produit.nom} ({commandes.count()} commandes)")
#             return None, None, None
        
#         # Préparation des données
#         df = pd.DataFrame([{
#             'ds': c.commande.date_commande.date(),
#             'y': float(c.quantite)
#         } for c in commandes])
        
#         df = df.groupby('ds')['y'].sum().reset_index()
        
#         # Configuration adaptative
#         model_config = {
#             'daily_seasonality': len(df) > 7,
#             'weekly_seasonality': len(df) > 14,
#             'yearly_seasonality': len(df) > 365,
#             'changepoint_prior_scale': 0.05,
#             'seasonality_mode': 'additive',
#             'holidays': france_holidays()
#         }
        
#         logger.info(f"Configuration Prophet pour {produit.nom}: {model_config}")
        
#         # Entraînement du modèle
#         model = Prophet(**model_config)
#         model.fit(df)
        
#         # Génération des prévisions
#         future = model.make_future_dataframe(periods=period)
#         forecast = model.predict(future)
        
#         # Enregistrement dans l'historique
#         save_forecast_history(produit, forecast, model_config)
        
#         # Validation croisée (si assez de données)
#         performance = {}
#         if len(df) > 30:
#             try:
#                 df_cv = cross_validation(
#                     model,
#                     initial='30 days',
#                     period='15 days',
#                     horizon='30 days'
#                 )
#                 df_p = performance_metrics(df_cv)
#                 performance = {
#                     'mae': float(df_p['mae'].mean()),
#                     'rmse': float(df_p['rmse'].mean()),
#                     'mdape': float(df_p['mdape'].mean()),
#                     'coverage': float(df_p['coverage'].mean())
#                 }
#             except Exception as e:
#                 logger.warning(f"Erreur validation croisée: {str(e)}")
        
#         # Mise en cache
#         cache_data = {
#             'history': df.to_dict('records'),
#             'forecast': forecast.to_dict('records'),
#             'performance': performance
#         }
#         cache.set(cache_key, cache_data, timeout=3600*12)  # Cache 12h
        
#         return df, forecast, performance
        
#     except Exception as e:
#         logger.error(f"Erreur de prévision pour {produit.nom}: {str(e)}", exc_info=True)
#         return None, None, None

# def save_forecast_history(produit, forecast, model_config):
#     """Enregistre les prévisions dans l'historique"""
#     try:
#         with transaction.atomic():
#             # Supprimer les anciennes prévisions non réalisées
#             HistoriquePrevision.objects.filter(
#                 produit=produit,
#                 date_prevision__gte=timezone.now().date(),
#                 quantite_reelle__isnull=True
#             ).delete()
            
#             # Ajouter les nouvelles prévisions
#             for _, row in forecast.iterrows():
#                 if row['ds'].date() >= timezone.now().date():
#                     HistoriquePrevision.objects.create(
#                         produit=produit,
#                         date_prevision=row['ds'].date(),
#                         quantite_predite=int(round(row['yhat'])),
#                         modele_utilise='Prophet',
#                         parametres={
#                             'config': model_config,
#                             'confidence_lower': int(round(row['yhat_lower'])),
#                             'confidence_upper': int(round(row['yhat_upper']))
#                         }
#                     )
#     except Exception as e:
#         logger.error(f"Erreur enregistrement historique: {str(e)}")

# def france_holidays():
#     """Retourne les jours fériés français"""
#     return pd.DataFrame({
#         'holiday': 'fete',
#         'ds': pd.to_datetime([
#             '2023-01-01', '2023-04-10', '2023-05-01', '2023-05-08',
#             '2023-05-18', '2023-05-29', '2023-07-14', '2023-08-15',
#             '2023-11-01', '2023-11-11', '2023-12-25',
#             '2024-01-01', '2024-04-01', '2024-05-01', '2024-05-08',
#             '2024-05-09', '2024-05-20', '2024-07-14', '2024-08-15',
#             '2024-11-01', '2024-11-11', '2024-12-25'
#         ]),
#         'lower_window': -2,
#         'upper_window': 1
#     })