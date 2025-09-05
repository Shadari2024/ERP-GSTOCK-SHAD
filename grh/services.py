from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from .models import Presence, Contrat, Employe, BulletinPaie, LigneBulletinPaie

from datetime import datetime, date, timedelta
from decimal import Decimal
from django.utils import timezone

class CalculPaieService:
    
    @staticmethod
    def calculer_salaire_brut(employe, periode):
        """Calcule le salaire brut basé sur la présence"""
        try:
            # Convertir la période en dates
            annee, mois = map(int, periode.split('-'))
            date_debut_periode = date(annee, mois, 1)
            if mois == 12:
                date_fin_periode = date(annee + 1, 1, 1) - timedelta(days=1)
            else:
                date_fin_periode = date(annee, mois + 1, 1) - timedelta(days=1)
            
            print(f"🔍 Recherche contrat pour {employe.nom_complet}")
            print(f"📅 Période demandée: {date_debut_periode} to {date_fin_periode}")
            
            # Récupérer TOUS les contrats de l'employé
            tous_contrats = Contrat.objects.filter(employe=employe)
            print(f"📋 Total contrats trouvés: {tous_contrats.count()}")
            
            for c in tous_contrats:
                print(f"   - {c.reference}: {c.statut}, {c.date_debut} to {c.date_fin}")
            
            # Chercher un contrat ACTIF qui couvre la période
            contrats_valides = []
            for contrat in tous_contrats:
                if contrat.statut != 'EN_COURS':
                    print(f"   ❌ Contrat {contrat.reference} ignoré (statut: {contrat.statut})")
                    continue
                
                # Vérifier la couverture de la période
                contrat_couvre_periode = (
                    contrat.date_debut <= date_fin_periode and 
                    (contrat.date_fin is None or contrat.date_fin >= date_debut_periode)
                )
                
                if contrat_couvre_periode:
                    print(f"   ✅ Contrat {contrat.reference} VALIDE pour la période")
                    contrats_valides.append(contrat)
                else:
                    print(f"   ❌ Contrat {contrat.reference} ne couvre pas la période")
            
            # Prendre le contrat le plus récent
            contrat = sorted(contrats_valides, key=lambda x: x.date_debut, reverse=True)[0] if contrats_valides else None
            
            if not contrat:
                print(f"❌ Aucun contrat valide trouvé pour {employe.nom_complet}")
                return Decimal('0'), 0, Decimal('0'), None
            
            print(f"✅ Contrat sélectionné: {contrat.reference}")
            print(f"💰 Salaire de base du contrat: {contrat.salaire_base}")
            
            # Calculer la période effective du contrat dans le mois
            date_debut_effective = max(contrat.date_debut, date_debut_periode)
            date_fin_effective = contrat.date_fin if contrat.date_fin else date_fin_periode
            date_fin_effective = min(date_fin_effective, date_fin_periode)
            
            # Nombre de jours du contrat dans la période
            jours_contrat_periode = (date_fin_effective - date_debut_effective).days + 1
            jours_total_periode = (date_fin_periode - date_debut_periode).days + 1
            
            print(f"📆 Jours contrat dans période: {jours_contrat_periode}/{jours_total_periode}")
            
            # Récupérer les présences du mois
            presences = Presence.objects.filter(
                employe=employe,
                date__gte=date_debut_periode,
                date__lte=date_fin_periode,
                statut='PRESENT'
            )
            
            jours_travailles = presences.count()
            print(f"👨‍💼 Jours travaillés trouvés: {jours_travailles}")
            
            # Si le contrat ne couvre pas tout le mois, proratiser le salaire de base
            if jours_contrat_periode < jours_total_periode:
                print(f"⚖️  Proratisation nécessaire: {jours_contrat_periode}/{jours_total_periode} jours")
                salaire_base_proratise = (contrat.salaire_base * Decimal(jours_contrat_periode) / Decimal(jours_total_periode))
                print(f"💰 Salaire de base proratisé: {salaire_base_proratise}")
            else:
                salaire_base_proratise = contrat.salaire_base
            
            # Si pas de présence mais contrat existe, utiliser le salaire de base proratisé
            if jours_travailles == 0:
                print(f"📊 Aucune présence trouvée, utilisation du salaire de base proratisé")
                return salaire_base_proratise, jours_contrat_periode, Decimal('0'), contrat
            
            # Calculer le salaire de base proportionnel aux jours travaillés
            salaire_journalier = salaire_base_proratise / Decimal(str(jours_contrat_periode))
            salaire_base = salaire_journalier * Decimal(str(jours_travailles))
            
            print(f"🧮 Calcul journalier: {salaire_base_proratise} / {jours_contrat_periode} = {salaire_journalier}/jour")
            print(f"🧾 Salaire base pour {jours_travailles} jours: {salaire_base}")
            
            # Calcul des heures supplémentaires
            heures_supp = CalculPaieService.calculer_heures_supplementaires(presences, contrat)
            taux_hs = Decimal('1.25')
            
            # Calcul du taux horaire basé sur le salaire mensuel
            taux_horaire = salaire_base_proratise / Decimal('173.33')  # 173.33 heures/mois en moyenne
            montant_hs = taux_horaire * taux_hs * heures_supp
            
            print(f"⏰ Heures supplémentaires: {heures_supp}h, Montant: {montant_hs}")
            
            # Prime d'ancienneté (sur le salaire de base complet, pas proratisé)
            prime_anciennete = CalculPaieService.calculer_prime_anciennete(contrat.salaire_base, employe.anciennete())
            print(f"🎖️  Prime ancienneté: {prime_anciennete}")
            
            # Total salaire brut
            salaire_brut = salaire_base + montant_hs + prime_anciennete
            
            print(f"💵 Calcul final - Base: {salaire_base}, HS: {montant_hs}, Prime: {prime_anciennete}, Total: {salaire_brut}")
            
            return salaire_brut, jours_travailles, heures_supp, contrat
            
        except Exception as e:
            print(f"❌ Erreur calcul salaire pour {employe.nom_complet}: {str(e)}")
            import traceback
            traceback.print_exc()
            return Decimal('0'), 0, Decimal('0'), None
    
    @staticmethod
    def calculer_heures_supplementaires(presences, contrat):
        """Calcule les heures supplémentaires"""
        heures_supp = Decimal('0')
        try:
            for presence in presences:
                if presence.heures_travaillees > Decimal('8'):  # Plus de 8 heures par jour
                    heures_supp += presence.heures_travaillees - Decimal('8')
            return heures_supp
        except:
            return Decimal('0')
    
    @staticmethod
    def calculer_prime_anciennete(salaire_base, annees_anciennete):
        """Calcule la prime d'ancienneté (2% par année)"""
        if annees_anciennete > 0:
            return salaire_base * Decimal('0.02') * Decimal(str(annees_anciennete))
        return Decimal('0')
    
    @staticmethod
    def calculer_cotisations(salaire_brut):
        """Calcule les cotisations sociales (10% du brut)"""
        return salaire_brut * Decimal('0.10')
    
    @staticmethod
    @transaction.atomic
    def generer_bulletin_automatique(employe, periode):
        """Génère automatiquement un bulletin de paie"""
        try:
            # Vérifier si un bulletin existe déjà pour cette période
            existing_bulletin = BulletinPaie.objects.filter(
                employe=employe,
                periode=periode,
                entreprise=employe.entreprise
            ).first()
            
            if existing_bulletin:
                return existing_bulletin
            
            # Calculer le salaire brut
            resultat_calcul = CalculPaieService.calculer_salaire_brut(employe, periode)
            if not resultat_calcul:
                return None
                
            salaire_brut, jours_travailles, heures_supp, contrat = resultat_calcul
            
            if salaire_brut == 0 or contrat is None:
                return None
            
            # Calculer les cotisations
            total_cotisations = CalculPaieService.calculer_cotisations(salaire_brut)
            salaire_net = salaire_brut - total_cotisations
            
            # Créer le bulletin
            bulletin = BulletinPaie.objects.create(
                entreprise=employe.entreprise,
                employe=employe,
                contrat=contrat,
                periode=periode,
                salaire_brut=salaire_brut,
                total_cotisations=total_cotisations,
                salaire_net=salaire_net,
                net_a_payer=salaire_net,
                jours_travailles=jours_travailles,
                heures_travaillees=heures_supp + (jours_travailles * 8)
            )
            
            # Ajouter les lignes détaillées
            lignes = [
                ('GAINS', 'Salaire de base', salaire_brut - (salaire_brut * Decimal('0.25') * heures_supp), 1),
                ('GAINS', 'Heures supplémentaires', salaire_brut * Decimal('0.25') * heures_supp, 2),
                ('GAINS', 'Prime ancienneté', CalculPaieService.calculer_prime_anciennete(contrat.salaire_base, employe.anciennete()), 3),
                ('RETENUES', 'CNSS', salaire_brut * CalculPaieService.TAUX_CNSS, 4),
                ('RETENUES', 'Impôt', salaire_brut * CalculPaieService.TAUX_IMPOT, 5),
                ('RETENUES', 'Autres cotisations', salaire_brut * CalculPaieService.TAUX_AUTRES, 6),
            ]
            
            for type_ligne, libelle, montant, ordre in lignes:
                if montant > 0:
                    LigneBulletinPaie.objects.create(
                        bulletin=bulletin,
                        type_ligne=type_ligne,
                        libelle=libelle,
                        montant=montant,
                        ordre=ordre
                    )
            
            return bulletin
            
        except Exception as e:
            print(f"Erreur génération bulletin automatique: {e}")
            return None
    
    @staticmethod
    def generer_bulletins_masse(periode, entreprise):
        """Génère les bulletins pour tous les employés actifs"""
        employes = Employe.objects.filter(entreprise=entreprise, statut='ACTIF')
        bulletins_crees = []
        
        for employe in employes:
            bulletin = CalculPaieService.generer_bulletin_automatique(employe, periode)
            if bulletin:
                bulletins_crees.append(bulletin)
        
        return bulletins_crees