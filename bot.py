  #!/usr/bin/env python3

import os
import logging
import asyncpg
from telegram import *
from telegram.ext import *

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")
MANAGER_ID = int(os.environ.get("MANAGER_ID", "5705817827"))

(
    ADD_DEAL,
    ADD_TYPE,
    ADD_TITLE,
    ADD_PRICE,
    ADD_DESC,
    ADD_PHONE,
    ADD_PHOTO,
    ADD_CONFIRM
) = range(8)

# ---------- DB ----------

async def db():
    return await asyncpg.connect(DATABASE_URL)

async def save(data):
    conn = await db()
    try:
        await conn.execute("""
        INSERT INTO properties (title, price, phone, deal, type, description, photos)
        VALUES ($1,$2,$3,$4,$5,$6,$7)
        """,
        data["title"], data["price"], data["phone"],
        data["deal"], data["type"], data["desc"], data["photos"])
    finally:
        await conn.close()

# ---------- UI ----------

def main_menu():
    return ReplyKeyboardMarkup([
        ["➕ Подать объявление"]
    ], resize_keyboard=True)

def deal_kb():
    return ReplyKeyboardMarkup([
        ["🏠 Купля", "🏠 Продажа"],
        ["🔑 Аренда", "🏦 Ипотека"],
        ["❌ Отмена"]
    ], resize_keyboard=True)

def type_kb():
    return ReplyKeyboardMarkup([
        ["🏢 Квартира", "🏡 Дом"],
        ["🌱 Участок", "🏪 Коммерция"],
        ["❌ Отмена"]
    ], resize_keyboard=True)

# ---------- START ----------

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 ESTA PRO", reply_markup=main_menu())

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("❌ Отменено", reply_markup=main_menu())
    return ConversationHandler.END

# ---------- FLOW ----------

async def add_start(update: Update, ctx):
    ctx.user_data["new"] = {"photos": []}
    await update.message.reply_text("Тип сделки:", reply_markup=deal_kb())
    return ADD_DEAL

async def add_deal(update: Update, ctx):
    ctx.user_data["new"]["deal"] = update.message.text
    await update.message.reply_text("Тип недвижимости:", reply_markup=type_kb())
    return ADD_TYPE

async def add_type(update: Update, ctx):
    ctx.user_data["new"]["type"] = update.message.text
    await update.message.reply_text("Заголовок:", reply_markup=ReplyKeyboardRemove())
    return ADD_TITLE

async def add_title(update: Update, ctx):
    ctx.user_data["new"]["title"] = update.message.text
    await update.message.reply_text("Цена:")
    return ADD_PRICE

async def add_price(update: Update, ctx):
    ctx.user_data["new"]["price"] = update.message.text
    await update.message.reply_text("Описание:")
    return ADD_DESC

async def add_desc(update: Update, ctx):
    ctx.user_data["new"]["desc"] = update.message.text
    await update.message.reply_text("Телефон:")
    return ADD_PHONE

async def add_phone(update: Update, ctx):
    ctx.user_data["new"]["phone"] = update.message.text
    await update.message.reply_text("Отправь фото (или напиши 'готово')")
    return ADD_PHOTO

async def add_photo(update: Update, ctx):
    if update.message.photo:
        file = await update.message.photo[-1].get_file()
        ctx.user_data["new"]["photos"].append(file.file_path)
        await update.message.reply_text("📸 Фото добавлено")
        return ADD_PHOTO

    if "готово" in (update.message.text or "").lower():
        data = ctx.user_data["new"]

        text = f"""
📢 НОВОЕ ОБЪЯВЛЕНИЕ

🏠 {data['title']}
💰 {data['price']}
📞 {data['phone']}
"""

        # отправка менеджеру
        await ctx.bot.send_message(MANAGER_ID, text)

        # сохранение в БД
        await save(data)

        await update.message.reply_text("✅ Опубликовано", reply_markup=main_menu())
        ctx.user_data.clear()
        return ConversationHandler.END

    return ADD_PHOTO

# ---------- MAIN ----------

def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("➕ Подать объявление"), add_start)],
        states={
            ADD_DEAL: [MessageHandler(filters.TEXT, add_deal)],
            ADD_TYPE: [MessageHandler(filters.TEXT, add_type)],
            ADD_TITLE: [MessageHandler(filters.TEXT, add_title)],
            ADD_PRICE: [MessageHandler(filters.TEXT, add_price)],
            ADD_DESC: [MessageHandler(filters.TEXT, add_desc)],
            ADD_PHONE: [MessageHandler(filters.TEXT, add_phone)],
            ADD_PHOTO: [MessageHandler(filters.ALL, add_photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)

    print("PRO BOT STARTED")
    app.run_polling()

if __name__ == "__main__":
    main()              
