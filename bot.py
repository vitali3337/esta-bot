#!/usr/bin/env python3

import os
import logging
import asyncpg
from telegram import *
from telegram.ext import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
DATABASE_URL = os.environ.get("DATABASE_URL")

ADD_DEAL = 0

# ================= DB =================

async def db():
    return await asyncpg.connect(DATABASE_URL)

# ================= KEYBOARDS =================

def main_menu():
    return ReplyKeyboardMarkup([
        ["🔍 Найти объект", "➕ Подать объявление"],
    ], resize_keyboard=True)

def deal_kb():
    return ReplyKeyboardMarkup([
        ["🏠 Продажа", "🔑 Аренда/мес"],
        ["❌ Отмена"]
    ], resize_keyboard=True)

# ================= COMMANDS =================

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Добро пожаловать в ESTA",
        reply_markup=main_menu()
    )

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("❌ Отменено", reply_markup=main_menu())
    return ConversationHandler.END

# ================= DELETE =================

async def cb_delete(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    prop_id = q.data.replace("del_", "")

    conn = await db()
    try:
        await conn.execute(
            "UPDATE properties SET is_active=FALSE WHERE id=$1::uuid",
            prop_id
        )
    finally:
        await conn.close()

    await q.edit_message_text("✅ Удалено")

# ================= ADD FLOW =================

async def add_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    ctx.user_data["new"] = {}

    await update.message.reply_text(
        "➕ Подача объявления\n\nТип сделки:",
        reply_markup=deal_kb()
    )
    return ADD_DEAL

async def add_deal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["deal"] = update.message.text

    await update.message.reply_text("Введите заголовок:")
    return ConversationHandler.END

# ================= SEARCH =================

async def search_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Поиск пока в разработке")
    return ConversationHandler.END

# ================= MAIN =================

def main():
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("➕ Подать объявление"), add_start)],
        states={
            ADD_DEAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_deal)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.Regex("🔍 Найти объект"), search_start))
    app.add_handler(CallbackQueryHandler(cb_delete, pattern="^del_"))

    print("BOT STARTED")
    app.run_polling()

if __name__ == "__main__":
    main()
