from django.core.management.base import BaseCommand
from parametres.models import Entreprise
from comptabilite.models import PlanComptableOHADA, JournalComptable

class Command(BaseCommand):
    help = 'Initialise le plan comptable OHADA pour toutes les entreprises'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--entreprise',
            type=int,
            help='ID de l\'entreprise spécifique à initialiser'
        )
    
    def handle(self, *args, **options):
        entreprise_id = options.get('entreprise')
        
        if entreprise_id:
            entreprises = Entreprise.objects.filter(id=entreprise_id)
        else:
            entreprises = Entreprise.objects.all()
        
        for entreprise in entreprises:
            self.stdout.write(f'Initialisation du plan comptable pour {entreprise.nom}...')
            
            # Utilisez les méthodes de classe correctement
            comptes_crees = PlanComptableOHADA.initialiser_plan_comptable(entreprise)
            journaux_crees = JournalComptable.initialiser_journaux(entreprise)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ {len(comptes_crees)} comptes et {len(journaux_crees)} journaux créés pour {entreprise.nom}'
                )
            )