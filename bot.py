#!/usr/bin/env python3

import os
import logging
from telegram import *
from telegram.ext import *

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("BOT_TOKEN")

(
    ADD_DEAL,
    ADD_TYPE,
    ADD_LOC,
    ADD_TITLE,
    ADD_ROOMS,
    ADD_AREA,
    ADD_PRICE,
    ADD_DESC,
    ADD_PHONE,
) = range(9)

# ---------- КЛАВИАТУРЫ ----------

def main_menu():
    return ReplyKeyboardMarkup([
        ["➕ Подать объявление"]
    ], resize_keyboard=True)

def deal_kb():
    return ReplyKeyboardMarkup([
        ["🏠 Продажа", "🔑 Аренда"],
        ["❌ Отмена"]
    ], resize_keyboard=True)

def type_kb():
    return ReplyKeyboardMarkup([
        ["🏢 Квартира", "🏡 Дом"],
        ["🌱 Участок", "🏪 Коммерция"],
        ["❌ Отмена"]
    ], resize_keyboard=True)

# ---------- СТАРТ ----------

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Добро пожаловать", reply_markup=main_menu())

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("❌ Отменено", reply_markup=main_menu())
    return ConversationHandler.END

# ---------- ФЛОУ ----------

async def add_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    ctx.user_data["new"] = {}

    await update.message.reply_text("Тип сделки:", reply_markup=deal_kb())
    return ADD_DEAL


async def add_deal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["deal"] = update.message.text

    await update.message.reply_text("Тип недвижимости:", reply_markup=type_kb())
    return ADD_TYPE


async def add_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["type"] = update.message.text

    await update.message.reply_text("Город:")
    return ADD_LOC


async def add_loc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["location"] = update.message.text

    await update.message.reply_text("Заголовок:")
    return ADD_TITLE


async def add_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["title"] = update.message.text

    await update.message.reply_text("Количество комнат:")
    return ADD_ROOMS


async def add_rooms(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["rooms"] = update.message.text

    await update.message.reply_text("Площадь м²:")
    return ADD_AREA


async def add_area(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["area"] = update.message.text

    await update.message.reply_text("Цена $:")
    return ADD_PRICE


async def add_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["price"] = update.message.text

    await update.message.reply_text("Описание:")
    return ADD_DESC


async def add_desc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["desc"] = update.message.text

    await update.message.reply_text("Телефон:")
    return ADD_PHONE


async def add_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["phone"] = update.message.text

    data = ctx.user_data["new"]

    text = (
        f"✅ Объявление принято\n\n"
        f"🏠 {data['title']}\n"
        f"📍 {data['location']}\n"
        f"💰 {data['price']}$\n"
        f"📞 {data['phone']}"
    )

    await update.message.reply_text(text, reply_markup=main_menu())

    ctx.user_data.clear()
    return ConversationHandler.END

# ---------- MAIN ----------

def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("➕ Подать объявление"), add_start)],
        states={
            ADD_DEAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_deal)],
            ADD_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_type)],
            ADD_LOC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_loc)],
            ADD_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_title)],
            ADD_ROOMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_rooms)],
            ADD_AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_area)],
            ADD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_price)],
            ADD_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_desc)],
            ADD_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)

    print("BOT STARTED")
    app.run_polling()

if __name__ == "__main__":
    main()
