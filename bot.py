#!/usr/bin/env python3
"""
ESTA Недвижимость — Telegram Bot v4.0
@esta_realty_bot
Production-ready | PostgreSQL | Все типы сделок
"""

import os
import logging
import asyncpg
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, ReplyKeyboardRemove, InputMediaPhoto
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, CallbackQueryHandler,
    ContextTypes, filters
)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN        = os.environ.get("BOT_TOKEN", "")
DATABASE_URL = os.environ.get("DATABASE_URL", "")
MANAGER_ID   = int(os.environ.get("MANAGER_CHAT_ID", "5705817827"))
SITE_URL     = "https://esta-site.vercel.app"

DEAL_TYPES = {
    "🏠 Продажа":    "sale",
    "🔑 Аренда/мес": "rent",
    "📅 Аренда/сут": "rent",
    "🔄 Обмен":      "sale",
}

PROP_TYPES = {
    "🏢 Квартира":    "apartment",
    "🏡 Дом/Дача":    "house",
    "🏗 Новостройка": "apartment",
    "🌱 Участок":     "land",
    "🏪 Коммерция":   "commercial",
    "🚗 Гараж":       "garage",
    "🏭 Склад":       "storage",
}

CITY_MAP = {
    "Тирасполь": 3, "Бендеры": 4, "Рыбница": 5,
    "Дубоссары": 6, "Слободзея": 3, "Днестровск": 3,
    "Григориополь": 3, "Суклея": 3, "Парканы": 4,
    "Кишинёв": 1, "Кишинёв - Центр": 1, "Кишинёв - Ботаника": 1,
    "Кишинёв - Рышкань": 1, "Кишинёв - Чокана": 1,
    "Кишинёв - Буюкань": 1, "Кишинёв - Телецентр": 1,
    "Бельцы": 2, "Унгены": 1, "Сорока": 1, "Оргеев": 1,
    "Кагул": 1, "Хынчешты": 1, "Яловень": 1,
    "Комрат": 1, "Чадыр-Лунга": 1, "Дурлешть": 1,
    "Кодру": 1, "Ватра": 1,
}

PMR = [
    "Тирасполь", "Бендеры", "Рыбница", "Дубоссары",
    "Слободзея", "Днестровск", "Григориополь",
    "Суклея", "Парканы", "Красное", "Колосово",
    "Ближний Хутор", "Дальний Хутор", "Малаешты",
    "Кицканы", "Меренешты", "Владимировка", "Карагаш",
    "Ташлык", "Чобручи", "Незавертайловка", "Глиное",
    "Погребя", "Коротное", "Спея",
]

MOLDOVA = [
    "Кишинёв", "Кишинёв - Центр", "Кишинёв - Ботаника",
    "Кишинёв - Рышкань", "Кишинёв - Чокана",
    "Кишинёв - Буюкань", "Кишинёв - Телецентр",
    "Бельцы", "Унгены", "Сорока", "Оргеев", "Кагул",
    "Хынчешты", "Стрэшень", "Яловень", "Криулень",
    "Дрокия", "Флорешть", "Единец", "Бричень", "Окница",
    "Дондушень", "Глодень", "Фалешть", "Ниспорень",
    "Кэлэрашь", "Леова", "Чимишлия", "Басарабяска",
    "Тараклия", "Штефан Водэ", "Кэушень", "Анений Ной",
    "Комрат", "Чадыр-Лунга", "Вулкэнешть",
    "Дурлешть", "Кодру", "Ватра", "Трушень",
]

def loc_pages():
    all_locs = ["═══ ПМР ═══"] + PMR + ["═══ МОЛДОВА ═══"] + MOLDOVA
    return [all_locs[i:i+8] for i in range(0, len(all_locs), 8)]

LOC_PAGES = loc_pages()

(
    ADD_DEAL, ADD_TYPE, ADD_LOC, ADD_TITLE, ADD_ROOMS,
    ADD_AREA, ADD_FLOOR, ADD_PRICE, ADD_DESC, ADD_PHONE,
    ADD_PHOTOS, ADD_CONFIRM,
    SEARCH_LOC, SEARCH_DEAL, SEARCH_TYPE, SEARCH_PRICE,
) = range(16)
async def db():
    return await asyncpg.connect(DATABASE_URL)

async def save_property(data: dict) -> str:
    conn = await db()
    try:
        city_id = CITY_MAP.get(data.get("location"), 1)
        deal    = data.get("deal", "sale")
        if deal not in ("sale", "rent"):
            deal = "sale"
        prop    = data.get("prop_type", "apartment")
        if prop not in ("apartment","house","commercial","garage","storage","land"):
            prop = "apartment"
        price   = float(data.get("price") or 0)
        rooms   = int(data["rooms"]) if data.get("rooms") else None
        area    = float(data["area"]) if data.get("area") else None
        photos  = data.get("photos", [])
        row = await conn.fetchrow("""
            INSERT INTO properties
              (deal_type, property_type, city_id, district,
               title, description, rooms, area_total,
               price, currency, price_usd,
               contact_phone, contact_type,
               source, is_active, photos)
            VALUES
              ($1,$2,$3,$4,$5,$6,$7,$8,$9,'USD',$9,$10,'owner','telegram',TRUE,$11)
            RETURNING id
        """,
            deal, prop, city_id, data.get("location"),
            data.get("title", "Без названия"),
            data.get("description", ""),
            rooms, area, price,
            data.get("phone", ""),
            photos
        )
        return str(row["id"])
    finally:
        await conn.close()

async def search_properties(location=None, deal=None, prop_type=None, max_price=None):
    conn = await db()
    try:
        conds = ["is_active = TRUE"]
        params = []
        n = 1
        if location and location in CITY_MAP:
            conds.append(f"city_id = ${n}"); params.append(CITY_MAP[location]); n+=1
        if deal in ("sale","rent"):
            conds.append(f"deal_type = ${n}"); params.append(deal); n+=1
        if prop_type in ("apartment","house","land","commercial","garage","storage"):
            conds.append(f"property_type = ${n}"); params.append(prop_type); n+=1
        if max_price:
            conds.append(f"price_usd <= ${n}"); params.append(float(max_price)); n+=1
        rows = await conn.fetch(
            f"SELECT * FROM properties WHERE {' AND '.join(conds)}"
            f" ORDER BY is_featured DESC, created_at DESC LIMIT 8",
            *params
        )
        return [dict(r) for r in rows]
    finally:
        await conn.close()

async def get_stats():
    conn = await db()
    try:
        return await conn.fetchrow("SELECT * FROM v_stats")
    except:
        return None
    finally:
        await conn.close()

def deal_ru(d):
    return {"sale":"Продажа","rent":"Аренда"}.get(d, d)

def type_ru(t):
    return {"apartment":"Квартира","house":"Дом/Дача","land":"Участок",
            "commercial":"Коммерция","garage":"Гараж","storage":"Склад"}.get(t, t)

def fmt_card(p, full=False):
    vip   = "💎 VIP\n" if p.get("is_featured") else ""
    rooms = f"🛏 {p['rooms']}к  " if p.get("rooms") else ""
    area  = f"📐 {p['area_total']} м²  " if p.get("area_total") else ""
    price = float(p.get("price") or 0)
    suf   = "/мес" if p.get("deal_type") == "rent" else ""
    city  = p.get("district") or "—"
    phone = p.get("contact_phone") or "—"
    base  = (
        f"{vip}🏠 *{p['title']}*\n"
        f"📍 {city}\n"
        f"🏷 {deal_ru(p['deal_type'])} · {type_ru(p['property_type'])}\n"
        f"{rooms}{area}\n"
        f"💵 *${price:,.0f}{suf}*\n"
    )
    if full:
        desc = p.get("description","")
        base += f"\n📝 {desc}\n" if desc else ""
        base += f"📞 {phone}\n"
        base += f"👁 {p.get('views_count',0)} просмотров"
    else:
        base += f"📞 {phone}"
    return base

def main_menu():
    return ReplyKeyboardMarkup([
        ["🔍 Найти объект",   "➕ Подать объявление"],
        ["📋 Мои объявления", "📊 Статистика"],
        ["ℹ️ О нас",          "📞 Связаться"],
    ], resize_keyboard=True)

def loc_kb(page=0):
    rows = [[loc] for loc in LOC_PAGES[page]]
    nav = []
    if page > 0:                  nav.append("◀️ Назад")
    if page < len(LOC_PAGES)-1:   nav.append("▶️ Далее")
    if nav: rows.append(nav)
    rows.append(["🌍 Весь регион", "❌ Отмена"])
    return ReplyKeyboardMarkup(rows, resize_keyboard=True, one_time_keyboard=True)

def deal_kb():
    return ReplyKeyboardMarkup([
        ["🏠 Продажа",    "🔑 Аренда/мес"],
        ["📅 Аренда/сут", "🔄 Обмен"],
        ["❌ Отмена"]
    ], resize_keyboard=True, one_time_keyboard=True)

def type_kb():
    return ReplyKeyboardMarkup([
        ["🏢 Квартира",    "🏡 Дом/Дача"],
        ["🏗 Новостройка", "🌱 Участок"],
        ["🏪 Коммерция",   "🚗 Гараж"],
        ["🏭 Склад",       "❌ Отмена"]
    ], resize_keyboard=True, one_time_keyboard=True)

def price_kb():
    return ReplyKeyboardMarkup([
        ["15 000", "25 000", "40 000"],
        ["60 000", "100 000", "200 000"],
        ["🔄 Любая цена", "❌ Отмена"]
    ], resize_keyboard=True, one_time_keyboard=True)

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    name   = update.effective_user.first_name
    stats  = await get_stats()
    total  = stats["total_active"] if stats else "..."
    await update.message.reply_text(
        f"👋 *Привет, {name}!*\n\n"
        f"🏠 *ESTA Недвижимость* — AI-платформа\n"
        f"недвижимости Молдовы и Приднестровья\n\n"
        f"📊 В базе: *{total}* объявлений\n\n"
        f"Выбери действие 👇",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )

async def cmd_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("❌ Отменено.", reply_markup=main_menu())
    return ConversationHandler.END

async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    stats = await get_stats()
    if not stats:
        await update.message.reply_text("Нет данных.", reply_markup=main_menu())
        return
    await update.message.reply_text(
        f"📊 *Статистика ESTA*\n\n"
        f"🏠 Всего: *{stats['total_active']}*\n"
        f"🛒 Продажа: *{stats['for_sale']}*\n"
        f"🔑 Аренда: *{stats['for_rent']}*\n"
        f"🏗 Новостройки: *{stats['new_builds']}*\n"
        f"✍️ Из бота: *{stats['manual_entries']}*\n"
        f"🤖 Спарсировано: *{stats['parsed_entries']}*",
        parse_mode="Markdown", reply_markup=main_menu()
    )

async def cmd_about(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"ℹ️ *ESTA Недвижимость*\n\n"
        f"🌐 Сайт: {SITE_URL}\n"
        f"🤖 Бот: @esta_realty_bot\n\n"
        f"Первая AI-платформа недвижимости\n"
        f"Молдовы и Приднестровья.\n\n"
        f"Купля, продажа, аренда — квартиры,\n"
        f"дома, коммерция, участки.",
        parse_mode="Markdown", reply_markup=main_menu()
    )

async def cmd_contact(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📞 *Связаться с нами*\n\n"
        f"Telegram: @esta_support\n"
        f"Сайт: {SITE_URL}\n\n"
        f"Ответим в течение 30 минут!",
        parse_mode="Markdown", reply_markup=main_menu()
    )

async def cmd_my_listings(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    conn = await db()
    try:
        rows = await conn.fetch(
            "SELECT * FROM properties WHERE source='telegram' AND is_active=TRUE"
            " ORDER BY created_at DESC LIMIT 10"
        )
    finally:
        await conn.close()
    if not rows:
        await update.message.reply_text(
            "У вас пока нет объявлений.\n\nНажми ➕ Подать объявление",
            reply_markup=main_menu()
        )
        return
    await update.message.reply_text(
        f"📋 *Ваши объявления* ({len(rows)} шт):",
        parse_mode="Markdown", reply_markup=main_menu()
    )
    for p in rows:
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("🌐 На сайте", url=SITE_URL),
            InlineKeyboardButton("❌ Удалить", callback_data=f"del_{p['id']}")
        ]])
        await update.message.reply_text(fmt_card(dict(p)), parse_mode="Markdown", reply_markup=kb)

async def cb_delete(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    prop_id = q.data.replace("del_","")
    conn = await db()
    try:
        await conn.execute("UPDATE properties SET is_active=FALSE WHERE id=$1::uuid", prop_id)
    finally:
        await conn.close()
    await q.edit_message_text("✅ Объявление удалено.")
    async def add_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        ctx.user_data.clear()
        ctx.user_data["new"] = {"photos": []}
    await update.message.reply_text(
        "➕ *Подача объявления*\n\n📋 Шаг 1/10 — Тип сделки:",
        parse_mode="Markdown", reply_markup=deal_kb()
    )
    return ADD_DEAL

async def add_deal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    if "Отмена" in t: return await cmd_cancel(update, ctx)
    ctx.user_data["new"]["deal"] = DEAL_TYPES.get(t, "sale")
    await update.message.reply_text("📋 Шаг 2/10 — Тип недвижимости:", reply_markup=type_kb())
    return ADD_TYPE

async def add_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    if "Отмена" in t: return await cmd_cancel(update, ctx)
    ctx.user_data["new"]["prop_type"] = PROP_TYPES.get(t, "apartment")
    ctx.user_data["loc_page"] = 0
    await update.message.reply_text("📋 Шаг 3/10 — Город или район:", reply_markup=loc_kb(0))
    return ADD_LOC

async def add_loc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    p = ctx.user_data.get("loc_page", 0)
    if "Отмена" in t: return await cmd_cancel(update, ctx)
    if t == "▶️ Далее":
        ctx.user_data["loc_page"] = min(p+1, len(LOC_PAGES)-1)
        await update.message.reply_text("📍 Выбери:", reply_markup=loc_kb(ctx.user_data["loc_page"]))
        return ADD_LOC
    if t == "◀️ Назад":
        ctx.user_data["loc_page"] = max(p-1, 0)
        await update.message.reply_text("📍 Выбери:", reply_markup=loc_kb(ctx.user_data["loc_page"]))
        return ADD_LOC
    if t.startswith("═══"):
        await update.message.reply_text("👆 Выбери конкретный город", reply_markup=loc_kb(p))
        return ADD_LOC
    ctx.user_data["new"]["location"] = "Весь регион" if t == "🌍 Весь регион" else t
    await update.message.reply_text(
        "📋 Шаг 4/10 — Заголовок объявления:\n_(Например: 2-комнатная квартира с ремонтом)_",
        parse_mode="Markdown", reply_markup=ReplyKeyboardRemove()
    )
    return ADD_TITLE

async def add_title(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["title"] = update.message.text
    prop = ctx.user_data["new"].get("prop_type")
    if prop in ("land","commercial","garage","storage"):
        ctx.user_data["new"]["rooms"] = None
        await update.message.reply_text("📋 Шаг 5/10 — Площадь в м²:")
        return ADD_AREA
    await update.message.reply_text(
        "📋 Шаг 5/10 — Количество комнат:",
        reply_markup=ReplyKeyboardMarkup([["1","2","3"],["4","5","6+"],["❌ Отмена"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return ADD_ROOMS

async def add_rooms(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    if "Отмена" in t: return await cmd_cancel(update, ctx)
    try: ctx.user_data["new"]["rooms"] = int(t.replace("+",""))
    except: ctx.user_data["new"]["rooms"] = 1
    await update.message.reply_text("📋 Шаг 6/10 — Площадь в м²:", reply_markup=ReplyKeyboardRemove())
    return ADD_AREA

async def add_area(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try: ctx.user_data["new"]["area"] = float(update.message.text.replace(",","."))
    except: ctx.user_data["new"]["area"] = None
    prop = ctx.user_data["new"].get("prop_type")
    if prop in ("land","commercial","garage","storage"):
        await update.message.reply_text("📋 Шаг 7/10 — Цена в $ (только цифры):")
        return ADD_PRICE
    await update.message.reply_text("📋 Шаг 7/10 — Этаж (например: 3/9):")
    return ADD_FLOOR

async def add_floor(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["floor"] = update.message.text
    await update.message.reply_text("📋 Шаг 8/10 — Цена в $ (только цифры, например: 45000):")
    return ADD_PRICE

async def add_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        ctx.user_data["new"]["price"] = float(update.message.text.replace(" ","").replace(",",""))
    except:
        await update.message.reply_text("⚠️ Введи только цифры, например: 45000")
        return ADD_PRICE
    await update.message.reply_text(
        "📋 Шаг 9/10 — Описание:\n_(Состояние, ремонт, инфраструктура)_",
        parse_mode="Markdown"
    )
    return ADD_DESC

async def add_desc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["description"] = update.message.text
    await update.message.reply_text("📋 Шаг 9.5/10 — Контактный телефон:")
    return ADD_PHONE

async def add_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["new"]["phone"] = update.message.text
    ctx.user_data["new"]["photos"] = []
    await update.message.reply_text(
        "📋 Шаг 10/10 — Фотографии:\n\n"
        "📸 Отправь фото (можно несколько)\n"
        "✅ Когда закончишь — напиши *готово*",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup([["✅ Готово, без фото"]], resize_keyboard=True)
    )
    return ADD_PHOTOS

async def add_photos(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        file = await update.message.photo[-1].get_file()
        ctx.user_data["new"]["photos"].append(file.file_path)
        count = len(ctx.user_data["new"]["photos"])
        await update.message.reply_text(f"✅ Фото {count} добавлено. Ещё или напиши *готово*", parse_mode="Markdown")
        return ADD_PHOTOS
    t = update.message.text or ""
    if "готово" in t.lower() or "Готово" in t or "✅" in t:
        return await add_confirm(update, ctx)
    return ADD_PHOTOS

async def add_confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    n = ctx.user_data.get("new", {})
    price = float(n.get("price") or 0)
    rooms = f"🛏 {n['rooms']}к  " if n.get("rooms") else ""
    area  = f"📐 {n.get('area')} м²  " if n.get("area") else ""
    photos_count = len(n.get("photos", []))
    preview = (
        f"📋 *Проверь объявление:*\n\n"
        f"🏠 {n.get('title')}\n"
        f"📍 {n.get('location')}\n"
        f"🏷 {deal_ru(n.get('deal','sale'))} · {type_ru(n.get('prop_type','apartment'))}\n"
        f"{rooms}{area}\n"
        f"💵 *${price:,.0f}*\n"
        f"📝 {str(n.get('description',''))[:80]}...\n"
        f"📞 {n.get('phone')}\n"
        f"📸 Фото: {photos_count} шт\n\n"
        f"Всё верно?"
    )
    await update.message.reply_text(
        preview, parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [["✅ Опубликовать", "✏️ Исправить"], ["❌ Отмена"]],
            resize_keyboard=True, one_time_keyboard=True
        )
    )
    return ADD_CONFIRM

async def add_final(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    if "Отмена" in t or "Исправить" in t:
        return await cmd_cancel(update, ctx)
    n = ctx.user_data.get("new", {})
    try:
        listing_id = await save_property(n)
        price = float(n.get("price") or 0)
        try:
            await ctx.bot.send_message(
                chat_id=MANAGER_ID,
                text=(
                    f"🔔 *Новое объявление!*\n\n"
                    f"🏠 {n.get('title')}\n"
                    f"📍 {n.get('location')}\n"
                    f"💵 ${price:,.0f}\n"
                    f"📞 {n.get('phone')}\n"
                    f"👤 @{update.effective_user.username or update.effective_user.id}\n"
                    f"🆔 `{listing_id}`"
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.warning(f"Manager notify failed: {e}")
        await update.message.reply_text(
            f"🎉 *Объявление опубликовано!*\n\n"
            f"🏠 {n.get('title')}\n"
            f"📍 {n.get('location')} · {deal_ru(n.get('deal','sale'))}\n"
            f"💵 ${price:,.0f}\n\n"
            f"🌐 Уже на сайте: {SITE_URL}\n"
            f"📋 Мои объявления: /my",
            parse_mode="Markdown", reply_markup=main_menu()
        )
        ctx.user_data.clear()
    except Exception as e:
        logger.error(f"Save error: {e}", exc_info=True)
        await update.message.reply_text(f"❌ Ошибка: {str(e)[:200]}", reply_markup=main_menu())
    return ConversationHandler.END

async def search_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    ctx.user_data["loc_page"] = 0
    await update.message.reply_text("🔍 *Поиск*\n\nВыбери город:", parse_mode="Markdown", reply_markup=loc_kb(0))
    return SEARCH_LOC

async def search_loc(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    p = ctx.user_data.get("loc_page", 0)
    if "Отмена" in t: return await cmd_cancel(update, ctx)
    if t == "▶️ Далее":
        ctx.user_data["loc_page"] = min(p+1, len(LOC_PAGES)-1)
        await update.message.reply_text("📍 Выбери:", reply_markup=loc_kb(ctx.user_data["loc_page"]))
        return SEARCH_LOC
    if t == "◀️ Назад":
        ctx.user_data["loc_page"] = max(p-1, 0)
        await update.message.reply_text("📍 Выбери:", reply_markup=loc_kb(ctx.user_data["loc_page"]))
        return SEARCH_LOC
    if t.startswith("═══"):
        await update.message.reply_text("👆 Выбери конкретный город", reply_markup=loc_kb(p))
        return SEARCH_LOC
    ctx.user_data["s_loc"] = None if t == "🌍 Весь регион" else t
    await update.message.reply_text(
        "Тип сделки:",
        reply_markup=ReplyKeyboardMarkup([["🏠 Продажа","🔑 Аренда"],["🔄 Все типы","❌ Отмена"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return SEARCH_DEAL

async def search_deal(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    if "Отмена" in t: return await cmd_cancel(update, ctx)
    if "Продажа" in t: ctx.user_data["s_deal"] = "sale"
    elif "Аренда" in t: ctx.user_data["s_deal"] = "rent"
    else: ctx.user_data["s_deal"] = None
    await update.message.reply_text(
        "Тип объекта:",
        reply_markup=ReplyKeyboardMarkup([["🏢 Квартира","🏡 Дом"],["🌱 Участок","🏪 Коммерция"],["🔄 Все","❌ Отмена"]], resize_keyboard=True, one_time_keyboard=True)
    )
    return SEARCH_TYPE

async def search_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    if "Отмена" in t: return await cmd_cancel(update, ctx)
    if "Квартира" in t: ctx.user_data["s_type"] = "apartment"
    elif "Дом" in t: ctx.user_data["s_type"] = "house"
    elif "Участок" in t: ctx.user_data["s_type"] = "land"
    elif "Коммерция" in t: ctx.user_data["s_type"] = "commercial"
    else: ctx.user_data["s_type"] = None
    await update.message.reply_text("Макс. цена $:", reply_markup=price_kb())
    return SEARCH_PRICE

async def search_price(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t = update.message.text
    if "Отмена" in t: return await cmd_cancel(update, ctx)
    max_p = None if "Любая" in t else int(t.replace(" ","").replace(",",""))
    await update.message.reply_text("⏳ Ищу...", reply_markup=ReplyKeyboardRemove())
    try:
        results = await search_properties(
            location=ctx.user_data.get("s_loc"),
            deal=ctx.user_data.get("s_deal"),
            prop_type=ctx.user_data.get("s_type"),
            max_price=max_p
        )
    except Exception as e:
        logger.error(f"Search error: {e}")
        results = []
    if not results:
        await update.message.reply_text("😔 *Ничего не найдено.*\n\nПопробуй изменить фильтры.", parse_mode="Markdown", reply_markup=main_menu())
        return ConversationHandler.END
    await update.message.reply_text(f"✅ *Найдено {len(results)} объявлений*", parse_mode="Markdown", reply_markup=main_menu())
    for p in results:
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("📞 Позвонить", url=f"tel:{p.get('contact_phone','')}"),
            InlineKeyboardButton("🌐 На сайте", url=SITE_URL),
        ]])
        await update.message.reply_text(fmt_card(p, full=True), parse_mode="Markdown", reply_markup=kb)
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()
    add_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("➕ Подать"), add_start)],
        states={
            ADD_DEAL:    [MessageHandler(filters.TEXT & ~filters.COMMAND, add_deal)],
            ADD_TYPE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, add_type)],
            ADD_LOC:     [MessageHandler(filters.TEXT & ~filters.COMMAND, add_loc)],
            ADD_TITLE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, add_title)],
            ADD_ROOMS:   [MessageHandler(filters.TEXT & ~filters.COMMAND, add_rooms)],
            ADD_AREA:    [MessageHandler(filters.TEXT & ~filters.COMMAND, add_area)],
            ADD_FLOOR:   [MessageHandler(filters.TEXT & ~filters.COMMAND, add_floor)],
            ADD_PRICE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, add_price)],
            ADD_DESC:    [MessageHandler(filters.TEXT & ~filters.COMMAND, add_desc)],
            ADD_PHONE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, add_phone)],
            ADD_PHOTOS:  [MessageHandler(filters.PHOTO, add_photos), MessageHandler(filters.TEXT & ~filters.COMMAND, add_photos)],
            ADD_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_final)],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
        allow_reentry=True,
    )
    search_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("🔍 Найти"), search_start)],
        states={
            SEARCH_LOC:   [MessageHandler(filters.TEXT & ~filters.COMMAND, search_loc)],
            SEARCH_DEAL:  [MessageHandler(filters.TEXT & ~filters.COMMAND, search_deal)],
            SEARCH_TYPE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, search_type)],
            SEARCH_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_price)],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
        allow_reentry=True,
    )
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("cancel", cmd_cancel))
    app.add_handler(CommandHandler("my",     cmd_my_listings))
    app.add_handler(CommandHandler("stats",  cmd_stats))
    app.add_handler(add_conv)
    app.add_handler(search_conv)
    app.add_handler(CallbackQueryHandler(cb_delete, pattern="^del_"))
    app.add_handler(MessageHandler(filters.Regex("📋 Мои"),   cmd_my_listings))
    app.add_handler(MessageHandler(filters.Regex("📊 Стат"),  cmd_stats))
    app.add_handler(MessageHandler(filters.Regex("ℹ️ О нас"), cmd_about))
    app.add_handler(MessageHandler(filters.Regex("📞 Связ"),  cmd_contact))
    logger.info("🚀 ESTA Bot v4.0 запущен!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
