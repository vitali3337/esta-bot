import os
import time
import logging
import requests

from telegram import (
    ReplyKeyboardMarkup, Update,
    InlineKeyboardButton, InlineKeyboardMarkup,
    InputMediaPhoto
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters, CallbackQueryHandler
)

from ai_core import AICore

# ========= CONFIG =========
TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MANAGER_ID = int(os.getenv("MANAGER_ID", "5705817827"))

logging.basicConfig(level=logging.INFO)

# ========= AI =========
ai = AICore(API_URL, OPENAI_API_KEY)

# ========= STATE =========
user_state = {}  # для "Продать" и для шага "phone"

# ========= UI =========
def main_menu():
    return ReplyKeyboardMarkup([
        ["🏠 Купить", "🔑 Аренда"],
        ["➕ Продать", "🏦 Ипотека"],
        ["📞 Связаться"]
    ], resize_keyboard=True)

def build_card(p: dict) -> str:
    return f"""
🏠 {p.get('title')}
📍 {p.get('city', '—')} | {p.get('deal_type','—')} | {p.get('rooms','')}к

💰 ${p.get('price')} | {p.get('area','')} м²
👁 {p.get('views', 0)} просмотров

🆔 ID: #{p.get('id')}
"""

def card_buttons(p: dict):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⭐ Сделать VIP", callback_data=f"vip_{p.get('id')}"),
            InlineKeyboardButton("👀 Посмотреть", url=f"{API_URL}/property/{p.get('id')}")
        ]
    ])

async def send_property(update: Update, ctx: ContextTypes.DEFAULT_TYPE, p: dict):
    photos = p.get("photos") or []

    # фото (если есть)
    if photos:
        media = [InputMediaPhoto(url) for url in photos[:3]]
        await ctx.bot.send_media_group(
            chat_id=update.effective_chat.id,
            media=media
        )

    # карточка + кнопки
    await update.message.reply_text(
        build_card(p),
        reply_markup=card_buttons(p)
    )

# ========= HELPERS =========
def is_phone(text: str) -> bool:
    text = text.strip()
    return text.startswith("+") or (text.isdigit() and len(text) >= 7)

def send_lead(phone: str):
    try:
        requests.post(f"{API_URL}/lead", json={"phone": phone}, timeout=5)
    except Exception:
        pass

def create_property(data: dict):
    try:
        return requests.post(f"{API_URL}/property", json=data, timeout=5).json()
    except Exception:
        return {}

# ========= HANDLERS =========
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏠 ESTA Недвижимость\n\nЧто ищешь?",
        reply_markup=main_menu()
    )

async def handle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    data = q.data or ""
    if data.startswith("vip_"):
        await q.message.reply_text("🚀 VIP подключим (пока заглушка)")

async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        text = (update.message.text or "").strip()

        # ===== ШАГ: ожидаем телефон =====
        if user_state.get(user_id, {}).get("step") == "phone":
            if is_phone(text):
                await ctx.bot.send_message(
                    MANAGER_ID,
                    f"🔥 ГОРЯЧИЙ ЛИД\nТелефон: {text}"
                )
                send_lead(text)
                await update.message.reply_text("✅ Спасибо! Мы скоро свяжемся.")
                user_state.pop(user_id, None)
                return
            else:
                await update.message.reply_text("📞 Введи корректный номер (например: +373XXXXXXXX)")
                return

        # ===== КНОПКИ =====
        if text == "🏠 Купить":
            await update.message.reply_text("Напиши запрос: город, тип, бюджет 👇")
            return

        if text == "🔑 Аренда":
            await update.message.reply_text("Напиши: город и бюджет для аренды 👇")
            return

        if text == "🏦 Ипотека":
            await update.message.reply_text("💰 Напиши доход и бюджет — подберу варианты")
            return

        if text == "📞 Связаться":
            await update.message.reply_text("Оставь номер телефона 👇")
            user_state[user_id] = {"step": "phone"}
            return

        # ===== ПРОДАТЬ (форма) =====
        if text == "➕ Продать":
            user_state[user_id] = {"step": "title"}
            await update.message.reply_text("✏️ Введите заголовок:")
            return

        if user_id in user_state:
            s = user_state[user_id]

            if s.get("step") == "title":
                s["title"] = text
                s["step"] = "price"
                await update.message.reply_text("💰 Введите цену (только цифры):")
                return

            if s.get("step") == "price":
                if not text.replace(" ", "").isdigit():
                    await update.message.reply_text("⚠️ Введите цену цифрами")
                    return

                price = int(text.replace(" ", ""))
                create_property({
                    "title": s["title"],
                    "price": price,
                    "deal_type": "sale"
                })

                await update.message.reply_text("✅ Объявление добавлено", reply_markup=main_menu())
                user_state.pop(user_id, None)
                return

        # ===== AI-ПОДБОР (ключевая часть) =====
        # триггер: свободный текст
        props, reply = await ai.run(text)

        if props:
            for p in props:
                await send_property(update, ctx, p)

            # дожим к номеру
            await update.message.reply_text(
                f"{reply}\n\nХочешь — подберу ещё лучше. Оставь номер 👇"
            )
            user_state[user_id] = {"step": "phone"}
            return
        else:
            # ничего не найдено — просто ответ AI
            await update.message.reply_text(reply)
            return

    except Exception as e:
        print("BOT ERROR:", e)
        await update.message.reply_text("⚠️ Ошибка, попробуй ещё раз")

# ========= MAIN =========
def main():
    # фикс конфликтов Telegram
    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook", timeout=5)
        time.sleep(1)
    except Exception:
        pass

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    print("🔥 ESTA AI BOT STARTED")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
