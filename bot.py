#!/usr/bin/env python3
"""
ESTA Недвижимость — Telegram Bot
@esta_realty_bot
"""

import json
import os
import logging
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, ContextTypes, filters
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8763376316:AAE-t9np7ntkoAbCyAsy5sz2DiwXHPEAZsI"
ADMIN_ID = None  # set after first /start

# ─── In-memory DB (replace with Supabase later) ───
DB = {
    "listings": [
        {
            "id": 1, "type": "sale", "category": "apartment",
            "title": "2-комнатная квартира Балка",
            "city": "Тирасполь", "rooms": 2, "price": 48000,
            "area": 52, "floor": 3, "floors_total": 9,
            "description": "Хороший ремонт, новая сантехника, рядом школа и магазины.",
            "contact": "@agent1", "phone": "+37377772473",
            "image": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800",
            "vip": True, "views": 124, "date": "2026-04-20",
            "agent_id": 0
        },
        {
            "id": 2, "type": "sale", "category": "apartment",
            "title": "1-комнатная квартира Центр",
            "city": "Тирасполь", "rooms": 1, "price": 35000,
            "area": 38, "floor": 5, "floors_total": 10,
            "description": "Центр города, евроремонт, встроенная кухня.",
            "contact": "@agent2", "phone": "+37377772473",
            "image": "https://images.unsplash.com/photo-1560448075-bb4caa6c6d91?w=800",
            "vip": False, "views": 89, "date": "2026-04-21",
            "agent_id": 0
        },
        {
            "id": 3, "type": "rent", "category": "apartment",
            "title": "3-комнатная квартира Балка",
            "city": "Тирасполь", "rooms": 3, "price": 62000,
            "area": 78, "floor": 2, "floors_total": 5,
            "description": "Просторная квартира, два балкона, парковка.",
            "contact": "@agent1", "phone": "+37377772473",
            "image": "https://images.unsplash.com/photo-1501183638710-841dd1904471?w=800",
            "vip": True, "views": 201, "date": "2026-04-19",
            "agent_id": 0
        },
        {
            "id": 4, "type": "sale", "category": "house",
            "title": "Дом в Кишинёве",
            "city": "Кишинёв", "rooms": 5, "price": 120000,
            "area": 150, "floor": 1, "floors_total": 2,
            "description": "Двухэтажный дом, гараж, сад 6 соток.",
            "contact": "@agent3", "phone": "+37369123456",
            "image": "https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=800",
            "vip": False, "views": 57, "date": "2026-04-22",
            "agent_id": 0
        },
    ],
    "users": {},       # user_id -> {name, role, subscriptions}
    "subscriptions": {},  # user_id -> {city, type, max_price, rooms}
    "next_id": 5,
}

CITIES = ["Тирасполь", "Кишинёв", "Бендеры", "Рыбница", "Бельцы", "Дубоссары"]
TYPES = {"🏠 Продажа": "sale", "🔑 Аренда": "rent"}
CATEGORIES = {"🏢 Квартира": "apartment", "🏡 Дом": "house", "🏗 Новостройка": "new", "🏪 Коммерция": "commercial"}

# Conversation states
(SEARCH_CITY, SEARCH_TYPE, SEARCH_ROOMS, SEARCH_PRICE,
 ADD_TYPE, ADD_CATEGORY, ADD_CITY, ADD_TITLE, ADD_ROOMS,
 ADD_PRICE, ADD_AREA, ADD_FLOOR, ADD_DESC, ADD_PHONE, ADD_PHOTO,
 SUB_CITY, SUB_TYPE, SUB_PRICE) = range(18)


def get_user(user_id, update=None):
    uid = str(user_id)
    if uid not in DB["users"]:
        name = ""
        if update and update.effective_user:
            u = update.effective_user
            name = u.full_name or u.username or "Пользователь"
        DB["users"][uid] = {"name": name, "role": "user", "listings_count": 0}
    return DB["users"][uid]


def listing_card(l, short=False):
    emoji = "💎 VIP | " if l.get("vip") else ""
    type_label = "Продажа" if l["type"] == "sale" else "Аренда"
    cat = {"apartment": "Квартира", "house": "Дом", "new": "Новостройка", "commercial": "Коммерция"}.get(l["category"], "Объект")
    
    if short:
        return (
            f"{emoji}🏠 *{l['title']}*\n"
            f"📍 {l['city']} | {type_label} | {l['rooms']}к\n"
            f"💵 *${l['price']:,}* | {l['area']} м²\n"
            f"👁 {l['views']} просмотров\n"
        )
    
    return (
        f"{emoji}🏠 *{l['title']}*\n\n"
        f"📍 Город: {l['city']}\n"
        f"🏷 Тип: {type_label} | {cat}\n"
        f"🛏 Комнат: {l['rooms']}\n"
        f"📐 Площадь: {l['area']} м²\n"
        f"🏢 Этаж: {l['floor']}/{l['floors_total']}\n"
        f"💵 Цена: *${l['price']:,}*\n\n"
        f"📝 {l['description']}\n\n"
        f"📞 {l['phone']}\n"
        f"👁 Просмотров: {l['views']}\n"
        f"📅 Добавлено: {l['date']}"
    )


def main_keyboard():
    return ReplyKeyboardMarkup([
        ["🔍 Поиск", "➕ Добавить объявление"],
        ["🔔 Подписка", "📊 Мои объявления"],
        ["⭐ VIP продвижение", "ℹ️ О сервисе"]
    ], resize_keyboard=True)


# ─── /start ───
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    get_user(user.id, update)
    
    text = (
        f"👋 Добро пожаловать в *ESTA Недвижимость*, {user.first_name}!\n\n"
        f"🏠 Первый AI-портал недвижимости Молдовы и ПМР\n\n"
        f"Что умею:\n"
        f"🔍 Поиск квартир и домов\n"
        f"➕ Добавить объявление за 2 минуты\n"
        f"🔔 Уведомления о новых объектах\n"
        f"💎 VIP продвижение объявлений\n\n"
        f"Выбери действие:"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=main_keyboard())


# ─── SEARCH ───
async def search_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    buttons = [[city] for city in CITIES] + [["🌍 Все города"]]
    await update.message.reply_text(
        "🔍 *Поиск объявлений*\n\nВыбери город:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)
    )
    return SEARCH_CITY


async def search_city(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    city = update.message.text
    ctx.user_data["search_city"] = None if city == "🌍 Все города" else city
    await update.message.reply_text(
        "Тип сделки:",
        reply_markup=ReplyKeyboardMarkup(
            [["🏠 Продажа", "🔑 Аренда"], ["🔄 Все"]],
            resize_keyboard=True, one_time_keyboard=True
        )
    )
    return SEARCH_TYPE


async def search_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    ctx.user_data["search_type"] = TYPES.get(t)
    await update.message.reply_text(
        "Количество комнат:",
        reply_markup=ReplyKeyboardMarkup(
            [["1", "2", "3"], ["4+", "🔄 Любое"]],
            resize_keyboard=True, one_time_keyboard=True
        )
    )
    return SEARCH_ROOMS


async def search_rooms(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    r = update.message.text
    ctx.user_data["search_rooms"] = None if r in ["🔄 Любое", "4+"] else int(r)
    if r == "4+":
        ctx.user_data["search_rooms_min"] = 4
    await update.message.reply_text(
        "Максимальная цена ($):",
        reply_markup=ReplyKeyboardMarkup(
            [["30000", "50000", "80000"], ["100000", "150000", "🔄 Любая"]],
            resize_keyboard=True, one_time_keyboard=True
        )
    )
    return SEARCH_PRICE


async def search_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    p = update.message.text
    max_price = None if p == "🔄 Любая" else int(p.replace(" ", ""))
    
    # Filter listings
    results = DB["listings"]
    if ctx.user_data.get("search_city"):
        results = [l for l in results if l["city"] == ctx.user_data["search_city"]]
    if ctx.user_data.get("search_type"):
        results = [l for l in results if l["type"] == ctx.user_data["search_type"]]
    if ctx.user_data.get("search_rooms"):
        results = [l for l in results if l["rooms"] == ctx.user_data["search_rooms"]]
    if ctx.user_data.get("search_rooms_min"):
        results = [l for l in results if l["rooms"] >= ctx.user_data["search_rooms_min"]]
    if max_price:
        results = [l for l in results if l["price"] <= max_price]
    
    # Sort: VIP first
    results = sorted(results, key=lambda x: (not x.get("vip"), -x["views"]))
    
    if not results:
        await update.message.reply_text(
            "😔 По вашим критериям ничего не найдено.\n\nПопробуйте изменить фильтры.",
            reply_markup=main_keyboard()
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        f"✅ Найдено: *{len(results)}* объявлений",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )
    
    for l in results[:5]:
        l["views"] += 1
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("📞 Позвонить", url=f"tel:{l['phone']}"),
            InlineKeyboardButton("🔗 На сайте", url=f"https://esta-site.vercel.app"),
        ]])
        try:
            await update.message.reply_photo(
                photo=l["image"],
                caption=listing_card(l),
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        except:
            await update.message.reply_text(
                listing_card(l),
                parse_mode="Markdown",
                reply_markup=keyboard
            )
    
    if len(results) > 5:
        await update.message.reply_text(f"... и ещё {len(results)-5} объявлений. Зайди на сайт для полного поиска 👉 esta-site.vercel.app")
    
    return ConversationHandler.END


# ─── ADD LISTING ───
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
    return ADD_TYPE


async def add_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["type"] = TYPES.get(update.message.text, "sale")
    await update.message.reply_text(
        "Категория:",
        reply_markup=ReplyKeyboardMarkup(
            [["🏢 Квартира", "🏡 Дом"], ["🏗 Новостройка", "🏪 Коммерция"]],
            resize_keyboard=True, one_time_keyboard=True
        )
    )
    return ADD_CATEGORY


async def add_category(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["category"] = CATEGORIES.get(update.message.text, "apartment")
    buttons = [[city] for city in CITIES]
    await update.message.reply_text(
        "Город:", reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)
    )
    return ADD_CITY


async def add_city(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["city"] = update.message.text
    await update.message.reply_text("Заголовок объявления (например: 2-комнатная квартира Центр):", reply_markup=ReplyKeyboardRemove())
    return ADD_TITLE


async def add_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["title"] = update.message.text
    await update.message.reply_text(
        "Количество комнат:",
        reply_markup=ReplyKeyboardMarkup([["1", "2", "3", "4", "5"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return ADD_ROOMS


async def add_rooms(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["new"]["rooms"] = int(update.message.text)
    except:
        ctx.user_data["new"]["rooms"] = 1
    await update.message.reply_text("Цена в долларах (только цифры, например: 48000):", reply_markup=ReplyKeyboardRemove())
    return ADD_PRICE


async def add_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["new"]["price"] = int(update.message.text.replace(" ", "").replace(",", ""))
    except:
        ctx.user_data["new"]["price"] = 0
    await update.message.reply_text("Площадь в м² (только цифры):")
    return ADD_AREA


async def add_area(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["new"]["area"] = int(update.message.text)
    except:
        ctx.user_data["new"]["area"] = 0
    await update.message.reply_text("Этаж (например: 3/9):")
    return ADD_FLOOR


async def add_floor(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    parts = update.message.text.split("/")
    ctx.user_data["new"]["floor"] = int(parts[0]) if parts[0].isdigit() else 1
    ctx.user_data["new"]["floors_total"] = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 9
    await update.message.reply_text("Описание объекта (состояние, особенности):")
    return ADD_DESC


async def add_desc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["description"] = update.message.text
    await update.message.reply_text("Контактный телефон (например: +37377123456):")
    return ADD_PHONE


async def add_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["phone"] = update.message.text
    await update.message.reply_text(
        "Отправь фото объекта (или нажми /skip чтобы пропустить):"
    )
    return ADD_PHOTO


async def add_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    n = ctx.user_data["new"]
    if update.message.photo:
        n["image"] = None  # in production: download & upload to Cloudinary
        n["has_photo"] = True
    else:
        n["image"] = "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800"
        n["has_photo"] = False
    return await save_listing(update, ctx)


async def skip_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["image"] = "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=800"
    return await save_listing(update, ctx)


async def save_listing(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    n = ctx.user_data["new"]
    user = update.effective_user
    
    listing = {
        "id": DB["next_id"],
        "type": n.get("type", "sale"),
        "category": n.get("category", "apartment"),
        "title": n.get("title", "Объект"),
        "city": n.get("city", "Тирасполь"),
        "rooms": n.get("rooms", 1),
        "price": n.get("price", 0),
        "area": n.get("area", 0),
        "floor": n.get("floor", 1),
        "floors_total": n.get("floors_total", 9),
        "description": n.get("description", ""),
        "phone": n.get("phone", ""),
        "contact": f"@{user.username}" if user.username else user.full_name,
        "image": n.get("image", ""),
        "vip": False,
        "views": 0,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "agent_id": user.id,
    }
    
    DB["listings"].append(listing)
    DB["next_id"] += 1
    
    uid = str(user.id)
    if uid in DB["users"]:
        DB["users"][uid]["listings_count"] = DB["users"][uid].get("listings_count", 0) + 1
    
    # Notify subscribers
    await notify_subscribers(update, ctx, listing)
    
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("⭐ Сделать VIP", callback_data=f"vip_{listing['id']}"),
        InlineKeyboardButton("👀 Посмотреть", url="https://esta-site.vercel.app"),
    ]])
    
    await update.message.reply_text(
        f"✅ *Объявление добавлено!*\n\n"
        f"{listing_card(listing, short=True)}\n"
        f"🆔 ID: #{listing['id']}\n\n"
        f"💡 Сделай VIP для большего охвата!",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    
    ctx.user_data.clear()
    await update.message.reply_text("Главное меню:", reply_markup=main_keyboard())
    return ConversationHandler.END


async def notify_subscribers(update, ctx, listing):
    for uid, sub in DB["subscriptions"].items():
        try:
            uid_int = int(uid)
            if uid_int == update.effective_user.id:
                continue
            match = True
            if sub.get("city") and sub["city"] != listing["city"]:
                match = False
            if sub.get("type") and sub["type"] != listing["type"]:
                match = False
            if sub.get("max_price") and listing["price"] > sub["max_price"]:
                match = False
            if match:
                await ctx.bot.send_message(
                    chat_id=uid_int,
                    text=f"🔔 *Новое объявление по вашей подписке!*\n\n{listing_card(listing, short=True)}\n👉 esta-site.vercel.app",
                    parse_mode="Markdown"
                )
        except Exception as e:
            logger.error(f"Notify error: {e}")


# ─── SUBSCRIPTION ───
async def sub_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    buttons = [[city] for city in CITIES] + [["🌍 Все города"]]
    await update.message.reply_text(
        "🔔 *Настройка уведомлений*\n\nВыбери город для подписки:",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)
    )
    return SUB_CITY


async def sub_city(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    city = update.message.text
    ctx.user_data["sub_city"] = None if city == "🌍 Все города" else city
    await update.message.reply_text(
        "Тип:",
        reply_markup=ReplyKeyboardMarkup(
            [["🏠 Продажа", "🔑 Аренда", "🔄 Все"]], resize_keyboard=True, one_time_keyboard=True
        )
    )
    return SUB_TYPE


async def sub_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    ctx.user_data["sub_type"] = TYPES.get(t)
    await update.message.reply_text(
        "Максимальная цена ($):",
        reply_markup=ReplyKeyboardMarkup(
            [["50000", "80000", "120000", "🔄 Любая"]], resize_keyboard=True, one_time_keyboard=True
        )
    )
    return SUB_PRICE


async def sub_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    p = update.message.text
    uid = str(update.effective_user.id)
    DB["subscriptions"][uid] = {
        "city": ctx.user_data.get("sub_city"),
        "type": ctx.user_data.get("sub_type"),
        "max_price": None if p == "🔄 Любая" else int(p),
    }
    city_label = ctx.user_data.get("sub_city") or "все города"
    await update.message.reply_text(
        f"✅ *Подписка активирована!*\n\n"
        f"📍 Город: {city_label}\n"
        f"💵 До: {p}\n\n"
        f"Я пришлю уведомление как только появится новое объявление по вашим критериям! 🔔",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )
    ctx.user_data.clear()
    return ConversationHandler.END


# ─── MY LISTINGS ───
async def my_listings(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    listings = [l for l in DB["listings"] if l.get("agent_id") == uid]
    
    if not listings:
        await update.message.reply_text(
            "📊 У вас пока нет объявлений.\n\nНажмите *➕ Добавить объявление* чтобы разместить!",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )
        return
    
    total_views = sum(l["views"] for l in listings)
    text = f"📊 *Мои объявления* ({len(listings)} шт)\n\n👁 Всего просмотров: {total_views}\n\n"
    
    for l in listings:
        vip = "💎 VIP" if l.get("vip") else "—"
        text += f"• *{l['title']}* | ${l['price']:,} | 👁{l['views']} | {vip}\n"
    
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("➕ Добавить ещё", callback_data="add_new"),
        InlineKeyboardButton("🌐 На сайте", url="https://esta-site.vercel.app"),
    ]])
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)


# ─── VIP ───
async def vip_info(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "⭐ *VIP продвижение*\n\n"
        "VIP объявления:\n"
        "✅ Показываются первыми в поиске\n"
        "✅ Выделены значком 💎\n"
        "✅ Рассылаются подписчикам\n"
        "✅ Публикуются в Telegram-канале\n\n"
        "💵 *Стоимость: $5/месяц*\n\n"
        "Для активации напишите нам:"
    )
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("💬 Написать менеджеру", url="https://t.me/solei3337"),
        InlineKeyboardButton("🌐 Сайт", url="https://esta-site.vercel.app"),
    ]])
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)


# ─── ABOUT ───
async def about(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "ℹ️ *ESTA Недвижимость*\n\n"
        "🏠 Первый AI-портал недвижимости Молдовы и ПМР\n\n"
        "📍 Города: Тирасполь, Кишинёв, Бендеры, Рыбница, Бельцы и другие\n"
        "🤖 AI поиск по описанию\n"
        "📱 Удобный Telegram бот\n"
        "🌐 Сайт: esta-site.vercel.app\n\n"
        "📞 Контакт: @solei3337"
    )
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🌐 Открыть сайт", url="https://esta-site.vercel.app"),
        InlineKeyboardButton("💬 Написать нам", url="https://t.me/solei3337"),
    ]])
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=keyboard)


# ─── CALLBACKS ───
async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    
    if data.startswith("vip_"):
        listing_id = int(data.split("_")[1])
        await q.message.reply_text(
            f"💎 Для активации VIP на объявление #{listing_id} напишите @solei3337\n\nСтоимость: $5/месяц",
        )
    elif data == "add_new":
        await q.message.reply_text("Нажмите ➕ Добавить объявление в меню", reply_markup=main_keyboard())


# ─── CANCEL ───
async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("❌ Отменено.", reply_markup=main_keyboard())
    return ConversationHandler.END


# ─── UNKNOWN ───
async def unknown(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""
    if "поиск" in text.lower() or "найти" in text.lower():
        await search_start(update, ctx)
    elif "добавить" in text.lower() or "разместить" in text.lower():
        await add_start(update, ctx)
    else:
        await update.message.reply_text(
            "Используй кнопки меню 👇",
            reply_markup=main_keyboard()
        )


def main():
    app = Application.builder().token(TOKEN).build()
    
    # Search conversation
    search_conv = ConversationHandler(
        entry_points=[
            CommandHandler("search", search_start),
            MessageHandler(filters.Regex("^🔍 Поиск$"), search_start),
        ],
        states={
            SEARCH_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_city)],
            SEARCH_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_type)],
            SEARCH_ROOMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_rooms)],
            SEARCH_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    # Add listing conversation
    add_conv = ConversationHandler(
        entry_points=[
            CommandHandler("add", add_start),
            MessageHandler(filters.Regex("^➕ Добавить объявление$"), add_start),
        ],
        states={
            ADD_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_type)],
            ADD_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_category)],
            ADD_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_city)],
            ADD_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_title)],
            ADD_ROOMS: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_rooms)],
            ADD_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_price)],
            ADD_AREA: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_area)],
            ADD_FLOOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_floor)],
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
    
    # Subscription conversation
    sub_conv = ConversationHandler(
        entry_points=[
            CommandHandler("subscribe", sub_start),
            MessageHandler(filters.Regex("^🔔 Подписка$"), sub_start),
        ],
        states={
            SUB_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, sub_city)],
            SUB_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, sub_type)],
            SUB_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, sub_price)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(search_conv)
    app.add_handler(add_conv)
    app.add_handler(sub_conv)
    app.add_handler(MessageHandler(filters.Regex("^📊 Мои объявления$"), my_listings))
    app.add_handler(MessageHandler(filters.Regex("^⭐ VIP продвижение$"), vip_info))
    app.add_handler(MessageHandler(filters.Regex("^ℹ️ О сервисе$"), about))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown))
    
    logger.info("🚀 ESTA Bot запущен!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
