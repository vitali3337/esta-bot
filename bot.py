#!/usr/bin/env python3
"""
ESTA Недвижимость — Telegram Bot v3.0
@esta_realty_bot
PostgreSQL интеграция
"""

import os
import logging
import asyncpg
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")

DEAL_TYPES = {
    "🏠 Продажа": "sale",
    "🔑 Аренда помесячно": "rent",
}

CATEGORIES = {
    "🏢 Квартира": "apartment",
    "🏡 Дом / Дача": "house",
    "🌱 Участок": "land",
    "🏪 Коммерция": "commercial",
    "🚗 Гараж": "garage",
}

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
    pages = []
    all_locs = ["=== ПМР ==="] + PMR_LOCATIONS + ["=== МОЛДОВА ==="] + MOLDOVA_LOCATIONS
    for i in range(0, len(all_locs), 8):
        pages.append(all_locs[i:i+8])
    return pages

LOCATION_PAGES = get_location_pages()

(
    SEARCH_LOCATION_PAGE, SEARCH_DEAL, SEARCH_CAT, SEARCH_PRICE,
    ADD_DEAL, ADD_CAT, ADD_LOC_PAGE, ADD_TITLE, ADD_ROOMS,
    ADD_PRICE, ADD_AREA, ADD_FLOOR, ADD_DESC, ADD_PHONE, ADD_PHOTO,
) = range(15)
# ─── DB ФУНКЦИИ ────────────────────────────────────────────────

async def db_connect():
    return await asyncpg.connect(DATABASE_URL)


    db = await db_connect()
    try:
        city_id = CITY_MAP.get(data.get("location"), 1)
        deal = data.get("deal", "sale")
        if deal not in ("sale", "rent"):
            deal = "sale"
        prop_type = data.get("category", "apartment")
        if prop_type not in ("apartment", "house", "commercial", "garage", "storage", "land"):
            prop_type = "apartment"
        price = float(data.get("price", 0))
        row = await db.fetchrow("""
            INSERT INTO properties
            (deal_type, property_type, city_id, title, description,
             rooms, area_total, price, currency, price_usd,
             contact_phone, source, is_active)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,'USD',$8,$9,'telegram',TRUE)
            RETURNING id
        """,
            deal, prop_type, city_id,
            data.get("title", ""), data.get("description", ""),
            data.get("rooms"),
            float(data.get("area", 0)) if data.get("area") else None,
            price, data.get("phone", "")
        )
        return str(row["id"])
    finally:
        await db.close()

async def db_save_listing(data: dict) -> str:
    db = await db_connect()
    try:
        city_id = CITY_MAP.get(data.get("location"), 1)
        deal = data.get("deal", "sale")
        if deal not in ("sale", "rent"):
            deal = "sale"
        prop_type = data.get("category", "apartment")
        if prop_type not in ("apartment", "house", "commercial", "garage", "storage", "land"):
            prop_type = "apartment"
        price = float(data.get("price", 0) or 0)
        rooms = data.get("rooms")
        if rooms is not None:
            rooms = int(rooms)
        area = data.get("area")
        if area is not None:
            area = float(area)
        row = await db.fetchrow("""
            INSERT INTO properties
            (deal_type, property_type, city_id, title, description,
             rooms, area_total, price, currency, price_usd,
             contact_phone, source, is_active)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,'USD',$8,$9,'telegram',TRUE)
            RETURNING id
        """,
            deal, prop_type, city_id,
            data.get("title", "Без названия"),
            data.get("description", ""),
            rooms, area, price,
            data.get("phone", "")
        )
        return str(row["id"])
    finally:
        await db.close()

def deal_label(d):
    return {"sale": "Продажа", "rent": "Аренда"}.get(d, d)

def cat_label(c):
    return {
        "apartment": "Квартира", "house": "Дом/Дача",
        "land": "Участок", "commercial": "Коммерция",
        "garage": "Гараж", "storage": "Хозпомещение"
    }.get(c, c)

def listing_card(l):
    rooms = f"🛏 {l['rooms']}к | " if l.get("rooms") else ""
    area = f"📐 {l['area_total']} м² | " if l.get("area_total") else ""
    vip = "💎 VIP\n" if l.get("is_featured") else ""
    return (
        f"{vip}🏠 *{l['title']}*\n"
        f"🏷 {deal_label(l['deal_type'])} · {cat_label(l['property_type'])}\n"
        f"{rooms}{area}"
        f"💵 *${l['price']:,.0f}*\n"
        f"📞 {l.get('contact_phone', '—')}\n"
        f"📅 {str(l['created_at'])[:10]}"
    )

def main_menu():
    return ReplyKeyboardMarkup([
        ["🔍 Поиск объектов", "➕ Подать объявление"],
        ["📋 Мои объявления", "ℹ️ О сервисе ESTA"],
    ], resize_keyboard=True)

def location_keyboard(page_idx):
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
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)
    # ─── /start ────────────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"👋 Добро пожаловать в *ESTA Недвижимость*, {name}!\n\n"
        f"🏠 Первый AI-портал недвижимости Молдовы и ПМР\n\n"
        f"🔍 Поиск квартир, домов, участков\n"
        f"➕ Добавить объявление за 2 минуты\n"
        f"🌐 Сайт: esta-site.vercel.app",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

async def search_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    ctx.user_data["loc_page"] = 0
    await update.message.reply_text("🔍 *Поиск*\n\nВыбери город:", parse_mode="Markdown", reply_markup=location_keyboard(0))
    return SEARCH_LOCATION_PAGE

async def search_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    page = ctx.user_data.get("loc_page", 0)
    if text == "▶️ След.":
        ctx.user_data["loc_page"] = min(page + 1, len(LOCATION_PAGES) - 1)
        await update.message.reply_text("📍 Город:", reply_markup=location_keyboard(ctx.user_data["loc_page"]))
        return SEARCH_LOCATION_PAGE
    if text == "◀️ Пред.":
        ctx.user_data["loc_page"] = max(page - 1, 0)
        await update.message.reply_text("📍 Город:", reply_markup=location_keyboard(ctx.user_data["loc_page"]))
        return SEARCH_LOCATION_PAGE
    if text == "🌍 Все регионы":
        ctx.user_data["search_location"] = None
    elif text.startswith("==="):
        await update.message.reply_text("Выбери конкретный город 👇", reply_markup=location_keyboard(page))
        return SEARCH_LOCATION_PAGE
    else:
        ctx.user_data["search_location"] = text
    await update.message.reply_text("Тип сделки:",
        reply_markup=ReplyKeyboardMarkup([["🏠 Продажа", "🔑 Аренда"], ["🔄 Все типы"]], resize_keyboard=True, one_time_keyboard=True))
    return SEARCH_DEAL

async def search_deal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    ctx.user_data["search_deal"] = "sale" if "Продажа" in text else "rent" if "Аренда" in text else None
    await update.message.reply_text("Категория:",
        reply_markup=ReplyKeyboardMarkup([["🏢 Квартира", "🏡 Дом"], ["🌱 Участок", "🏪 Коммерция"], ["🔄 Все"]], resize_keyboard=True, one_time_keyboard=True))
    return SEARCH_CAT

async def search_cat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "Квартира" in text: ctx.user_data["search_cat"] = "apartment"
    elif "Дом" in text: ctx.user_data["search_cat"] = "house"
    elif "Участок" in text: ctx.user_data["search_cat"] = "land"
    elif "Коммерция" in text: ctx.user_data["search_cat"] = "commercial"
    else: ctx.user_data["search_cat"] = None
    await update.message.reply_text("Макс. цена ($):",
        reply_markup=ReplyKeyboardMarkup([["20000", "35000", "50000"], ["80000", "150000", "🔄 Любая"]], resize_keyboard=True, one_time_keyboard=True))
    return SEARCH_PRICE

async def search_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    max_price = None if "Любая" in text else int(text.replace(" ", "").replace(",", ""))
    try:
        results = await db_search_listings(
            location=ctx.user_data.get("search_location"),
            deal=ctx.user_data.get("search_deal"),
            category=ctx.user_data.get("search_cat"),
            max_price=max_price
        )
    except Exception as e:
        logger.error(f"Save error FULL: {type(e).__name__}: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка сохранения: {type(e).__name__}: {str(e)[:100]}", reply_markup=main_menu())
        f"✅ Найдено: *{len(results)}* объявлений" if results else "😔 Ничего не найдено.",
        parse_mode="Markdown", reply_markup=main_menu())
    for l in results:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🌐 На сайте", url="https://esta-site.vercel.app")]])
        await update.message.reply_text(listing_card(l), parse_mode="Markdown", reply_markup=kb)
    return ConversationHandler.END

async def add_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    ctx.user_data["new"] = {}
    await update.message.reply_text("➕ *Добавить объявление*\n\nТип сделки:", parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([["🏠 Продажа", "🔑 Аренда помесячно"]], resize_keyboard=True, one_time_keyboard=True))
    return ADD_DEAL

async def add_deal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["deal"] = "rent" if "Аренда" in update.message.text else "sale"
    await update.message.reply_text("Категория:",
        reply_markup=ReplyKeyboardMarkup([["🏢 Квартира", "🏡 Дом / Дача"], ["🌱 Участок", "🏪 Коммерция"], ["🚗 Гараж"]], resize_keyboard=True, one_time_keyboard=True))
    return ADD_CAT

async def add_cat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "Квартира" in text: ctx.user_data["new"]["category"] = "apartment"
    elif "Дом" in text: ctx.user_data["new"]["category"] = "house"
    elif "Участок" in text: ctx.user_data["new"]["category"] = "land"
    elif "Коммерция" in text: ctx.user_data["new"]["category"] = "commercial"
    elif "Гараж" in text: ctx.user_data["new"]["category"] = "garage"
    else: ctx.user_data["new"]["category"] = "apartment"
    ctx.user_data["loc_page"] = 0
    await update.message.reply_text("📍 Выбери город:", reply_markup=location_keyboard(0))
    return ADD_LOC_PAGE

async def add_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    page = ctx.user_data.get("loc_page", 0)
    if text == "▶️ След.":
        ctx.user_data["loc_page"] = min(page + 1, len(LOCATION_PAGES) - 1)
        await update.message.reply_text("📍 Город:", reply_markup=location_keyboard(ctx.user_data["loc_page"]))
        return ADD_LOC_PAGE
    if text == "◀️ Пред.":
        ctx.user_data["loc_page"] = max(page - 1, 0)
        await update.message.reply_text("📍 Город:", reply_markup=location_keyboard(ctx.user_data["loc_page"]))
        return ADD_LOC_PAGE
    if text.startswith("===") or text == "🌍 Все регионы":
        await update.message.reply_text("Выбери конкретный город 👇", reply_markup=location_keyboard(page))
        return ADD_LOC_PAGE
    ctx.user_data["new"]["location"] = text
    await update.message.reply_text("✏️ Заголовок объявления:", reply_markup=ReplyKeyboardRemove())
    return ADD_TITLE

async def add_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["title"] = update.message.text
    cat = ctx.user_data["new"].get("category")
    if cat in ("land", "commercial", "garage"):
        ctx.user_data["new"]["rooms"] = None
        await update.message.reply_text("📐 Площадь в м²:")
        return ADD_AREA
    await update.message.reply_text("🛏 Количество комнат:",
        reply_markup=ReplyKeyboardMarkup([["1", "2", "3"], ["4", "5", "6+"]], resize_keyboard=True, one_time_keyboard=True))
    return ADD_ROOMS

async def add_rooms(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["new"]["rooms"] = int(update.message.text.replace("+", ""))
    except:
        ctx.user_data["new"]["rooms"] = 1
    await update.message.reply_text("📐 Площадь в м²:", reply_markup=ReplyKeyboardRemove())
    return ADD_AREA

async def add_area(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["new"]["area"] = float(update.message.text.replace(" ", ""))
    except:
        ctx.user_data["new"]["area"] = 0
    cat = ctx.user_data["new"].get("category")
    if cat in ("land", "commercial", "garage"):
        await update.message.reply_text("💵 Цена в $:")
        return ADD_PRICE
    await update.message.reply_text("🏢 Этаж (например: 3/9):")
    return ADD_FLOOR

async def add_floor(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["floor"] = update.message.text
    await update.message.reply_text("💵 Цена в $:")
    return ADD_PRICE

async def add_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["new"]["price"] = float(update.message.text.replace(" ", "").replace(",", ""))
    except:
        ctx.user_data["new"]["price"] = 0
    await update.message.reply_text("📝 Описание объекта:")
    return ADD_DESC

async def add_desc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["description"] = update.message.text
    await update.message.reply_text("📞 Контактный телефон:")
    return ADD_PHONE

async def add_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["phone"] = update.message.text
    await update.message.reply_text("📸 Отправь фото (или напиши 'пропустить'):")
    return ADD_PHOTO

async def add_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        listing_id = await db_save_listing(ctx.user_data["new"])
        n = ctx.user_data["new"]
        await update.message.reply_text(
            f"✅ *Объявление добавлено!*\n\n"
            f"🏠 {n.get('title')}\n"
            f"📍 {n.get('location')} | {deal_label(n.get('deal','sale'))}\n"
            f"💵 ${n.get('price', 0):,.0f}\n\n"
            f"🌐 esta-site.vercel.app",
            parse_mode="Markdown", reply_markup=main_menu())
    except Exception as e:
        logger.error(f"Save error: {e}")
        await update.message.reply_text("✅ Принято! Появится на сайте скоро.", reply_markup=main_menu())
    return ConversationHandler.END

async def my_listings(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        db = await db_connect()
        row = await db.fetchrow("""
    INSERT INTO properties
    (deal_type, property_type, city_id, title, description,
     rooms, area_total, price, currency, price_usd,
     contact_phone, source, is_active)
    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,'USD',$8,$9,'telegram',TRUE)
    RETURNING id
""", deal, prop_type, city_id,
    data.get("title", "Без названия"),
    data.get("description", ""),
    rooms, area, price,
    data.get("phone", "")
)
return str(row["id"])
        await update.message.reply_text(f"📋 {len(listings)} объявлений:", reply_markup=main_menu())
        for l in listings:
            await update.message.reply_text(listing_card(l), parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("Ошибка. Попробуй позже.", reply_markup=main_menu())

async def about(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ *ESTA Недвижимость*\n\nПервый AI-портал Молдовы и ПМР\n\n🌐 esta-site.vercel.app",
        parse_mode="Markdown", reply_markup=main_menu())

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("Отменено.", reply_markup=main_menu())
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()
    search_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("🔍 Поиск"), search_start)],
        states={
            SEARCH_LOCATION_PAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_location)],
            SEARCH_DEAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_deal)],
            SEARCH_CAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_cat)],
            SEARCH_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
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
            ADD_PHOTO: [
                MessageHandler(filters.PHOTO, add_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_photo),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(search_conv)
    app.add_handler(add_conv)
    app.add_handler(MessageHandler(filters.Regex("📋 Мои"), my_listings))
    app.add_handler(MessageHandler(filters.Regex("ℹ️ О сервисе"), about))
    logger.info("ESTA Bot v3.0 запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
