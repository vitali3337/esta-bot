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

user_state = {}

# ================= AI =================

async def ai_funnel(text):
    try:
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": "Ты брокер. Доведи клиента до заявки."},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print("AI ERROR:", e)
        return "Напиши подробнее, что ищешь 👇"

# ================= API =================

def create_property(data):
    try:
        return requests.post(f"{API_URL}/property", json=data, timeout=5).json()
    except Exception as e:
        print("CREATE ERROR:", e)
        return {"error": True}

def search_property():
    try:
        return requests.get(f"{API_URL}/properties", timeout=5).json()
    except Exception as e:
        print("SEARCH ERROR:", e)
        return []

def send_lead(data):
    try:
        return requests.post(f"{API_URL}/lead", json=data, timeout=5)
    except Exception as e:
        print("LEAD ERROR:", e)

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

        send_lead({"phone": text})

        await update.message.reply_text("✅ Мы скоро свяжемся")
        return True

    return False

# ================= HANDLE =================

async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        text = update.message.text

        print("USER:", text)

        # ===== ЛИД =====
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

        # ===== ПОИСК =====
        if text == "🔍 Поиск" or ("квартира" in text.lower()):
            data = search_property()

            if not data:
                await update.message.reply_text("❌ Ничего не найдено")
                return

            for p in data[:5]:
                await update.message.reply_text(
                    f"🏠 {p.get('title')}\n📍 {p.get('city','')}\n💰 ${p.get('price')}"
                )

            await update.message.reply_text(
                "Хочешь больше вариантов или подобрать под тебя?"
            )
            return

        # ===== VIP =====
        if text == "💰 VIP":
            await update.message.reply_text(
                "🚀 VIP = топ выдача\nНапиши: VIP"
            )
            return

        # ===== AI =====
        reply = await ai_funnel(text)
        await update.message.reply_text(reply)

    except Exception as e:
        print("BOT ERROR:", e)
        await update.message.reply_text("⚠️ Ошибка, попробуй ещё раз")

# ================= MAIN =================

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    print("🔥 ESTA BOT STARTED")
    app.run_polling()

if __name__ == "__main__":
    main()
