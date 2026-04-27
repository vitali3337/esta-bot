import os
import logging
import requests
from telegram import *
from telegram.ext import *
from openai import OpenAI

TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MANAGER_ID = int(os.getenv("MANAGER_ID", "5705817827"))

client = OpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(level=logging.INFO)

user_state = {}
memory = {}

# ========= AI =========

async def ai_agent(user_id, text):
    history = memory.get(user_id, [])

    messages = [
        {
            "role": "system",
            "content": """
Ты топовый риелтор.

Цель:
— понять клиента
— предложить варианты
— довести до звонка

Не пиши "напиши подробнее"
Задавай конкретные вопросы
"""
        }
    ] + history + [{"role": "user", "content": text}]

    res = client.chat.completions.create(
        model="gpt-5",
        messages=messages
    )

    reply = res.choices[0].message.content

    memory[user_id] = history + [
        {"role": "user", "content": text},
        {"role": "assistant", "content": reply}
    ]

    return reply

# ========= API =========

def get_properties():
    try:
        return requests.get(f"{API_URL}/properties", timeout=5).json()
    except:
        return []

# ========= UI =========

def menu():
    return ReplyKeyboardMarkup([
        ["🏠 Купить", "🔑 Аренда"],
        ["➕ Продать", "🏦 Ипотека"]
    ], resize_keyboard=True)

# ========= START =========

async def start(update: Update, ctx):
    await update.message.reply_text(
        "🏠 ESTA Недвижимость\n\nЧто хочешь сделать?",
        reply_markup=menu()
    )

# ========= HANDLE =========

async def handle(update: Update, ctx):
    user_id = update.effective_user.id
    text = update.message.text

    # ===== КНОПКИ =====
    if text == "🏠 Купить":
        await update.message.reply_text("Напиши город и бюджет 👇")
        return

    if text == "🔑 Аренда":
        await update.message.reply_text("Ищешь аренду? Напиши район и цену 👇")
        return

    if text == "➕ Продать":
        user_state[user_id] = {"step": "title"}
        await update.message.reply_text("Введите название объекта:")
        return

    if text == "🏦 Ипотека":
        await update.message.reply_text(
            "💰 Помогу рассчитать ипотеку\n\nНапиши доход и бюджет"
        )
        return

    # ===== ДОБАВЛЕНИЕ =====
    if user_id in user_state:
        s = user_state[user_id]

        if s["step"] == "title":
            s["title"] = text
            s["step"] = "price"
            await update.message.reply_text("Введите цену:")
            return

        if s["step"] == "price":
            s["price"] = text

            requests.post(f"{API_URL}/property", json=s, timeout=5)

            await update.message.reply_text("✅ Добавлено", reply_markup=menu())
            user_state.pop(user_id)
            return

    # ===== ПОИСК =====
    data = get_properties()

    if data:
        for p in data[:3]:
            if p.get("photo"):
                await update.message.reply_photo(
                    photo=p["photo"],
                    caption=f"{p['title']}\n💰 {p['price']}$"
                )
            else:
                await update.message.reply_text(
                    f"{p['title']}\n💰 {p['price']}$"
                )

    # ===== AI =====
    reply = await ai_agent(user_id, text)
    await update.message.reply_text(reply)

# ========= MAIN =========

def main():
    import requests
    requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    print("🔥 AI REAL ESTATE BOT STARTED")
    app.run_polling()

if __name__ == "__main__":
    main()
