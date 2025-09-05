import openai
from django.conf import settings

client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

def repondre_au_message(message, historique=None):
    messages = [{"role": "system", "content": "Tu es un assistant expert en gestion de stock et de vente."}]

    if historique:
        messages += historique
    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.3
    )

    return response.choices[0].message.content
