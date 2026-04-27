import os
import logging
import requests
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from openai import OpenAI

# ========= CONFIG =========
TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")
MANAGER_ID = int(os.getenv("MANAGER_ID", "5705817827"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(level=logging.INFO)

user_state = {}
dialog_memory = {}

# ========= AI =========

async def ai_agent(user_id, text):
    try:
        history = dialog_memory.get(user_id, [])

        messages = [
            {
                "role": "system",
                "content": """
Ты топовый агент недвижимости.

Твоя задача:
— понять запрос
— задать уточняющие вопросы
— предложить варианты
— довести до оставления номера

Правила:
— не пиши "напиши подробнее"
— говори конкретно
— всегда веди к действию
— если мало данных: спроси город и бюджет
— если достаточно данных: предложи варианты и дожми

Стиль:
живой, уверенный, как риелтор
"""
            }
        ] + history + [{"role": "user", "content": text}]

        res = client.chat.completions.create(
            model="gpt-5",
            messages=messages
        )

        reply = res.choices[0].message.content

        # сохраняем диалог
        dialog_memory[user_id] = history + [
            {"role": "user", "content": text},
            {"role": "assistant", "content": reply}
        ]

        return reply

    except Exception as e:
        print("AI ERROR:", e)
        return "Скажи город и бюджет, подберу варианты 👇"


# ========= API =========

def search_property():
    try:
        return requests.get(f"{API_URL}/properties", timeout=5).json()
    except:
        return []

def ai_search(text):
    try:
        return requests.post(f"{API_URL}/ai-search", json={"text": text}, timeout=5).json()
    except:
        return []

def create_property(data):
    try:
        return requests.post(f"{API_URL}/property", json=data, timeout=5).json()
    except:
        return {}

def send_lead(phone):
    try:
        requests.post(f"{API_URL}/lead", json={"phone": phone}, timeout=5)
    except:
        pass

# ========= UI =========

def main_menu():
    return ReplyKeyboardMarkup([
        ["🔍 Купить", "🏠 Аренда"],
        ["➕ Подать", "💰 VIP"]
    ], resize_keyboard=True)

# ========= START =========

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏠 ESTA Недвижимость\n\nЧто ищешь?",
        reply_markup=main_menu()
    )

# ========= HANDLE =========

async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        text = update.message.text

        print("USER:", text)

        # ===== ШАГ PHONE =====
        if user_id in user_state and user_state[user_id].get("step") == "phone":
            if len(text) >= 9:
                await ctx.bot.send_message(
                    MANAGER_ID,
                    f"🔥 ГОРЯЧИЙ ЛИД\nТелефон: {text}"
                )

                send_lead(text)

                await update.message.reply_text("✅ Мы скоро свяжемся")
                user_state.pop(user_id)
                return

        # ===== ДОБАВИТЬ =====
        if text == "➕ Подать":
            user_state[user_id] = {"step": "title"}
            await update.message.reply_text("✏️ Введите заголовок:")
            return

        if user_id in user_state:
            s = user_state[user_id]

            if s["step"] == "title":
                s["title"] = text
                s["step"] = "price"
                await update.message.reply_text("💰 Введите цену:")
                return

            if s["step"] == "price":
                try:
                    price = float(text.replace(" ", "").replace(",", ""))
                except:
                    await update.message.reply_text("⚠️ Введите цену цифрами")
                    return

                create_property({
                    "title": s["title"],
                    "price": price,
                    "deal_type": "sale"
                })

                await update.message.reply_text(
                    "✅ Объявление добавлено",
                    reply_markup=main_menu()
                )

                user_state.pop(user_id)
                return

        # ===== AI SEARCH (умный поиск по базе) =====
        data = ai_search(text)

        if data:
            for p in data:
                await update.message.reply_text(
                    f"🏠 {p.get('title')}\n📍 {p.get('city','')}\n💰 ${p.get('price')}"
                )

            await update.message.reply_text(
                "Хочешь ещё варианты или подобрать под тебя? Оставь номер 👇"
            )

            user_state[user_id] = {"step": "phone"}
            return

        # ===== КНОПКИ =====
        if text in ["🔍 Купить", "🏠 Аренда"]:
            await update.message.reply_text(
                "Скажи город и бюджет 👇"
            )
            return

        if text == "💰 VIP":
            await update.message.reply_text(
                "🚀 VIP размещение скоро будет доступно"
            )
            return

        # ===== AI =====
        reply = await ai_agent(user_id, text)
        await update.message.reply_text(reply)

    except Exception as e:
        print("BOT ERROR:", e)
        await update.message.reply_text("⚠️ Ошибка, попробуй ещё раз")

# ========= MAIN =========

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    print("🔥 ESTA AI BOT STARTED")
    app.run_polling()

if __name__ == "__main__":
    main()
