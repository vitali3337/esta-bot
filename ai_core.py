import json
import requests
from openai import OpenAI

class AICore:
    def __init__(self, api_url, openai_key):
        self.api_url = api_url
        self.client = OpenAI(api_key=openai_key)

    # ================= AI PARSE =================
    async def parse(self, text):
        response = self.client.responses.create(
            model="gpt-5.5",
            reasoning={"effort": "low"},
            input=[
                {
                    "role": "system",
                    "content": """
Разбери запрос пользователя в JSON.

Формат:
{
 "deal_type": "sale|rent",
 "property_type": "apartment|house",
 "city": "",
 "rooms": int,
 "max_price": int
}

Если нет данных — null
Только JSON
"""
                },
                {"role": "user", "content": text}
            ]
        )

        try:
            return json.loads(response.output_text)
        except:
            return {}

    # ================= SEARCH =================
    def search(self, filters):
        try:
            return requests.get(
                f"{self.api_url}/properties",
                params=filters,
                timeout=5
            ).json()
        except:
            return []

    # ================= RANK =================
    async def rank(self, text, properties):
        response = self.client.responses.create(
            model="gpt-5.5",
            reasoning={"effort": "medium"},
            input=[
                {
                    "role": "system",
                    "content": "Выбери 3 лучших объекта. Верни только ID через запятую."
                },
                {
                    "role": "user",
                    "content": f"{text}\n{properties}"
                }
            ]
        )

        ids = response.output_text.split(",")

        return [
            int(i.strip())
            for i in ids
            if i.strip().isdigit()
        ]

    # ================= REPLY =================
    async def reply(self, text, properties):
        response = self.client.responses.create(
            model="gpt-5.5",
            reasoning={"effort": "medium"},
            text={"verbosity": "low"},
            input=[
                {
                    "role": "system",
                    "content": """
Ты топ агент недвижимости.

Задача:
— предложить варианты
— задать 1 вопрос
— довести до заявки

Коротко.
"""
                },
                {
                    "role": "user",
                    "content": f"{text}\nВарианты: {properties}"
                }
            ]
        )

        return response.output_text

    # ================= PIPELINE =================
    async def run(self, text):
        filters = await self.parse(text)

        data = self.search(filters)

        if not data:
            return [], "❌ Ничего не найдено. Уточни запрос"

        top_ids = await self.rank(text, data)

        top = [p for p in data if p.get("id") in top_ids]

        reply = await self.reply(text, top)

        return top, reply
