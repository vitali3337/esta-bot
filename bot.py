import logging
import os
import requests

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
ApplicationBuilder,
CommandHandler,
MessageHandler,
ContextTypes,
filters,
ConversationHandler,
)

TOKEN = os.getenv("BOT_TOKEN")
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = "appIQflEcagGQpjXQ"
TABLE = "Listings"

logging.basicConfig(level=logging.INFO)

--- Состояния ---

DEAL, PROPERTY, PRICE, CITY, ROOMS, CONFIRM = range(6)

--- Кнопки ---

def main_menu():
return ReplyKeyboardMarkup(
[
["🔍 Поиск", "➕ Добавить"],
["📄 Мои объявления"],
],
resize_keyboard=True,
)

def deal_kb():
return ReplyKeyboardMarkup(
[["🏠 Продажа", "🔑 Аренда"]],
resize_keyboard=True,
)

def property_kb():
return ReplyKeyboardMarkup(
[["🏢 Квартира", "🏡 Дом"], ["🏗 Новостройка", "🏬 Коммерция"]],
resize_keyboard=True,
)

--- START ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
name = update.effective_user.first_name

await update.message.reply_text(
    f"👋 Привет, {name}!\n"
    f"🏠 ESTA недвижимость\n\n"
    f"Выбери действие 👇",
    reply_markup=main_menu(),
)

--- ДОБАВЛЕНИЕ ---

async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
context.user_data.clear()

await update.message.reply_text(
    "📌 Тип сделки:",
    reply_markup=deal_kb(),
)
return DEAL

async def set_deal(update: Update, context: ContextTypes.DEFAULT_TYPE):
context.user_data["deal"] = update.message.text

await update.message.reply_text(
    "🏠 Тип недвижимости:",
    reply_markup=property_kb(),
)
return PROPERTY

async def set_property(update: Update, context: ContextTypes.DEFAULT_TYPE):
context.user_data["property"] = update.message.text

await update.message.reply_text("💰 Цена:")
return PRICE

async def set_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
context.user_data["price"] = update.message.text

await update.message.reply_text("📍 Город:")
return CITY

async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
context.user_data["city"] = update.message.text

await update.message.reply_text("🛏 Кол-во комнат:")
return ROOMS

async def set_rooms(update: Update, context: ContextTypes.DEFAULT_TYPE):
context.user_data["rooms"] = update.message.text
data = context.user_data

text = (
    f"📋 Проверь данные:\n\n"
    f"{data['deal']}\n"
    f"{data['property']}\n"
    f"💰 {data['price']}\n"
    f"📍 {data['city']}\n"
    f"🛏 {data['rooms']}\n\n"
    f"Подтвердить?"
)

await update.message.reply_text(
    text,
    reply_markup=ReplyKeyboardMarkup([["✅ Да", "❌ Нет"]], resize_keyboard=True),
)
return CONFIRM

--- СОХРАНЕНИЕ ---

def save_to_airtable(data):
url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE}"

headers = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json",
}

payload = {
    "fields": {
        "Listing Title": f"{data['property']} {data['city']}",
        "Price": int(data["price"]),
        "City": data["city"],
        "Rooms": int(data["rooms"]),
        "Deal Type": data["deal"],
        "Property Type": data["property"],
    }
}

requests.post(url, json=payload, headers=headers)

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
if update.message.text == "✅ Да":
save_to_airtable(context.user_data)

    await update.message.reply_text(
        "✅ Объявление добавлено!",
        reply_markup=main_menu(),
    )
else:
    await update.message.reply_text(
        "❌ Отменено",
        reply_markup=main_menu(),
    )

return ConversationHandler.END

--- ОТМЕНА ---

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.message.reply_text("❌ Отмена", reply_markup=main_menu())
return ConversationHandler.END

--- MAIN ---

def main():
app = ApplicationBuilder().token(TOKEN).build()

conv = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("➕ Добавить"), add_start)],
    states={
        DEAL: [MessageHandler(filters.TEXT, set_deal)],
        PROPERTY: [MessageHandler(filters.TEXT, set_property)],
        PRICE: [MessageHandler(filters.TEXT, set_price)],
        CITY: [MessageHandler(filters.TEXT, set_city)],
        ROOMS: [MessageHandler(filters.TEXT, set_rooms)],
        CONFIRM: [MessageHandler(filters.TEXT, confirm)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

app.add_handler(CommandHandler("start", start))
app.add_handler(conv)

app.run_polling()

if name == "main":
main()
