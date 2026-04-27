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

async def ai_agent(user_text):
    response = client.responses.create(
        model="gpt-5.5",
        reasoning={"effort": "medium"},
        text={"verbosity": "low"},
        input=[
            {
                "role": "system",
                "content": """
Ты топовый агент по недвижимости (Молдова/ПМР).

Цель:
— понять что хочет клиент
— предложить варианты
— довести до контакта

Правила:
— коротко
— конкретно
— задавай 1 вопрос
— предлагай варианты
— веди к звонку

Если клиент не дал параметры:
→ уточни (город, бюджет, тип)

Если дал:
→ предложи варианты + спроси "показать ещё или оставить заявку?"
"""
            },
            {"role": "user", "content": user_text}
        ]
    )

    return response.output_text


# ================= API =================

def search_property(params={}):
    try:
        return requests.get(f"{API_URL}/properties", params=params).json()
    except:
        return []

def create_property(data):
    try:
        return requests.post(f"{API_URL}/property", json=data).json()
    except:
        return {}

def send_lead(phone):
    try:
        requests.post(f"{API_URL}/lead", json={"phone": phone})
    except:
        pass


# ================= UI =================

def main_menu():
    return ReplyKeyboardMarkup([
        ["🏠 Купить", "💰 Продать"],
        ["🔑 Аренда", "🏦 Ипотека"],
        ["📞 Связаться"]
    ], resize_keyboard=True)


# ================= START =================

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 ESTA Недвижимость\n\nВыбери действие:",
        reply_markup=main_menu()
    )


# ================= PHONE =================

def is_phone(text):
    return text.startswith("+") or (text.isdigit() and len(text) >= 7)


async def capture_phone(update, ctx):
    text = update.message.text

    if is_phone(text):
        await ctx.bot.send_message(
            MANAGER_ID,
            f"🔥 ГОРЯЧИЙ ЛИД\nТелефон: {text}"
        )

        send_lead(text)

        await update.message.reply_text("✅ Мы скоро свяжемся")
        return True

    return False


# ================= HANDLE =================

async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    # ===== PHONE =====
    if await capture_phone(update, ctx):
        return

    # ===== ПРОДАТЬ =====
    if text == "💰 Продать":
        user_state[user_id] = {"step": "title"}
        await update.message.reply_text("✏️ Введите заголовок:")
        return

    if user_id in user_state:
        s = user_state[user_id]

        if s["step"] == "title":
            s["title"] = text
            s["step"] = "price"
            await update.message.reply_text("💰 Введите цену (только цифры):")
            return

        if s["step"] == "price":
            if not text.isdigit():
                await update.message.reply_text("⚠️ Введите цену цифрами")
                return

            s["price"] = int(text)

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

    # ===== ПОКУПКА =====
    if text in ["🏠 Купить", "🔑 Аренда"]:
        await update.message.reply_text(
            "Напиши что ищешь (например: 2к квартира Тирасполь до 50000)"
        )
        return

    # ===== ИПОТЕКА =====
    if text == "🏦 Ипотека":
        await update.message.reply_text(
            "💰 Напиши бюджет и доход — подберу ипотеку"
        )
        return

    # ===== ПОИСК =====
    if any(word in text.lower() for word in ["квартира", "дом", "купить", "аренда"]):
        data = search_property()

        if data:
            for p in data[:3]:
                msg = f"""
🏠 {p.get('title')}
📍 {p.get('city','')}
💰 ${p.get('price')}
"""
                await update.message.reply_text(msg)

        reply = await ai_agent(text)
        await update.message.reply_text(reply)
        return

    # ===== AI =====
    reply = await ai_agent(text)
    await update.message.reply_text(reply)


# ================= MAIN =================

def main():
    import requests
    import time

    # 💥 фикс конфликта
    requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook")
    time.sleep(1)

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    print("🔥 ESTA AI BOT STARTED")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
