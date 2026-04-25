#!/usr/bin/env python3
"""
ESTA Недвижимость — Telegram Bot v2.0
@esta_realty_bot
Все категории, все города и сёла ПМР и Молдовы
"""

import os
import logging
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

TOKEN = os.environ.get("BOT_TOKEN", "8763376316:AAE-t9np7ntkoAbCyAsy5sz2DiwXHPEAZsI")

# ─── СПРАВОЧНИКИ ───────────────────────────────────────────────

DEAL_TYPES = {
    "🏠 Продажа": "sale",
    "🔑 Аренда помесячно": "rent",
    "📅 Аренда посуточно": "rent_daily",
    "🛒 Куплю": "buy",
    "🔄 Обмен": "exchange",
}

CATEGORIES = {
    "🏢 Квартира": "apartment",
    "🏡 Дом / Дача": "house",
    "🏗 Новостройка": "new_build",
    "🌱 Участок": "land",
    "🏪 Коммерция": "commercial",
    "🏠 Комната": "room",
    "🚗 Гараж": "garage",
}

# Все города и сёла ПМР
PMR_LOCATIONS = [
    # Города ПМР
    "Тирасполь", "Бендеры", "Рыбница", "Дубоссары", "Слободзея",
    "Днестровск", "Григориополь",
    # Районы и сёла ПМР
    "Суклея", "Парканы", "Красное", "Колосово", "Ближний Хутор",
    "Дальний Хутор", "Малаешты", "Кицканы", "Меренешты", "Владимировка",
    "Карагаш", "Ташлык", "Чобручи", "Незавертайловка", "Глиное",
    "Новые Анены (ПМР)", "Погребя", "Коротное", "Спея",
    "Рашково", "Резина (ПМР)", "Камионка", "Воронково",
]

# Все города и районы Молдовы
MOLDOVA_LOCATIONS = [
    # Крупные города
    "Кишинёв", "Бельцы", "Унгены", "Сорока", "Оргеев",
    "Кагул", "Хынчешты", "Стрэшень", "Яловень", "Криулень",
    "Дрокия", "Флорешть", "Единец", "Бричень", "Окница",
    "Дондушень", "Глодень", "Фалешть", "Ниспорень", "Кэлэрашь",
    "Леова", "Чимишлия", "Басарабяска", "Тараклия", "Штефан Водэ",
    "Кэушень", "Анений Ной", "Новые Анены",
    # Районы Кишинёва
    "Кишинёв - Центр", "Кишинёв - Ботаника", "Кишинёв - Рышкань",
    "Кишинёв - Чокана", "Кишинёв - Буюкань", "Кишинёв - Телецентр",
    "Кишинёв - Скулянка", "Кишинёв - Малина Мике",
    # Пригороды Кишинёва
    "Дурлешть", "Кодру", "Ватра", "Трушень", "Чореску",
    "Сынджерей", "Кишинёв пригород",
    # АТО Гагаузия
    "Комрат", "Чадыр-Лунга", "Вулкэнешть",
]

ALL_LOCATIONS = PMR_LOCATIONS + MOLDOVA_LOCATIONS

# Разбивка по страницам (по 8 городов)
def get_location_pages():
    pages = []
    pmr = ["=== ПМР ==="] + PMR_LOCATIONS
    mol = ["=== МОЛДОВА ==="] + MOLDOVA_LOCATIONS
    all_locs = pmr + mol
    for i in range(0, len(all_locs), 8):
        pages.append(all_locs[i:i+8])
    return pages

LOCATION_PAGES = get_location_pages()

# ─── БАЗА ДАННЫХ (в памяти) ────────────────────────────────────
DB = {
    "listings": [
        {
            "id": 1, "deal": "sale", "category": "apartment",
            "title": "2-комнатная квартира Балка",
            "location": "Тирасполь", "rooms": 2, "price": 48000,
            "area": 52, "floor": "3/9",
            "description": "Хороший ремонт, новая сантехника, рядом школа.",
            "phone": "+37377772473", "vip": True, "views": 124,
            "date": "2026-04-20", "agent_id": 0,
            "image": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800"
        },
        {
            "id": 2, "deal": "sale", "category": "apartment",
            "title": "1-комнатная квартира Центр",
            "location": "Тирасполь", "rooms": 1, "price": 35000,
            "area": 38, "floor": "5/10",
            "description": "Центр города, евроремонт, встроенная кухня.",
            "phone": "+37377772473", "vip": False, "views": 89,
            "date": "2026-04-21", "agent_id": 0,
            "image": "https://images.unsplash.com/photo-1560448075-bb4caa6c6d91?w=800"
        },
        {
            "id": 3, "deal": "rent", "category": "apartment",
            "title": "3-комнатная квартира Балка",
            "location": "Тирасполь", "rooms": 3, "price": 300,
            "area": 78, "floor": "2/5",
            "description": "Просторная квартира, два балкона, парковка.",
            "phone": "+37377772473", "vip": True, "views": 201,
            "date": "2026-04-19", "agent_id": 0,
            "image": "https://images.unsplash.com/photo-1501183638710-841dd1904471?w=800"
        },
        {
            "id": 4, "deal": "sale", "category": "land",
            "title": "Участок под строительство, 8 соток",
            "location": "Бендеры", "rooms": 0, "price": 15000,
            "area": 800, "floor": "-",
            "description": "Ровный участок, документы готовы, свет, вода рядом.",
            "phone": "+37377772473", "vip": False, "views": 45,
            "date": "2026-04-22", "agent_id": 0,
            "image": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=800"
        },
        {
            "id": 5, "deal": "sale", "category": "house",
            "title": "Дом в Кишинёве, р-н Ботаника",
            "location": "Кишинёв - Ботаника", "rooms": 5, "price": 120000,
            "area": 150, "floor": "2 этажа",
            "description": "Двухэтажный дом, гараж, сад 6 соток, автономное отопление.",
            "phone": "+37369123456", "vip": False, "views": 57,
            "date": "2026-04-22", "agent_id": 0,
            "image": "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=800"
        },
    ],
    "users": {},
    "subscriptions": {},
    "next_id": 6,
}

# ─── СОСТОЯНИЯ ДИАЛОГОВ ────────────────────────────────────────
(
    SEARCH_LOCATION_PAGE, SEARCH_LOCATION_PICK, SEARCH_DEAL,
    SEARCH_CAT, SEARCH_ROOMS, SEARCH_PRICE,
    ADD_DEAL, ADD_CAT, ADD_LOC_PAGE, ADD_LOC_PICK,
    ADD_TITLE, ADD_ROOMS, ADD_PRICE, ADD_AREA, ADD_FLOOR,
    ADD_DESC, ADD_PHONE, ADD_PHOTO,
    SUB_LOC_PAGE, SUB_LOC_PICK, SUB_DEAL, SUB_PRICE,
) = range(22)


# ─── ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ───────────────────────────────────

def get_user(uid, update=None):
    key = str(uid)
    if key not in DB["users"]:
        name = ""
        if update and update.effective_user:
            u = update.effective_user
            name = u.full_name or u.username or "Пользователь"
        DB["users"][key] = {"name": name, "count": 0}
    return DB["users"][key]

def deal_label(d):
    return {
        "sale": "Продажа", "rent": "Аренда/мес", "rent_daily": "Аренда/сут",
        "buy": "Куплю", "exchange": "Обмен"
    }.get(d, d)

def cat_label(c):
    return {
        "apartment": "Квартира", "house": "Дом/Дача", "new_build": "Новостройка",
        "land": "Участок", "commercial": "Коммерция", "room": "Комната", "garage": "Гараж"
    }.get(c, c)

def price_suffix(deal):
    if deal == "rent": return "/мес"
    if deal == "rent_daily": return "/сут"
    return ""

def listing_short(l):
    vip = "💎 " if l.get("vip") else ""
    suf = price_suffix(l.get("deal", "sale"))
    rooms = f"{l['rooms']}к | " if l.get("rooms") and l["rooms"] > 0 else ""
    return (
        f"{vip}🏠 *{l['title']}*\n"
        f"📍 {l['location']} | {deal_label(l['deal'])} | {cat_label(l['category'])}\n"
        f"{rooms}💵 *${l['price']:,}{suf}* | {l['area']} м²\n"
        f"👁 {l['views']} просмотров\n"
    )

def listing_full(l):
    vip = "💎 VIP | " if l.get("vip") else ""
    suf = price_suffix(l.get("deal", "sale"))
    rooms_line = f"🛏 Комнат: {l['rooms']}\n" if l.get("rooms") and l["rooms"] > 0 else ""
    floor_line = f"🏢 Этаж: {l['floor']}\n" if l.get("floor") and l["floor"] != "-" else ""
    return (
        f"{vip}🏠 *{l['title']}*\n\n"
        f"📍 Расположение: {l['location']}\n"
        f"🏷 Сделка: {deal_label(l['deal'])}\n"
        f"🏗 Тип: {cat_label(l['category'])}\n"
        f"{rooms_line}"
        f"📐 Площадь: {l['area']} м²\n"
        f"{floor_line}"
        f"💵 Цена: *${l['price']:,}{suf}*\n\n"
        f"📝 {l['description']}\n\n"
        f"📞 {l['phone']}\n"
        f"👁 Просмотров: {l['views']} | 📅 {l['date']}"
    )

def main_menu():
    return ReplyKeyboardMarkup([
        ["🔍 Поиск объектов", "➕ Подать объявление"],
        ["🔔 Подписка на объекты", "📋 Мои объявления"],
        ["💎 VIP продвижение", "ℹ️ О сервисе ESTA"],
    ], resize_keyboard=True)

def location_keyboard(page_idx, back_label="◀️ Назад"):
    """Клавиатура выбора города с пагинацией"""
    pages = LOCATION_PAGES
    page = pages[page_idx]
    rows = []
    for loc in page:
        if loc.startswith("==="):
            rows.append([loc])
        else:
            rows.append([loc])
    nav = []
    if page_idx > 0:
        nav.append(f"◀️ Пред.")
    if page_idx < len(pages) - 1:
        nav.append(f"▶️ След.")
    if nav:
        rows.append(nav)
    rows.append(["🌍 Все регионы"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)


# ─── /start ────────────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    get_user(update.effective_user.id, update)
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"👋 Добро пожаловать в *ESTA Недвижимость*, {name}!\n\n"
        f"🏠 Первый AI-портал недвижимости Молдовы и ПМР\n\n"
        f"Что умею:\n"
        f"🔍 Поиск квартир, домов, участков, коммерции\n"
        f"➕ Добавить объявление за 2 минуты\n"
        f"🔔 Уведомления о новых объектах по вашим критериям\n"
        f"💎 VIP продвижение для агентов\n\n"
        f"🌐 Сайт: esta-site.vercel.app",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


# ─── ПОИСК ─────────────────────────────────────────────────────

async def search_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    ctx.user_data["loc_page"] = 0
    await update.message.reply_text(
        "🔍 *Поиск объектов*\n\nВыбери город или район:",
        parse_mode="Markdown",
        reply_markup=location_keyboard(0)
    )
    return SEARCH_LOCATION_PAGE

async def search_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    page = ctx.user_data.get("loc_page", 0)
    pages = LOCATION_PAGES

    if text == "▶️ След.":
        ctx.user_data["loc_page"] = min(page + 1, len(pages) - 1)
        await update.message.reply_text("📍 Выбери город:", reply_markup=location_keyboard(ctx.user_data["loc_page"]))
        return SEARCH_LOCATION_PAGE
    if text == "◀️ Пред.":
        ctx.user_data["loc_page"] = max(page - 1, 0)
        await update.message.reply_text("📍 Выбери город:", reply_markup=location_keyboard(ctx.user_data["loc_page"]))
        return SEARCH_LOCATION_PAGE
    if text == "🌍 Все регионы":
        ctx.user_data["search_location"] = None
    elif text.startswith("==="):
        await update.message.reply_text("Выбери конкретный город или село 👇", reply_markup=location_keyboard(page))
        return SEARCH_LOCATION_PAGE
    else:
        ctx.user_data["search_location"] = text

    # Выбор типа сделки
    await update.message.reply_text(
        "Тип сделки:",
        reply_markup=ReplyKeyboardMarkup(
            [["🏠 Продажа", "🔑 Аренда помесячно"],
             ["📅 Аренда посуточно", "🛒 Куплю"],
             ["🔄 Все типы"]],
            resize_keyboard=True, one_time_keyboard=True
        )
    )
    return SEARCH_DEAL

async def search_deal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    ctx.user_data["search_deal"] = DEAL_TYPES.get(text)
    await update.message.reply_text(
        "Категория:",
        reply_markup=ReplyKeyboardMarkup(
            [["🏢 Квартира", "🏡 Дом / Дача"],
             ["🌱 Участок", "🏗 Новостройка"],
             ["🏪 Коммерция", "🏠 Комната"],
             ["🔄 Все категории"]],
            resize_keyboard=True, one_time_keyboard=True
        )
    )
    return SEARCH_CAT

async def search_cat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    ctx.user_data["search_cat"] = CATEGORIES.get(text)
    cat = ctx.user_data.get("search_cat")

    # Для участков, коммерции и гаражей — пропускаем комнаты
    if cat in ("land", "commercial", "garage"):
        ctx.user_data["search_rooms"] = None
        await update.message.reply_text(
            "Максимальная цена ($):",
            reply_markup=ReplyKeyboardMarkup(
                [["10000", "30000", "50000"],
                 ["80000", "150000", "🔄 Любая"]],
                resize_keyboard=True, one_time_keyboard=True
            )
        )
        return SEARCH_PRICE

    await update.message.reply_text(
        "Количество комнат:",
        reply_markup=ReplyKeyboardMarkup(
            [["1", "2", "3"], ["4", "5+", "🔄 Любое"]],
            resize_keyboard=True, one_time_keyboard=True
        )
    )
    return SEARCH_ROOMS

async def search_rooms(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🔄 Любое":
        ctx.user_data["search_rooms"] = None
        ctx.user_data["search_rooms_min"] = None
    elif text == "5+":
        ctx.user_data["search_rooms"] = None
        ctx.user_data["search_rooms_min"] = 5
    else:
        try:
            ctx.user_data["search_rooms"] = int(text)
        except:
            ctx.user_data["search_rooms"] = None

    await update.message.reply_text(
        "Максимальная цена ($):",
        reply_markup=ReplyKeyboardMarkup(
            [["20000", "35000", "50000"],
             ["80000", "120000", "200000"],
             ["🔄 Любая"]],
            resize_keyboard=True, one_time_keyboard=True
        )
    )
    return SEARCH_PRICE

async def search_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    max_price = None if text == "🔄 Любая" else int(text.replace(" ", "").replace(",", ""))

    results = list(DB["listings"])
    if ctx.user_data.get("search_location"):
        results = [l for l in results if l["location"] == ctx.user_data["search_location"]]
    if ctx.user_data.get("search_deal"):
        results = [l for l in results if l["deal"] == ctx.user_data["search_deal"]]
    if ctx.user_data.get("search_cat"):
        results = [l for l in results if l["category"] == ctx.user_data["search_cat"]]
    if ctx.user_data.get("search_rooms"):
        results = [l for l in results if l["rooms"] == ctx.user_data["search_rooms"]]
    if ctx.user_data.get("search_rooms_min"):
        results = [l for l in results if l["rooms"] >= ctx.user_data["search_rooms_min"]]
    if max_price:
        results = [l for l in results if l["price"] <= max_price]

    results = sorted(results, key=lambda x: (not x.get("vip"), -x["views"]))

    await update.message.reply_text(
        f"✅ Найдено: *{len(results)}* объявлений" if results else "😔 Ничего не найдено. Попробуй изменить фильтры.",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

    for l in results[:5]:
        l["views"] += 1
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("📞 Позвонить", url=f"tel:{l['phone']}"),
            InlineKeyboardButton("🌐 На сайте", url="https://esta-site.vercel.app"),
        ]])
        try:
            await update.message.reply_photo(photo=l["image"], caption=listing_full(l),
                                              parse_mode="Markdown", reply_markup=kb)
        except:
            await update.message.reply_text(listing_full(l), parse_mode="Markdown", reply_markup=kb)

    if len(results) > 5:
        await update.message.reply_text(
            f"📋 Ещё {len(results)-5} объявлений на сайте 👉 esta-site.vercel.app"
        )
    return ConversationHandler.END


# ─── ДОБАВИТЬ ОБЪЯВЛЕНИЕ ────────────────────────────────────────

async def add_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    ctx.user_data["new"] = {}
    await update.message.reply_text(
        "➕ *Добавить объявление*\n\nТип сделки:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [["🏠 Продажа", "🔑 Аренда помесячно"],
             ["📅 Аренда посуточно", "🔄 Обмен"]],
            resize_keyboard=True, one_time_keyboard=True
        )
    )
    return ADD_DEAL

async def add_deal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["deal"] = DEAL_TYPES.get(update.message.text, "sale")
    await update.message.reply_text(
        "Категория объекта:",
        reply_markup=ReplyKeyboardMarkup(
            [["🏢 Квартира", "🏡 Дом / Дача"],
             ["🌱 Участок", "🏗 Новостройка"],
             ["🏪 Коммерция", "🏠 Комната"],
             ["🚗 Гараж"]],
            resize_keyboard=True, one_time_keyboard=True
        )
    )
    return ADD_CAT

async def add_cat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["category"] = CATEGORIES.get(update.message.text, "apartment")
    ctx.user_data["loc_page"] = 0
    await update.message.reply_text(
        "📍 Выбери город или село:",
        reply_markup=location_keyboard(0)
    )
    return ADD_LOC_PAGE

async def add_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    page = ctx.user_data.get("loc_page", 0)
    pages = LOCATION_PAGES

    if text == "▶️ След.":
        ctx.user_data["loc_page"] = min(page + 1, len(pages) - 1)
        await update.message.reply_text("📍 Выбери город:", reply_markup=location_keyboard(ctx.user_data["loc_page"]))
        return ADD_LOC_PAGE
    if text == "◀️ Пред.":
        ctx.user_data["loc_page"] = max(page - 1, 0)
        await update.message.reply_text("📍 Выбери город:", reply_markup=location_keyboard(ctx.user_data["loc_page"]))
        return ADD_LOC_PAGE
    if text.startswith("===") or text == "🌍 Все регионы":
        await update.message.reply_text("Выбери конкретный город 👇", reply_markup=location_keyboard(page))
        return ADD_LOC_PAGE

    ctx.user_data["new"]["location"] = text
    await update.message.reply_text(
        "✏️ Введи заголовок объявления:\n_(например: 2-комнатная квартира Центр, участок 8 соток)_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    return ADD_TITLE

async def add_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["title"] = update.message.text
    cat = ctx.user_data["new"].get("category")

    if cat in ("land", "commercial", "garage"):
        ctx.user_data["new"]["rooms"] = 0
        await update.message.reply_text("📐 Площадь в м² (или соток для участка):")
        return ADD_AREA

    await update.message.reply_text(
        "🛏 Количество комнат:",
        reply_markup=ReplyKeyboardMarkup(
            [["1", "2", "3"], ["4", "5", "6+"]],
            resize_keyboard=True, one_time_keyboard=True
        )
    )
    return ADD_ROOMS

async def add_rooms(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        rooms = int(update.message.text.replace("+", ""))
        ctx.user_data["new"]["rooms"] = rooms
    except:
        ctx.user_data["new"]["rooms"] = 1
    await update.message.reply_text("📐 Площадь в м²:", reply_markup=ReplyKeyboardRemove())
    return ADD_AREA

async def add_area(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["new"]["area"] = int(update.message.text.replace(" ", ""))
    except:
        ctx.user_data["new"]["area"] = 0
    cat = ctx.user_data["new"].get("category")

    if cat in ("land", "commercial", "garage"):
        ctx.user_data["new"]["floor"] = "-"
        await update.message.reply_text("💵 Цена в $ (только цифры, например: 25000):")
        return ADD_PRICE

    await update.message.reply_text("🏢 Этаж (например: 3/9 или просто 3):")
    return ADD_FLOOR

async def add_floor(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["floor"] = update.message.text
    await update.message.reply_text("💵 Цена в $ (только цифры, например: 48000):")
    return ADD_PRICE

async def add_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["new"]["price"] = int(update.message.text.replace(" ", "").replace(",", "").replace("$", ""))
    except:
        ctx.user_data["new"]["price"] = 0
    await update.message.reply_text("📝 Описание объекта (состояние, особенности, коммуникации):")
    return ADD_DESC

async def add_desc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["description"] = update.message.text
    await update.message.reply_text("📞 Контактный телефон (например: +37377123456):")
    return ADD_PHONE

async def add_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["phone"] = update.message.text
    await update.message.reply_text(
        "📸 Отправь фото объекта\n_(или напиши /skip чтобы пропустить)_",
        parse_mode="Markdown"
    )
    return ADD_PHOTO

async def add_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        ctx.user_data["new"]["image"] = "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800"
    else:
        ctx.user_data["new"]["image"] = "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800"
    return await save_listing(update, ctx)

async def skip_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["image"] = "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800"
    return await save_listing(update, ctx)

async def save_listing(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    n = ctx.user_data["new"]
    user = update.effective_user
    listing = {
        "id": DB["next_id"],
        "deal": n.get("deal", "sale"),
        "category": n.get("category", "apartment"),
        "title": n.get("title", "Объект"),
        "location": n.get("location", "Тирасполь"),
        "rooms": n.get("rooms", 0),
        "price": n.get("price", 0),
        "area": n.get("area", 0),
        "floor": n.get("floor", "-"),
        "description": n.get("description", ""),
        "phone": n.get("phone", ""),
        "image": n.get("image", ""),
        "vip": False,
        "views": 0,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "agent_id": user.id,
    }
    DB["listings"].append(listing)
    DB["next_id"] += 1

    uid = str(user.id)
    DB["users"].setdefault(uid, {"name": user.full_name, "count": 0})
    DB["users"][uid]["count"] = DB["users"][uid].get("count", 0) + 1

    await notify_subscribers(update, ctx, listing)

    suf = price_suffix(listing["deal"])
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("💎 Сделать VIP", callback_data=f"vip_{listing['id']}"),
        InlineKeyboardButton("🌐 На сайте", url="https://esta-site.vercel.app"),
    ]])
    await update.message.reply_text(
        f"✅ *Объявление #{listing['id']} добавлено!*\n\n"
        f"🏠 {listing['title']}\n"
        f"📍 {listing['location']} | {deal_label(listing['deal'])}\n"
        f"💵 ${listing['price']:,}{suf} | {listing['area']} м²\n\n"
        f"💡 Сделай VIP — объявление увидит больше людей!",
        parse_mode="Markdown",
        reply_markup=kb
    )
    ctx.user_data.clear()
    await update.message.reply_text("Главное меню 👇", reply_markup=main_menu())
    return ConversationHandler.END


async def notify_subscribers(update, ctx, listing):
    for uid, sub in DB["subscriptions"].items():
        try:
            uid_int = int(uid)
            if uid_int == update.effective_user.id:
                continue
            if sub.get("location") and sub["location"] != listing["location"]:
                continue
            if sub.get("deal") and sub["deal"] != listing["deal"]:
                continue
            if sub.get("max_price") and listing["price"] > sub["max_price"]:
                continue
            await ctx.bot.send_message(
                chat_id=uid_int,
                text=f"🔔 *Новое объявление по вашей подписке!*\n\n{listing_short(listing)}\n👉 esta-site.vercel.app",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Notify error: {e}")


# ─── ПОДПИСКА ───────────────────────────────────────────────────

async def sub_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    ctx.user_data["loc_page"] = 0
    await update.message.reply_text(
        "🔔 *Настройка уведомлений*\n\nВыбери город для подписки:",
        parse_mode="Markdown",
        reply_markup=location_keyboard(0)
    )
    return SUB_LOC_PAGE

async def sub_location(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    page = ctx.user_data.get("loc_page", 0)

    if text == "▶️ След.":
        ctx.user_data["loc_page"] = min(page + 1, len(LOCATION_PAGES) - 1)
        await update.message.reply_text("📍 Выбери город:", reply_markup=location_keyboard(ctx.user_data["loc_page"]))
        return SUB_LOC_PAGE
    if text == "◀️ Пред.":
        ctx.user_data["loc_page"] = max(page - 1, 0)
        await update.message.reply_text("📍 Выбери город:", reply_markup=location_keyboard(ctx.user_data["loc_page"]))
        return SUB_LOC_PAGE
    if text == "🌍 Все регионы":
        ctx.user_data["sub_location"] = None
    elif text.startswith("==="):
        await update.message.reply_text("Выбери конкретный город 👇", reply_markup=location_keyboard(page))
        return SUB_LOC_PAGE
    else:
        ctx.user_data["sub_location"] = text

    await update.message.reply_text(
        "Тип сделки:",
        reply_markup=ReplyKeyboardMarkup(
            [["🏠 Продажа", "🔑 Аренда помесячно"],
             ["📅 Аренда посуточно", "🔄 Все типы"]],
            resize_keyboard=True, one_time_keyboard=True
        )
    )
    return SUB_DEAL

async def sub_deal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["sub_deal"] = DEAL_TYPES.get(update.message.text)
    await update.message.reply_text(
        "Максимальная цена ($):",
        reply_markup=ReplyKeyboardMarkup(
            [["20000", "50000", "80000"],
             ["120000", "200000", "🔄 Любая"]],
            resize_keyboard=True, one_time_keyboard=True
        )
    )
    return SUB_PRICE

async def sub_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.effective_user.id)
    max_price = None if text == "🔄 Любая" else int(text.replace(" ", ""))
    DB["subscriptions"][uid] = {
        "location": ctx.user_data.get("sub_location"),
        "deal": ctx.user_data.get("sub_deal"),
        "max_price": max_price,
    }
    loc = ctx.user_data.get("sub_location") or "все регионы"
    await update.message.reply_text(
        f"✅ *Подписка активирована!*\n\n"
        f"📍 {loc}\n"
        f"💵 До ${text}\n\n"
        f"Пришлю уведомление как только появится подходящий объект! 🔔",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )
    ctx.user_data.clear()
    return ConversationHandler.END


# ─── МОИ ОБЪЯВЛЕНИЯ ────────────────────────────────────────────

async def my_listings(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    listings = [l for l in DB["listings"] if l.get("agent_id") == uid]
    if not listings:
        await update.message.reply_text(
            "📋 У вас пока нет объявлений.\n\nНажми *➕ Подать объявление*!",
            parse_mode="Markdown", reply_markup=main_menu()
        )
        return
    total_views = sum(l["views"] for l in listings)
    text = f"📋 *Мои объявления* ({len(listings)} шт)\n👁 Всего просмотров: {total_views}\n\n"
    for l in listings:
        suf = price_suffix(l.get("deal", "sale"))
        vip = "💎" if l.get("vip") else "—"
        text += f"• *{l['title']}* | ${l['price']:,}{suf} | 👁{l['views']} | {vip}\n"
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("➕ Добавить ещё", callback_data="add_new"),
        InlineKeyboardButton("🌐 На сайте", url="https://esta-site.vercel.app"),
    ]])
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=kb)


# ─── VIP ────────────────────────────────────────────────────────

async def vip_info(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("💬 Написать менеджеру", url="https://t.me/solei3337"),
        InlineKeyboardButton("🌐 Сайт", url="https://esta-site.vercel.app"),
    ]])
    await update.message.reply_text(
        "💎 *VIP продвижение*\n\n"
        "VIP объявления:\n"
        "✅ Показываются первыми в поиске\n"
        "✅ Отмечены значком 💎\n"
        "✅ Рассылаются всем подписчикам\n"
        "✅ Публикуются в Telegram-канале ESTA\n"
        "✅ Выделены на сайте esta-site.vercel.app\n\n"
        "💵 *Стоимость: $5/месяц*\n\n"
        "Для активации напиши менеджеру:",
        parse_mode="Markdown", reply_markup=kb
    )


# ─── О СЕРВИСЕ ──────────────────────────────────────────────────

async def about(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🌐 Открыть сайт", url="https://esta-site.vercel.app"),
        InlineKeyboardButton("💬 Написать нам", url="https://t.me/solei3337"),
    ]])
    await update.message.reply_text(
        "ℹ️ *ESTA Недвижимость*\n\n"
        "🏠 Первый AI-портал недвижимости Молдовы и ПМР\n\n"
        "📍 Охват: Тирасполь, Бендеры, Рыбница, Дубоссары, Слободзея, "
        "Кишинёв, Бельцы, Унгены и все сёла ПМР и Молдовы\n\n"
        "🔍 Все категории:\n"
        "• Квартиры (1-5+ комнат)\n"
        "• Дома и дачи\n"
        "• Участки\n"
        "• Новостройки\n"
        "• Коммерческая недвижимость\n"
        "• Комнаты, гаражи\n\n"
        "🌐 esta-site.vercel.app\n"
        "📞 @solei3337",
        parse_mode="Markdown", reply_markup=kb
    )


# ─── CALLBACKS ──────────────────────────────────────────────────

async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data.startswith("vip_"):
        lid = q.data.split("_")[1]
        await q.message.reply_text(
            f"💎 Для VIP на объявление #{lid} напишите @solei3337\nСтоимость: $5/месяц"
        )
    elif q.data == "add_new":
        await q.message.reply_text("Нажми ➕ Подать объявление в меню 👇", reply_markup=main_menu())


# ─── ОТМЕНА ─────────────────────────────────────────────────────

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("❌ Отменено.", reply_markup=main_menu())
    return ConversationHandler.END

async def unknown(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Используй кнопки меню 👇", reply_markup=main_menu())


# ─── MAIN ───────────────────────────────────────────────────────

def make_search_conv():
    return ConversationHandler(
        entry_points=[
            CommandHandler("search", search_start),
            MessageHandler(filters.Regex("^🔍 Поиск объектов$"), search_start),
        ],
        states={
            SEARCH_LOCATION_PAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_location)],
            SEARCH_DEAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_deal)],
            SEARCH_CAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_cat)],
            SEARCH_ROOMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_rooms)],
            SEARCH_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

def make_add_conv():
    return ConversationHandler(
        entry_points=[
            CommandHandler("add", add_start),
            MessageHandler(filters.Regex("^➕ Подать объявление$"), add_start),
        ],
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
                CommandHandler("skip", skip_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, skip_photo),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

def make_sub_conv():
    return ConversationHandler(
        entry_points=[
            CommandHandler("subscribe", sub_start),
            MessageHandler(filters.Regex("^🔔 Подписка на объекты$"), sub_start),
        ],
        states={
            SUB_LOC_PAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, sub_location)],
            SUB_DEAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, sub_deal)],
            SUB_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, sub_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )


def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(make_search_conv())
    app.add_handler(make_add_conv())
    app.add_handler(make_sub_conv())
    app.add_handler(MessageHandler(filters.Regex("^📋 Мои объявления$"), my_listings))
    app.add_handler(MessageHandler(filters.Regex("^💎 VIP продвижение$"), vip_info))
    app.add_handler(MessageHandler(filters.Regex("^ℹ️ О сервисе ESTA$"), about))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))
    logger.info("🚀 ESTA Bot v2.0 запущен!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
