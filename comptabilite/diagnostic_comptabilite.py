import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Gstock.settings')
django.setup()

import logging
logging.basicConfig(level=logging.DEBUG)

from django.db import connection
from comptabilite.models import JournalComptable, PlanComptableOHADA, EcritureComptable, LigneEcriture
from STOCK.models import MouvementStock
from parametres.models import Entreprise
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

def diagnostic_complet():
    """Diagnostic complet du module comptabilité"""
    print("=" * 60)
    print("DIAGNOSTIC COMPLET MODULE COMPTABILITÉ")
    print("=" * 60)
    
    # 1. Vérification de la connexion à la base de données
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✓ Connexion à la base de données: OK")
    except Exception as e:
        print(f"✗ Erreur connexion base de données: {e}")
        return False
    
    # 2. Vérification des entreprises
    entreprises = Entreprise.objects.all()
    print(f"Nombre d'entreprises: {entreprises.count()}")
    
    for entreprise in entreprises:
        print(f"\n--- ENTREPRISE: {entreprise.nom} ---")
        
        # 3. Vérification des journaux comptables
        journaux = JournalComptable.objects.filter(entreprise=entreprise)
        print(f"Journaux comptables: {journaux.count()}")
        
        journal_stk = JournalComptable.objects.filter(code='STK', entreprise=entreprise).first()
        if journal_stk:
            print(f"✓ Journal STK: {journal_stk.intitule}")
        else:
            print("✗ Journal STK: MANQUANT - Création...")
            try:
                journal_stk = JournalComptable.objects.create(
                    code='STK',
                    intitule='Journal des Stocks',
                    type_journal='divers',
                    entreprise=entreprise
                )
                print(f"✓ Journal STK créé: {journal_stk.intitule}")
            except Exception as e:
                print(f"✗ Erreur création journal STK: {e}")
        
        # 4. Vérification des comptes comptables
        comptes = PlanComptableOHADA.objects.filter(entreprise=entreprise)
        print(f"Comptes comptables: {comptes.count()}")
        
        # Comptes essentiels pour les stocks
        comptes_essentiels = ['31', '6037']
        for compte_num in comptes_essentiels:
            compte = PlanComptableOHADA.objects.filter(numero=compte_num, entreprise=entreprise).first()
            if compte:
                print(f"✓ Compte {compte_num}: {compte.intitule}")
            else:
                print(f"✗ Compte {compte_num}: MANQUANT - Création...")
                try:
                    if compte_num == '31':
                        nouveau_compte = PlanComptableOHADA.objects.create(
                            numero='31',
                            entreprise=entreprise,
                            classe='3',
                            intitule='Stocks',
                            type_compte='actif',
                            description='Stocks de matières et marchandises'
                        )
                    elif compte_num == '6037':
                        nouveau_compte = PlanComptableOHADA.objects.create(
                            numero='6037',
                            entreprise=entreprise,
                            classe='6',
                            intitule='Variation des stocks (inventaires)',
                            type_compte='charge',
                            description='Ajustements de stocks suite aux inventaires'
                        )
                    print(f"✓ Compte {compte_num} créé: {nouveau_compte.intitule}")
                except Exception as e:
                    print(f"✗ Erreur création compte {compte_num}: {e}")
        
        # 5. Vérification des écritures existantes
        ecritures = EcritureComptable.objects.filter(entreprise=entreprise)
        print(f"Écritures comptables existantes: {ecritures.count()}")
        
        # 6. Vérification des mouvements de stock
        mouvements = MouvementStock.objects.filter(entreprise=entreprise, type_mouvement='ajustement')
        print(f"Mouvements d'ajustement: {mouvements.count()}")
        
        for mouvement in mouvements[:5]:  # Afficher les 5 premiers
            ecriture_liee = hasattr(mouvement, 'ecriturecomptable') if hasattr(mouvement, 'ecriturecomptable') else False
            print(f"  - Mouvement {mouvement.id}: Écriture liée = {ecriture_liee}")
    
    # 7. Test de création d'écriture manuelle
    print(f"\n--- TEST CRÉATION MANUELLE ---")
    test_creation_manuelle()
    
    print("\n" + "=" * 60)
    print("DIAGNOSTIC TERMINÉ")
    print("=" * 60)

def test_creation_manuelle():
    """Test de création manuelle d'écriture comptable"""
    try:
        entreprise = Entreprise.objects.first()
        user = get_user_model().objects.first()
        
        if not entreprise or not user:
            print("✗ Données manquantes pour le test")
            return False
        
        # Vérifier et créer les prérequis
        journal, created = JournalComptable.objects.get_or_create(
            code='STK',
            entreprise=entreprise,
            defaults={
                'intitule': 'Journal des Stocks',
                'type_journal': 'divers'
            }
        )
        
        compte_stock, created = PlanComptableOHADA.objects.get_or_create(
            numero='31',
            entreprise=entreprise,
            defaults={
                'classe': '3',
                'intitule': 'Stocks',
                'type_compte': 'actif'
            }
        )
        
        compte_variation, created = PlanComptableOHADA.objects.get_or_create(
            numero='6037',
            entreprise=entreprise,
            defaults={
                'classe': '6',
                'intitule': 'Variation des stocks',
                'type_compte': 'charge'
            }
        )
        
        # Créer une écriture manuellement
        from django.utils import timezone
        ecriture = EcritureComptable.objects.create(
            journal=journal,
            numero=f"TEST-{timezone.now().strftime('%Y%m%d')}-001",
            date_ecriture=timezone.now(),
            date_comptable=timezone.now().date(),
            libelle="Test manuel d'écriture",
            piece_justificative="TEST-MANUEL",
            montant_devise=100.00,
            entreprise=entreprise,
            created_by=user
        )
        
        # Créer les lignes d'écriture
        LigneEcriture.objects.create(
            ecriture=ecriture,
            compte=compte_stock,
            libelle="Test débit",
            debit=100.00,
            credit=0,
            entreprise=entreprise
        )
        
        LigneEcriture.objects.create(
            ecriture=ecriture,
            compte=compte_variation,
            libelle="Test crédit",
            debit=0,
            credit=100.00,
            entreprise=entreprise
        )
        
        print("✓ Test manuel réussi - Écriture créée")
        print(f"  - Écriture: {ecriture.numero}")
        print(f"  - Lignes: {ecriture.lignes.count()}")
        
        # Nettoyer le test
        ecriture.delete()
        print("✓ Test nettoyé")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur test manuel: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    diagnostic_complet()