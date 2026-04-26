import logging
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = "ТВОЙ_ТОКЕН"
API_URL = "https://your-backend.up.railway.app/properties"

logging.basicConfig(level=logging.INFO)

# ====== МЕНЮ ======
def menu():
    return ReplyKeyboardMarkup(
        [
            ["🔍 Поиск объектов", "➕ Подать объявление"],
            ["📂 Мои объявления"]
        ],
        resize_keyboard=True
    )

# ====== START ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Добро пожаловать в ESTA Realty\n\n🏠 AI-платформа недвижимости",
        reply_markup=menu()
    )

# ====== СТАРТ ДОБАВЛЕНИЯ ======
async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["step"] = "type"
    context.user_data["data"] = {}
    context.user_data["photos"] = []

    await update.message.reply_text("Тип сделки:\nПродажа или Аренда?")

# ====== ОБРАБОТКА СООБЩЕНИЙ ======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "➕ Подать объявление":
        await add_start(update, context)
        return

    step = context.user_data.get("step")

    if step == "type":
        context.user_data["data"]["type"] = text
        context.user_data["step"] = "category"
        await update.message.reply_text("Тип недвижимости:")
    
    elif step == "category":
        context.user_data["data"]["category"] = text
        context.user_data["step"] = "price"
        await update.message.reply_text("Цена:")
    
    elif step == "price":
        context.user_data["data"]["price"] = text
        context.user_data["step"] = "location"
        await update.message.reply_text("Локация:")
    
    elif step == "location":
        context.user_data["data"]["location"] = text
        context.user_data["step"] = "description"
        await update.message.reply_text("Описание:")
    
    elif step == "description":
        context.user_data["data"]["description"] = text
        context.user_data["step"] = "photos"
        await update.message.reply_text("📸 Отправь фото (можно несколько), потом напиши ГОТОВО")

    elif step == "photos":
        if text.lower() == "готово":
            await send_to_api(update, context)
            context.user_data.clear()
        else:
            await update.message.reply_text("Отправь фото или напиши ГОТОВО")

# ====== ФОТО ======
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("step") != "photos":
        return

    photo = update.message.photo[-1]
    file = await photo.get_file()

    context.user_data["photos"].append(file.file_path)

    await update.message.reply_text("✅ Фото добавлено")

# ====== ОТПРАВКА В API ======
async def send_to_api(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data["data"]
    data["photos"] = context.user_data["photos"]

    try:
        r = requests.post(API_URL, json=data)

        if r.status_code == 200:
            await update.message.reply_text("✅ Объявление добавлено")
        else:
            await update.message.reply_text(f"❌ Ошибка API: {r.text}")

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

# ====== MAIN ======
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
