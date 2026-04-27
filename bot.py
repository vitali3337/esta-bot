import os
import logging
import requests
from telegram import *
from telegram.ext import *
from openai import OpenAI

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")
MANAGER_ID = int(os.getenv("MANAGER_ID", "5705817827"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(level=logging.INFO)

# ================= STATE =================
user_state = {}

# ================= AI =================

async def ai_funnel(text):
    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {
                "role": "system",
                "content": """
Ты AI брокер недвижимости.

Твоя цель:
— довести клиента до заявки

Правила:
— коротко
— задавай вопрос
— веди к действию
— предлагай просмотр или варианты
"""
            },
            {"role": "user", "content": text}
        ]
    )

    return response.choices[0].message.content


# ================= API =================

def create_property(data):
    return requests.post(f"{API_URL}/property", json=data).json()

def search_property(params={}):
    return requests.get(f"{API_URL}/properties", params=params).json()

def send_lead(data):
    return requests.post(f"{API_URL}/lead", json=data).json()


# ================= UI =================

def main_menu():
    return ReplyKeyboardMarkup([
        ["🔍 Поиск", "➕ Подать"],
        ["💰 VIP", "📞 Контакт"]
    ], resize_keyboard=True)


# ================= START =================

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 ESTA Недвижимость\n\nВыбери действие:",
        reply_markup=main_menu()
    )


# ================= LEAD =================

async def capture_phone(update, ctx):
    text = update.message.text

    if text.startswith("+") or text.isdigit():

        await ctx.bot.send_message(
            MANAGER_ID,
            f"🔥 ГОРЯЧИЙ ЛИД\nТелефон: {text}"
        )

        await update.message.reply_text("✅ Спасибо! Мы скоро свяжемся")

        return True

    return False


# ================= HANDLE =================

async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # ===== СБОР ТЕЛЕФОНА =====
    if await capture_phone(update, ctx):
        return

    # ===== ДОБАВЛЕНИЕ =====
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
            s["price"] = text

            create_property({
                "title": s["title"],
                "price": s["price"],
                "deal_type": "sale"
            })

            await update.message.reply_text(
                "✅ Объявление добавлено",
                reply_markup=main_menu()
            )

            user_state.pop(user_id)
            return

    # ===== ПОИСК =====
    if text == "🔍 Поиск" or "квартира" in text.lower():

        data = search_property()

        if not data:
            await update.message.reply_text("❌ Ничего не найдено")
            return

        for p in data[:5]:
            msg = f"""
🏠 {p.get('title')}
📍 {p.get('city','')}
💰 ${p.get('price')}
"""

            await update.message.reply_text(msg)

        await update.message.reply_text(
            "Хочешь больше вариантов или связаться? Напиши 👇"
        )
        return

    # ===== VIP =====
    if text == "💰 VIP":
        await update.message.reply_text(
            "🚀 Поднять объявление в топ\n\nНапиши: VIP"
        )
        return

    # ===== AI =====
    reply = await ai_funnel(text)
    await update.message.reply_text(reply)


# ================= MAIN =================

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    print("🔥 ESTA BOT STARTED")
    app.run_polling()


if __name__ == "__main__":
    main()
