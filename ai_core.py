import json
import requests
from openai import OpenAI

class AICore:
    def __init__(self, api_url, openai_key):
        self.api_url = api_url
        self.client = OpenAI(api_key=openai_key)

    # ===== 1) PARSE: текст → фильтры =====
    async def parse(self, text: str):
        resp = self.client.responses.create(
            model="gpt-5.5",
            reasoning={"effort": "low"},
            input=[
                {
                    "role": "system",
                    "content": (
                        "Разбери запрос пользователя в JSON фильтры недвижимости.\n"
                        "Формат:\n"
                        "{\n"
                        ' "deal_type": "sale|rent",\n'
                        ' "property_type": "apartment|house|land|commercial",\n'
                        ' "city": string|null,\n'
                        ' "rooms": int|null,\n'
                        ' "max_price": int|null\n'
                        "}\n"
                        "Если нет данных — null. Только JSON, без текста."
                    )
                },
                {"role": "user", "content": text}
            ]
        )
        try:
            return json.loads(resp.output_text)
        except Exception:
            return {}

    # ===== 2) SEARCH: запрос в backend =====
    def search(self, filters: dict):
        try:
            return requests.get(
                f"{self.api_url}/properties",
                params=filters,
                timeout=5
            ).json()
        except Exception:
            return []

    # ===== 3) RANK: выбрать топ-3 =====
    async def rank(self, text: str, properties: list):
        resp = self.client.responses.create(
            model="gpt-5.5",
            reasoning={"effort": "medium"},
            input=[
                {
                    "role": "system",
                    "content": "Выбери 3 лучших варианта под запрос. Верни только ID через запятую."
                },
                {
                    "role": "user",
                    "content": f"Запрос: {text}\nОбъекты: {properties}"
                }
            ]
        )
        ids = resp.output_text.split(",")
        return [int(i.strip()) for i in ids if i.strip().isdigit()]

    # ===== 4) REPLY: короткий ответ-риелтор =====
    async def reply(self, text: str, properties: list):
        resp = self.client.responses.create(
            model="gpt-5.5",
            reasoning={"effort": "medium"},
            text={"verbosity": "low"},
            input=[
                {
                    "role": "system",
                    "content": (
                        "Ты риелтор. Коротко: предложи варианты, задай 1 вопрос, "
                        "подведи к действию (просмотр/заявка)."
                    )
                },
                {
                    "role": "user",
                    "content": f"{text}\nВарианты: {properties}"
                }
            ]
        )
        return resp.output_text

    # ===== PIPELINE =====
    async def run(self, text: str):
        filters = await self.parse(text)
        data = self.search(filters)

        if not data:
            return [], "❌ Ничего не найдено. Уточни параметры (город/бюджет)."

        top_ids = await self.rank(text, data)
        top = [p for p in data if p.get("id") in top_ids][:3]

        reply = await self.reply(text, top)
        return top, reply
