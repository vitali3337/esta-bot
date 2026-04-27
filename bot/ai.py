from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def ai_funnel(text):
    res = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {
                "role": "system",
                "content": """
Ты AI брокер недвижимости.

Цель:
— довести клиента до контакта

Правила:
— коротко
— задавай вопрос
— веди к действию
"""
            },
            {"role": "user", "content": text}
        ]
    )

    return res.choices[0].message.content
