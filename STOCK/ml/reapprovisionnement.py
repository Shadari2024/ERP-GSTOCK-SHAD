import numpy as np
import pandas as pd
from datetime import timedelta
from sklearn.linear_model import LinearRegression
from django.utils import timezone

from STOCK.models import Produit, LigneCommande, SuggestionReapprovisionnement


def generer_suggestions_reapprovisionnement(jours_prevision=30):
    suggestions = []
    aujourd_hui = timezone.now().date()
    date_debut = aujourd_hui - timedelta(days=180)

    for produit in Produit.objects.all():
        lignes = LigneCommande.objects.filter(
            produit=produit,
            commande__date_commande__gte=date_debut
        ).order_by('commande__date_commande')

        if not lignes.exists():
            continue

        # Création du DataFrame à partir des ventes
        data = pd.DataFrame.from_records(
            lignes.values('commande__date_commande', 'quantite')
        )

        # Renommage pour standardiser la colonne de date
        data.rename(columns={'commande__date_commande': 'date_vente'}, inplace=True)

        # Agrégation par jour et interpolation des jours manquants avec 0
        data = data.groupby('date_vente').sum()
        data.index = pd.to_datetime(data.index)
        data = data.asfreq('D', fill_value=0)

        # Ajout de la colonne "jour" comme index numérique
        data['jour'] = np.arange(len(data))

        X = data[['jour']]
        y = data['quantite']

        # Vérification de variance : au moins 2 points différents
        if y.nunique() <= 1:
            continue  # Skip si pas assez de variation pour entraîner un modèle

        # Entraînement du modèle linéaire
        model = LinearRegression().fit(X, y)

        jour_futur = np.array([[len(data) + jours_prevision]])
        quantite_predite = model.predict(jour_futur)[0]

        # Calcul de la suggestion en comparant avec le stock actuel
        quantite_suggeree = max(0, int(round(quantite_predite - produit.stock)))

        # Debugging facultatif :
        print(f"{produit.nom} | Prédit: {quantite_predite:.2f} | Stock: {produit.stock} → Suggestion: {quantite_suggeree}")

        # ✅ Enregistrement dans la base
        SuggestionReapprovisionnement.objects.create(
            produit=produit,
            quantite_predite=int(round(quantite_predite)),
            quantite_suggeree=quantite_suggeree
        )

        # Ajout à la liste des suggestions retournées
        suggestions.append({
            'produit': produit,
            'quantite_predite': int(round(quantite_predite)),
            'quantite_suggeree': quantite_suggeree
        })

    return suggestions
