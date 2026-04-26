#!/usr/bin/env python3
"""
ESTA Недвижимость — Telegram Bot v3.1
@esta_realty_bot
"""

import os
import logging
import asyncpg
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")

CITY_MAP = {
    "Тирасполь": 3, "Бендеры": 4, "Рыбница": 5, "Дубоссары": 6,
    "Кишинёв": 1, "Кишинёв - Центр": 1, "Кишинёв - Ботаника": 1,
    "Кишинёв - Рышкань": 1, "Кишинёв - Чокана": 1,
    "Кишинёв - Буюкань": 1, "Кишинёв - Телецентр": 1, "Бельцы": 2,
}

PMR_LOCATIONS = [
    "Тирасполь", "Бендеры", "Рыбница", "Дубоссары", "Слободзея",
    "Днестровск", "Григориополь", "Суклея", "Парканы", "Красное",
    "Колосово", "Ближний Хутор", "Дальний Хутор", "Малаешты",
    "Кицканы", "Меренешты", "Владимировка", "Карагаш", "Ташлык",
    "Чобручи", "Незавертайловка", "Глиное", "Погребя", "Коротное",
]

MOLDOVA_LOCATIONS = [
    "Кишинёв", "Бельцы", "Унгены", "Сорока", "Оргеев", "Кагул",
    "Хынчешты", "Стрэшень", "Яловень", "Криулень", "Дрокия",
    "Флорешть", "Единец", "Бричень", "Окница", "Дондушень",
    "Глодень", "Фалешть", "Ниспорень", "Кэлэрашь", "Леова",
    "Чимишлия", "Басарабяска", "Тараклия", "Штефан Водэ", "Кэушень",
    "Анений Ной", "Комрат", "Чадыр-Лунга", "Вулкэнешть",
    "Кишинёв - Центр", "Кишинёв - Ботаника", "Кишинёв - Рышкань",
    "Кишинёв - Чокана", "Кишинёв - Буюкань", "Кишинёв - Телецентр",
    "Дурлешть", "Кодру", "Ватра", "Трушень",
]

def get_location_pages():
    all_locs = ["=== ПМР ==="] + PMR_LOCATIONS + ["=== МОЛДОВА ==="] + MOLDOVA_LOCATIONS
    pages = []
    for i in range(0, len(all_locs), 8):
        pages.append(all_locs[i:i+8])
    return pages

LOCATION_PAGES = get_location_pages()

(
    ADD_DEAL, ADD_CAT, ADD_LOC_PAGE, ADD_TITLE, ADD_ROOMS,
    ADD_AREA, ADD_FLOOR, ADD_PRICE, ADD_DESC, ADD_PHONE, ADD_PHOTO,
    SEARCH_LOC, SEARCH_DEAL, SEARCH_CAT, SEARCH_PRICE,
) = range(15)

async def db_save(data):
    db = await asyncpg.connect(DATABASE_URL)
    try:
        city_id = CITY_MAP.get(data.get("location"), 1)
        deal = data.get("deal", "sale")
        if deal not in ("sale", "rent"):
            deal = "sale"
        prop = data.get("category", "apartment")
        if prop not in ("apartment", "house", "commercial", "garage", "storage", "land"):
            prop = "apartment"
        price = float(data.get("price") or 0)
        rooms = data.get("rooms")
        area = data.get("area")
        if area:
            area = float(area)
        row = await db.fetchrow(
            """INSERT INTO properties
            (deal_type, property_type, city_id, title, description,
             rooms, area_total, price, currency, price_usd,
             contact_phone, source, is_active)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,'USD',$8,$9,'telegram',TRUE)
            RETURNING id""",
            deal, prop, city_id,
            data.get("title", "Без названия"),
            data.get("description", ""),
            rooms, area, price,
            data.get("phone", "")
        )
        return str(row["id"])
    finally:
        await db.close()

async def db_search(location=None, deal=None, category=None, max_price=None):
    db = await asyncpg.connect(DATABASE_URL)
    try:
        conds = ["is_active = TRUE"]
        params = []
        i = 1
        if location and location in CITY_MAP:
            conds.append(f"city_id = ${i}")
            params.append(CITY_MAP[location])
            i += 1
        if deal in ("sale", "rent"):
            conds.append(f"deal_type = ${i}")
            params.append(deal)
            i += 1
        if category in ("apartment", "house", "commercial", "garage", "land"):
            conds.append(f"property_type = ${i}")
            params.append(category)
            i += 1
        if max_price:
            conds.append(f"price_usd <= ${i}")
            params.append(float(max_price))
            i += 1
        rows = await db.fetch(
            f"SELECT * FROM properties WHERE {' AND '.join(conds)} ORDER BY is_featured DESC, created_at DESC LIMIT 5",
            *params
        )
        return [dict(r) for r in rows]
    finally:
        await db.close()

def deal_label(d):
    return {"sale": "Продажа", "rent": "Аренда"}.get(d, d)

def cat_label(c):
    return {"apartment": "Квартира", "house": "Дом", "land": "Участок",
            "commercial": "Коммерция", "garage": "Гараж"}.get(c, c)

def card(l):
    r = f"🛏 {l['rooms']}к | " if l.get("rooms") else ""
    a = f"📐 {l['area_total']} м² | " if l.get("area_total") else ""
    return (
        f"🏠 *{l['title']}*\n"
        f"🏷 {deal_label(l['deal_type'])} · {cat_label(l['property_type'])}\n"
        f"{r}{a}💵 *${float(l['price']):,.0f}*\n"
        f"📞 {l.get('contact_phone') or '—'}"
    )

def menu():
    return ReplyKeyboardMarkup(
        [["🔍 Поиск объектов", "➕ Подать объявление"],
         ["📋 Мои объявления", "ℹ️ О сервисе ESTA"]],
        resize_keyboard=True
    )

def loc_kb(page_idx):
    page = LOCATION_PAGES[page_idx]
    rows = [[loc] for loc in page]

    nav = []
    if page_idx > 0:
        nav.append("◀️ Пред.")
    if page_idx < len(LOCATION_PAGES) - 1:
        nav.append("▶️ След.")

    if nav:
        rows.append(nav)

    rows.append(["🌍 Все регионы"])

    return ReplyKeyboardMarkup(rows, resize_keyboard=True)
    async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"👋 Добро пожаловать в *ESTA Недвижимость*, {name}!\n\n"
        f"🏠 AI-портал недвижимости Молдовы и ПМР\n"
        f"🌐 esta-site.vercel.app",
        parse_mode="Markdown", reply_markup=menu()
    )

async def add_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    ctx.user_data["new"] = {}
    await update.message.reply_text(
        "➕ *Добавить объявление*\n\nТип сделки:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [["🏠 Продажа", "🔑 Аренда"]], resize_keyboard=True, one_time_keyboard=True
        )
    )
    return ADD_DEAL

async def add_deal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["deal"] = "rent" if "Аренда" in update.message.text else "sale"
    await update.message.reply_text(
        "Категория:",
        reply_markup=ReplyKeyboardMarkup(
            [["🏢 Квартира", "🏡 Дом"], ["🌱 Участок", "🏪 Коммерция"], ["🚗 Гараж"]],
            resize_keyboard=True, one_time_keyboard=True
        )
    )
    return ADD_CAT

async def add_cat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    if "Квартира" in t: ctx.user_data["new"]["category"] = "apartment"
    elif "Дом" in t: ctx.user_data["new"]["category"] = "house"
    elif "Участок" in t: ctx.user_data["new"]["category"] = "land"
    elif "Коммерция" in t: ctx.user_data["new"]["category"] = "commercial"
    elif "Гараж" in t: ctx.user_data["new"]["category"] = "garage"
    else: ctx.user_data["new"]["category"] = "apartment"
    ctx.user_data["loc_page"] = 0
    await update.message.reply_text("📍 Город:", reply_markup=loc_kb(0))
    return ADD_LOC_PAGE

async def add_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    p = ctx.user_data.get("loc_page", 0)
    if t == "▶️ След.":
        ctx.user_data["loc_page"] = min(p+1, len(LOCATION_PAGES)-1)
        await update.message.reply_text("📍 Город:", reply_markup=loc_kb(ctx.user_data["loc_page"]))
        return ADD_LOC_PAGE
    if t == "◀️ Пред.":
        ctx.user_data["loc_page"] = max(p-1, 0)
        await update.message.reply_text("📍 Город:", reply_markup=loc_kb(ctx.user_data["loc_page"]))
        return ADD_LOC_PAGE
    if t.startswith("===") or t == "🌍 Все регионы":
        await update.message.reply_text("Выбери конкретный город 👇", reply_markup=loc_kb(p))
        return ADD_LOC_PAGE
    ctx.user_data["new"]["location"] = t
    await update.message.reply_text("✏️ Заголовок объявления:", reply_markup=ReplyKeyboardRemove())
    return ADD_TITLE

async def add_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["title"] = update.message.text
    cat = ctx.user_data["new"].get("category")
    if cat in ("land", "commercial", "garage"):
        ctx.user_data["new"]["rooms"] = None
        await update.message.reply_text("📐 Площадь м²:")
        return ADD_AREA
    await update.message.reply_text(
        "🛏 Комнат:",
        reply_markup=ReplyKeyboardMarkup([["1","2","3"],["4","5","6+"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return ADD_ROOMS

async def add_rooms(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try: ctx.user_data["new"]["rooms"] = int(update.message.text.replace("+",""))
    except: ctx.user_data["new"]["rooms"] = 1
    await update.message.reply_text("📐 Площадь м²:", reply_markup=ReplyKeyboardRemove())
    return ADD_AREA

async def add_area(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try: ctx.user_data["new"]["area"] = float(update.message.text.replace(" ",""))
    except: ctx.user_data["new"]["area"] = None
    cat = ctx.user_data["new"].get("category")
    if cat in ("land", "commercial", "garage"):
        await update.message.reply_text("💵 Цена $:")
        return ADD_PRICE
    await update.message.reply_text("🏢 Этаж (например 3/9):")
    return ADD_FLOOR

async def add_floor(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["floor"] = update.message.text
    await update.message.reply_text("💵 Цена $:")
    return ADD_PRICE

async def add_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try: ctx.user_data["new"]["price"] = float(update.message.text.replace(" ","").replace(",",""))
    except: ctx.user_data["new"]["price"] = 0
    await update.message.reply_text("📝 Описание:")
    return ADD_DESC

async def add_desc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["description"] = update.message.text
    await update.message.reply_text("📞 Телефон:")
    return ADD_PHONE

async def add_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["phone"] = update.message.text
    await update.message.reply_text("📸 Фото (или напиши 'пропустить'):")
    return ADD_PHOTO

async def add_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    n = ctx.user_data.get("new", {})
    try:
        listing_id = await db_save(n)
        await update.message.reply_text(
            "✅ *Объявление сохранено в базе!*\n\n"
            f"🏠 {n.get('title')}\n"
            f"📍 {n.get('location')} | {deal_label(n.get('deal','sale'))}\n"
            f"💵 ${float(n.get('price') or 0):,.0f}\n\n"
            f"🌐 esta-site.vercel.app",
            parse_mode="Markdown", reply_markup=menu()
        )
    except Exception as e:
        logger.error(f"DB error: {e}")
        await update.message.reply_text(f"❌ Ошибка БД: {str(e)[:150]}", reply_markup=menu())
    return ConversationHandler.END

async def search_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    ctx.user_data["loc_page"] = 0
    await update.message.reply_text("🔍 Город:", reply_markup=loc_kb(0))
    return SEARCH_LOC

async def search_loc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    p = ctx.user_data.get("loc_page", 0)
    if t == "▶️ След.":
        ctx.user_data["loc_page"] = min(p+1, len(LOCATION_PAGES)-1)
        await update.message.reply_text("📍 Город:", reply_markup=loc_kb(ctx.user_data["loc_page"]))
        return SEARCH_LOC
    if t == "◀️ Пред.":
        ctx.user_data["loc_page"] = max(p-1, 0)
        await update.message.reply_text("📍 Город:", reply_markup=loc_kb(ctx.user_data["loc_page"]))
        return SEARCH_LOC
    if t.startswith("==="):
        await update.message.reply_text("Выбери город 👇", reply_markup=loc_kb(p))
        return SEARCH_LOC
    ctx.user_data["s_loc"] = None if t == "🌍 Все регионы" else t
    await update.message.reply_text(
        "Сделка:",
        reply_markup=ReplyKeyboardMarkup([["🏠 Продажа","🔑 Аренда"],["🔄 Все"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return SEARCH_DEAL

async def search_deal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    ctx.user_data["s_deal"] = "sale" if "Продажа" in t else "rent" if "Аренда" in t else None
    await update.message.reply_text(
        "Тип:",
        reply_markup=ReplyKeyboardMarkup([["🏢 Квартира","🏡 Дом"],["🌱 Участок","🏪 Коммерция"],["🔄 Все"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return SEARCH_CAT

async def search_cat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    if "Квартира" in t: ctx.user_data["s_cat"] = "apartment"
    elif "Дом" in t: ctx.user_data["s_cat"] = "house"
    elif "Участок" in t: ctx.user_data["s_cat"] = "land"
    elif "Коммерция" in t: ctx.user_data["s_cat"] = "commercial"
    else: ctx.user_data["s_cat"] = None
    await update.message.reply_text(
        "Макс. цена $:",
        reply_markup=ReplyKeyboardMarkup([["20000","35000","50000"],["80000","150000","🔄 Любая"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return SEARCH_PRICE

async def search_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    max_p = None if "Любая" in t else int(t.replace(" ","").replace(",",""))
    try:
        results = await db_search(
            location=ctx.user_data.get("s_loc"),
            deal=ctx.user_data.get("s_deal"),
            category=ctx.user_data.get("s_cat"),
            max_price=max_p
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        results = []
    await update.message.reply_text(
        f"✅ Найдено: *{len(results)}*" if results else "😔 Ничего не найдено.",
        parse_mode="Markdown", reply_markup=menu()
    )
    for l in results:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🌐 На сайте", url="https://esta-site.vercel.app")]])
        await update.message.reply_text(card(l), parse_mode="Markdown", reply_markup=kb)
    return ConversationHandler.END

async def my_listings(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        db = await asyncpg.connect(DATABASE_URL)
        rows = await db.fetch("SELECT * FROM properties WHERE source='telegram' AND is_active=TRUE ORDER BY created_at DESC LIMIT 5")
        await db.close()
        if not rows:
            await update.message.reply_text("Объявлений нет. Нажми ➕ Подать объявление", reply_markup=menu())
            return
        await update.message.reply_text(f"📋 {len(rows)} объявлений:", reply_markup=menu())
        for l in rows:
            await update.message.reply_text(card(dict(l)), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)[:100]}", reply_markup=menu())

async def about(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *ESTA Недвижимость*\n\nAI-портал Молдовы и ПМР\n🌐 esta-site.vercel.app",
        parse_mode="Markdown", reply_markup=menu()
    )

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("Отменено.", reply_markup=menu())
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()
    add_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("➕ Подать"), add_start)],
        states={
            ADD_DEAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_deal)],
            ADD_CAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_cat)],
            ADD_LOC_PAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_location)],
            ADD_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_title)],
            ADD_ROOMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_rooms)],
            ADD_AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_area)],
            ADD_FLOOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_floor)],
            ADD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_price)],
            ADD_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_desc)],
            ADD_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_phone)],
            ADD_PHOTO: [MessageHandler(filters.ALL, add_photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    search_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("🔍 Поиск"), search_start)],
        states={
            SEARCH_LOC: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_loc)],
            SEARCH_DEAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_deal)],
            SEARCH_CAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_cat)],
            SEARCH_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(add_conv)
    app.add_handler(search_conv)
    app.add_handler(MessageHandler(filters.Regex("📋 Мои"), my_listings))
    app.add_handler(MessageHandler(filters.Regex("ℹ️ О сервисе"), about))
    logger.info("ESTA Bot v3.1 запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
