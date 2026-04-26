import os
import aiohttp
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = "https://propai-md.vercel.app/api/properties"

TYPE, CATEGORY, PRICE, LOCATION, DESCRIPTION, PHOTOS = range(6)

def main_menu():
    return ReplyKeyboardMarkup(
        [["🔍 Поиск", "➕ Добавить"], ["📂 Мои объявления"]],
        resize_keyboard=True,
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏡 ESTA Realty Bot\n\nВыберите действие:",
        reply_markup=main_menu(),
    )

async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Тип сделки:",
        reply_markup=ReplyKeyboardMarkup(
            [["🏠 Продажа", "🔑 Аренда"]],
            resize_keyboard=True,
        ),
    )
    return TYPE

async def set_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["type"] = update.message.text
    await update.message.reply_text(
        "Тип недвижимости:",
        reply_markup=ReplyKeyboardMarkup(
            [["🏢 Квартира", "🏡 Дом", "🏗 Участок"]],
            resize_keyboard=True,
        ),
    )
    return CATEGORY

async def set_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["category"] = update.message.text
    await update.message.reply_text("💰 Введите цену:")
    return PRICE

async def set_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["price"] = update.message.text
    await update.message.reply_text("📍 Локация:")
    return LOCATION

async def set_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["location"] = update.message.text
    await update.message.reply_text("📝 Описание:")
    return DESCRIPTION

async def set_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    context.user_data["photos"] = []
    await update.message.reply_text(
        "📸 Отправьте фото (можно несколько).\nКогда закончите — напишите: ГОТОВО"
    )
    return PHOTOS

async def handle_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text and update.message.text.lower() == "готово":
        await save_property(update, context)
        return ConversationHandler.END

    if update.message.photo:
        file = update.message.photo[-1]
        context.user_data["photos"].append(file.file_id)
        await update.message.reply_text("✅ Фото добавлено")

    return PHOTOS

async def save_property(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data

    payload = {
        "type": data.get("type"),
        "category": data.get("category"),
        "price": data.get("price"),
        "location": data.get("location"),
        "description": data.get("description"),
        "photos": data.get("photos"),
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(API_URL, json=payload) as resp:
                if resp.status == 200:
                    await update.message.reply_text(
                        "🔥 Объявление добавлено!",
                        reply_markup=main_menu(),
                    )
                else:
                    await update.message.reply_text("❌ Ошибка API")
        except Exception as e:
            await update.message.reply_text(f"Ошибка: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("➕ Добавить"), add_start)],
        states={
            TYPE: [MessageHandler(filters.TEXT, set_type)],
            CATEGORY: [MessageHandler(filters.TEXT, set_category)],
            PRICE: [MessageHandler(filters.TEXT, set_price)],
            LOCATION: [MessageHandler(filters.TEXT, set_location)],
            DESCRIPTION: [MessageHandler(filters.TEXT, set_description)],
            PHOTOS: [MessageHandler(filters.ALL, handle_photos)],
        },
        fallbacks=[],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)

    print("🚀 BOT STARTED")
    app.run_polling()

if __name__ == "__main__":
    main()
