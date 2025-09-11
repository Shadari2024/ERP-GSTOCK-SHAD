# management/commands/corriger_comptes_urgence.py
from django.core.management.base import BaseCommand
from comptabilite.models import PlanComptableOHADA, JournalComptable
from parametres.models import Entreprise
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Correction URGENTE des comptes manquants'

    def handle(self, *args, **options):
        for entreprise in Entreprise.objects.all():
            self.stdout.write(f"\n🔧 CORRECTION URGENTE pour: {entreprise.nom}")
            
            # Créer les comptes MANQUANTS URGENTS
            comptes_urgents = [
                {'numero': '521', 'intitule': 'Banque', 'classe': '5', 'type_compte': 'actif'},
                {'numero': '511', 'intitule': 'Chèques à encaisser', 'classe': '5', 'type_compte': 'actif'},
                {'numero': '531', 'intitule': 'Caisse', 'classe': '5', 'type_compte': 'actif'},
                {'numero': '4456', 'intitule': 'TVA déductible', 'classe': '4', 'type_compte': 'actif'},
                {'numero': '607', 'intitule': 'Achats de marchandises', 'classe': '6', 'type_compte': 'charge'},
            ]
            
            for compte_data in comptes_urgents:
                try:
                    compte, created = PlanComptableOHADA.objects.get_or_create(
                        numero=compte_data['numero'],
                        entreprise=entreprise,
                        defaults={
                            'classe': compte_data['classe'],
                            'intitule': compte_data['intitule'],
                            'type_compte': compte_data['type_compte'],
                            'description': f"Compte {compte_data['numero']} - {compte_data['intitule']}"
                        }
                    )
                    if created:
                        self.stdout.write(f"✅ Créé: {compte.numero} - {compte.intitule}")
                    else:
                        self.stdout.write(f"✓ Existe: {compte.numero} - {compte.intitule}")
                except Exception as e:
                    self.stdout.write(f"❌ Erreur création {compte_data['numero']}: {e}")
            
            # Créer le journal TRS URGENT
            try:
                journal, created = JournalComptable.objects.get_or_create(
                    code='TRS',
                    entreprise=entreprise,
                    defaults={
                        'intitule': 'Journal de Trésorerie',
                        'type_journal': 'banque',
                        'actif': True
                    }
                )
                if created:
                    self.stdout.write(f"✅ Journal créé: TRS - Journal de Trésorerie")
                else:
                    self.stdout.write(f"✓ Journal existe: TRS - {journal.intitule}")
            except Exception as e:
                self.stdout.write(f"❌ Erreur création journal TRS: {e}")
            
            self.stdout.write(f"✅ Correction terminée pour {entreprise.nom}")