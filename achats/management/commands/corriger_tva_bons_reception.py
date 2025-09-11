# management/commands/corriger_tva_bons_reception.py
from django.core.management.base import BaseCommand
from achats.models import *
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Corrige les incohérences TVA dans les bons de réception'

    def handle(self, *args, **options):
        self.stdout.write("=== CORRECTION DES INCOHÉRENCES TVA BONS DE RÉCEPTION ===")
        
        # Corriger tous les bons de réception
        bons = BonReception.objects.all()
        
        for bon in bons:
            lignes_corrigees = 0
            for ligne in bon.lignes.all():
                if ligne.ligne_commande and ligne.taux_tva != ligne.ligne_commande.taux_tva:
                    ancien_taux = ligne.taux_tva
                    ligne.taux_tva = ligne.ligne_commande.taux_tva
                    ligne.save()
                    lignes_corrigees += 1
                    
                    self.stdout.write(
                        f"Bon {bon.numero_bon} - Ligne {ligne.id}: "
                        f"TVA {ancien_tva}→{ligne.ligne_commande.taux_tva}"
                    )
            
            if lignes_corrigees > 0:
                # Recalculer les totaux
                bon.calculer_totaux()
                self.stdout.write(
                    f"Bon {bon.numero_bon} recalculé: "
                    f"HT={bon.total_ht}, TVA={bon.total_tva}, TTC={bon.total_ttc}"
                )
        
        self.stdout.write(self.style.SUCCESS("=== CORRECTION TERMINÉE ==="))