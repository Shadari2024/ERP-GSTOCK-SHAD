from django.utils import timezone
from django.db.models import Sum, Q
import logging
from .models import GrandLivre, Balance, Bilan, EcritureComptable, LigneEcriture

logger = logging.getLogger(__name__)

def generate_ecriture_number(journal):
    """Génère un numéro d'écriture séquentiel"""
    try:
        today = timezone.now().date()
        last_ecriture = EcritureComptable.objects.filter(
            journal=journal,
            date_ecriture__date=today
        ).order_by('-numero').first()
        
        sequence = 1
        if last_ecriture and last_ecriture.numero:
            try:
                # Format: STK-20231201-0001
                parts = last_ecriture.numero.split('-')
                if len(parts) >= 3:
                    sequence = int(parts[-1]) + 1
            except (ValueError, IndexError):
                pass
        
        return f"{journal.code}-{today.strftime('%Y%m%d')}-{sequence:04d}"
    except Exception as e:
        logger.error(f"Erreur génération numéro d'écriture: {e}")
        return f"{journal.code}-{timezone.now().strftime('%Y%m%d')}-0001"

def update_grand_livre(ecriture, entreprise):
    """Met à jour le Grand Livre avec une nouvelle écriture"""
    try:
        for ligne in ecriture.lignes.all():
            GrandLivre.objects.create(
                compte=ligne.compte,
                date=ecriture.date_comptable,
                libelle=ecriture.libelle,
                piece_justificative=ecriture.piece_justificative,
                journal=ecriture.journal,
                debit=ligne.debit,
                credit=ligne.credit,
                solde_debiteur=0,
                solde_crediteur=0,
                entreprise=entreprise
            )
        
        recalculer_soldes_grand_livre(ecriture.date_comptable, entreprise)
        
    except Exception as e:
        logger.error(f"Erreur mise à jour Grand Livre: {e}")

def recalculer_soldes_grand_livre(date, entreprise):
    """Recalcule les soldes du Grand Livre"""
    try:
        comptes = GrandLivre.objects.filter(
            entreprise=entreprise,
            date__lte=date
        ).values('compte').distinct()
        
        for compte_data in comptes:
            lignes = GrandLivre.objects.filter(
                compte_id=compte_data['compte'],
                entreprise=entreprise,
                date__lte=date
            ).order_by('date', 'id')
            
            solde_debiteur = 0
            solde_crediteur = 0
            
            for ligne in lignes:
                solde_debiteur += float(ligne.debit or 0)
                solde_crediteur += float(ligne.credit or 0)
                
                ligne.solde_debiteur = max(0, solde_debiteur - solde_crediteur)
                ligne.solde_crediteur = max(0, solde_crediteur - solde_debiteur)
                ligne.save()
                
    except Exception as e:
        logger.error(f"Erreur recalcul soldes Grand Livre: {e}")

def update_balance(entreprise, date):
    """Met à jour la Balance comptable"""
    try:
        soldes = GrandLivre.objects.filter(
            entreprise=entreprise,
            date__lte=date
        ).values('compte').annotate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit')
        )
        
        for solde in soldes:
            Balance.objects.update_or_create(
                compte_id=solde['compte'],
                date=date,
                entreprise=entreprise,
                defaults={
                    'total_debit': solde['total_debit'] or 0,
                    'total_credit': solde['total_credit'] or 0,
                    'solde_debiteur': max(0, (solde['total_debit'] or 0) - (solde['total_credit'] or 0)),
                    'solde_crediteur': max(0, (solde['total_credit'] or 0) - (solde['total_debit'] or 0))
                }
            )
            
    except Exception as e:
        logger.error(f"Erreur mise à jour Balance: {e}")

def update_bilan(entreprise, date):
    """Met à jour le Bilan comptable"""
    try:
        classes = ['1', '2', '3', '4', '5']
        
        for classe in classes:
            total_actif = Balance.objects.filter(
                entreprise=entreprise,
                compte__classe=classe,
                date=date
            ).aggregate(
                total=Sum('solde_debiteur') - Sum('solde_crediteur')
            )['total'] or 0
            
            Bilan.objects.update_or_create(
                entreprise=entreprise,
                date=date,
                classe=classe,
                defaults={'montant': max(0, total_actif)}
            )
                
    except Exception as e:
        logger.error(f"Erreur mise à jour Bilan: {e}")