from django.core.management.base import BaseCommand
from app.models import ChatbotKnowledgeBase

DEFAULT_KNOWLEDGE = [
    {
        "question": "Comment voir le stock d'un produit?",
        "answer": "Vous pouvez demander 'Quel est le stock de [nom du produit]?' ou 'Quels produits sont en faible stock?'",
        "topic": "stock",
        "keywords": "stock, quantité, inventaire"
    },
    {
        "question": "Comment voir les ventes d'un produit?",
        "answer": "Demandez 'Combien de [produit] a été vendu ce mois-ci?' ou 'Quels sont les produits les plus vendus?'",
        "topic": "vente",
        "keywords": "vente, vendu, chiffre, statistiques"
    },
    {
        "question": "Comment connaître le prix d'un produit?",
        "answer": "Demandez simplement 'Quel est le prix de [produit]?'",
        "topic": "vente",
        "keywords": "prix, coût, tarif"
    }
]

class Command(BaseCommand):
    help = 'Populate the chatbot knowledge base with default questions'

    def handle(self, *args, **options):
        for item in DEFAULT_KNOWLEDGE:
            ChatbotKnowledgeBase.objects.get_or_create(
                question=item['question'],
                defaults={
                    'answer': item['answer'],
                    'topic': item['topic'],
                    'keywords': item['keywords']
                }
            )
        self.stdout.write(self.style.SUCCESS('Knowledge base populated successfully'))