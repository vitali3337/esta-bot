import os
import re
import time
import logging
import requests

from telegram import (
    ReplyKeyboardMarkup, Update,
    InlineKeyboardButton, InlineKeyboardMarkup,
    InputMediaPhoto
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters, CallbackQueryHandler
)

# ========= CONFIG =========
TOKEN         = os.getenv("BOT_TOKEN")
API_URL       = os.getenv("API_URL", "")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY= os.getenv("OPENAI_API_KEY", "")
MANAGER_ID    = int(os.getenv("MANAGER_ID", "5705817827"))

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("esta_bot")

# ========= SAMPLE DATA (если API недоступен) =========
SAMPLE = [
    {"id":"1","title":"2-комнатная квартира, центр","city":"Тирасполь","district":"Центр","deal_type":"sale","type":"apartment","price":38000,"rooms":2,"area":54.5,"views":127,"photos":[],"desc":"Светлая квартира, хороший ремонт."},
    {"id":"2","title":"3-комнатная, ул. Ленина","city":"Тирасполь","district":"Ленинский р-н","deal_type":"sale","type":"apartment","price":52000,"rooms":3,"area":74,"views":89,"photos":[],"desc":"Просторная, кухня 12м², лоджия. Торг."},
    {"id":"3","title":"1-комнатная в аренду","city":"Тирасполь","district":"Красный Октябрь","deal_type":"rent","type":"apartment","price":200,"rooms":1,"area":35,"views":213,"photos":[],"desc":"Меблирована, вся техника."},
    {"id":"4","title":"Дом 120м², участок 10 соток","city":"Слободзея","district":"","deal_type":"sale","type":"house","price":45000,"rooms":4,"area":120,"views":54,"photos":[],"desc":"Кирпичный дом, гараж, баня, колодец."},
    {"id":"5","title":"Дача в Тирасполе, 6 соток","city":"Тирасполь","district":"Зелёный мир","deal_type":"sale","type":"house","price":18000,"rooms":2,"area":45,"views":41,"photos":[],"desc":"Дача с домиком, сад, огород."},
    {"id":"6","title":"Офис в аренду, центр 45м²","city":"Тирасполь","district":"Центр","deal_type":"rent","type":"commercial","price":350,"rooms":None,"area":45,"views":67,"photos":[],"desc":"Деловой центр, парковка, охрана."},
    {"id":"7","title":"2-комнатная, Ботаника","city":"Кишинёв","district":"Ботаника","deal_type":"sale","type":"apartment","price":95000,"rooms":2,"area":68,"views":188,"photos":[],"desc":"Евроремонт, встроенная кухня, паркинг."},
    {"id":"8","title":"Дом в Бендерах, 150м²","city":"Бендеры","district":"","deal_type":"sale","type":"house","price":55000,"rooms":5,"area":150,"views":33,"photos":[],"desc":"Газ, вода, канализация, фруктовый сад."},
    {"id":"9","title":"Студия в аренду, центр","city":"Тирасполь","district":"Центр","deal_type":"rent","type":"apartment","price":180,"rooms":1,"area":28,"views":301,"photos":[],"desc":"Дизайнерский ремонт, панорамный вид."},
    {"id":"10","title":"Участок 6 соток, Дубоссары","city":"Дубоссары","district":"","deal_type":"sale","type":"land","price":8000,"rooms":None,"area":600,"views":22,"photos":[],"desc":"Ровный участок под строительство."},
    {"id":"11","title":"4-комнатная, элитный ЖК","city":"Тирасполь","district":"Центр","deal_type":"sale","type":"apartment","price":89000,"rooms":4,"area":115,"views":156,"photos":[],"desc":"Консьерж, паркинг, закрытая территория."},
    {"id":"12","title":"1-комнатная, новостройка","city":"Рыбница","district":"","deal_type":"sale","type":"apartment","price":22000,"rooms":1,"area":42,"views":45,"photos":[],"desc":"Новостройка 2020 года, черновая отделка."},
]

# ========= LOCAL NLU — никогда не падает =========
def local_search(query: str) -> tuple:
    q = query.lower()

    # Тип сделки
    deal = "rent" if any(w in q for w in ["аренд","снять","сниму","rent"]) else "sale"

    # Город
    city = None
    for key, val in {
        "тирасполь":"Тирасполь","тирасполе":"Тирасполь","тирасполя":"Тирасполь",
        "кишинёв":"Кишинёв","кишинев":"Кишинёв","кишинёве":"Кишинёв","кишиневе":"Кишинёв",
        "бендер":"Бендеры","бендеры":"Бендеры",
        "рыбниц":"Рыбница","дубоссар":"Дубоссары",
        "слободзе":"Слободзея","бельц":"Бельцы",
    }.items():
        if key in q:
            city = val
            break

    # Тип объекта
    prop_type = None
    if any(w in q for w in ["квартир","апартамент","студи"]):
        prop_type = "apartment"
    elif any(w in q for w in ["дач"]):          # "дача" → house (ЭТО БЫЛ БАГ)
        prop_type = "house"
    elif any(w in q for w in ["дом","коттедж"]):
        prop_type = "house"
    elif any(w in q for w in ["участок","земл","соток"]):
        prop_type = "land"
    elif any(w in q for w in ["офис","магазин","коммерц"]):
        prop_type = "commercial"
    elif "гараж" in q:
        prop_type = "garage"

    # Комнаты
    rooms = None
    for key, val in {
        "однокомнат":1,"1-комнат":1,"двухкомнат":2,
        "2-комнат":2,"трёхкомнат":3,"трехкомнат":3,"3-комнат":3,
    }.items():
        if key in q:
            rooms = val
            break

    # Цена — первое число > 100 в запросе
    max_price = None
    for m in re.finditer(r"\d[\d\s]*", q):
        try:
            n = int(m.group().replace(" ",""))
            if n > 100:
                max_price = n
                break
        except ValueError:
            pass

    # Сначала пробуем backend API
    props = []
    try:
        if API_URL:
            params = {"deal_type": deal, "per_page": 5}
            if city:       params["city"]      = city
            if prop_type:  params["type"]      = prop_type
            if rooms:      params["rooms"]     = rooms
            if max_price:  params["max_price"] = max_price
            r = requests.get(f"{API_URL}/api/v1/listings", params=params, timeout=5)
            data = r.json()
            props = data.get("data", {}).get("items", []) or data.get("items", [])
    except Exception as e:
        log.warning(f"Backend API unavailable: {e}")

    # Фолбэк на SAMPLE если API не дал результатов
    if not props:
        for l in SAMPLE:
            if l["deal_type"] != deal:                       continue
            if city      and city      not in l["city"]:     continue
            if prop_type and l["type"] != prop_type:         continue
            if rooms     and l.get("rooms") != rooms:        continue
            if max_price and l["price"] > max_price:         continue
            props.append(l)

    # Ответ
    if props:
        parts = list(filter(None, [
            f"📍 {city}"      if city      else None,
            {"apartment":"🏢 Квартира","house":"🏡 Дом/Дача","land":"🌿 Участок",
             "commercial":"🏪 Коммерция"}.get(prop_type,"") if prop_type else None,
            f"🛏 {rooms} комн." if rooms     else None,
            f"💰 до {max_price:,} $".replace(",","_") if max_price else None,
        ]))
        reply = f"🔍 Нашёл *{len(props)}* вариантов\n_{'  ·  '.join(parts)}_"
    else:
        reply = (
            "😔 По запросу ничего не найдено.\n\n"
            "Попробуй:\n"
            "• _Тирасполь, квартира, 40000_\n"
            "• _дом Слободзея_\n"
            "• _снять 1к в центре_"
        )

    return props[:5], reply


# ========= CLAUDE AI (если есть ключ) =========
async def ai_search(query: str) -> tuple:
    """Claude API → local NLU fallback. Никогда не падает."""
    if not ANTHROPIC_KEY:
        return local_search(query)
    try:
        import aiohttp, json as _json
        db = "\n".join(
            f"id:{l['id']}|{l['title']}|{l['city']}|{l['type']}|{l['deal_type']}|{l['price']}$"
            for l in SAMPLE
        )
        sys_prompt = (
            f"Ты — AI-ассистент ESTA Realty. База:\n{db}\n"
            f'Отвечай ТОЛЬКО JSON: {{"matched_ids":[],"explanation":""}}'
        )
        async with aiohttp.ClientSession() as sess:
            async with sess.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key":ANTHROPIC_KEY,"anthropic-version":"2023-06-01","content-type":"application/json"},
                json={"model":"claude-sonnet-4-20250514","max_tokens":300,
                      "system":sys_prompt,"messages":[{"role":"user","content":query}]},
                timeout=aiohttp.ClientTimeout(total=12),
            ) as resp:
                raw = await resp.json()
                parsed = _json.loads(raw["content"][0]["text"].strip())
                matched = set(parsed.get("matched_ids",[]))
                props = [l for l in SAMPLE if l["id"] in matched]
                exp = parsed.get("explanation","")
                reply = f"🤖 *Claude нашёл {len(props)} вариантов*\n_{exp}_" if props else "😔 Ничего не найдено."
                return props, reply
    except Exception as e:
        log.warning(f"Claude failed ({e}), using local NLU")
        return local_search(query)


# ========= UI =========
def main_menu():
    return ReplyKeyboardMarkup([
        ["🏠 Купить", "🔑 Аренда"],
        ["➕ Продать", "🏦 Ипотека"],
        ["📞 Связаться"]
    ], resize_keyboard=True)


def build_card(p: dict) -> str:
    price = f"{p.get('price',0):,}".replace(",", " ")
    sfx   = "/мес" if p.get("deal_type") == "rent" else ""
    rooms = f"{p.get('rooms')}к | " if p.get("rooms") else ""
    loc   = p.get("city","—")
    if p.get("district"):
        loc += f", {p['district']}"
    return (
        f"🏠 *{p.get('title')}*\n"
        f"📍 {loc}\n"
        f"💰 *{price} ${sfx}* | {rooms}{p.get('area','')} м²\n"
        f"👁 {p.get('views',0)} просмотров · 🆔 #{p.get('id')}\n"
        f"_{p.get('desc','')}_"
    )


def card_buttons(p: dict):
    row = []
    if API_URL:
        row.append(InlineKeyboardButton("👀 На сайте", url=f"{API_URL}/property/{p.get('id')}"))
    row.append(InlineKeyboardButton("📩 Заявка", callback_data=f"lead_{p.get('id')}"))
    return InlineKeyboardMarkup([row])


async def send_property(update: Update, ctx: ContextTypes.DEFAULT_TYPE, p: dict):
    photos = p.get("photos") or []
    if photos:
        try:
            await ctx.bot.send_media_group(
                chat_id=update.effective_chat.id,
                media=[InputMediaPhoto(u) for u in photos[:3]]
            )
        except Exception:
            pass
    await update.message.reply_text(
        build_card(p), reply_markup=card_buttons(p), parse_mode="Markdown"
    )


def is_phone(text: str) -> bool:
    clean = re.sub(r"[\s\-()]", "", text)
    return bool(re.match(r"^\+?[\d]{7,15}$", clean))


def send_lead_to_api(phone: str, listing_id: str = None):
    try:
        requests.post(f"{API_URL}/lead",
                      json={"phone": phone, "listing_id": listing_id},
                      timeout=5)
    except Exception:
        pass


def create_property_api(data: dict):
    try:
        return requests.post(f"{API_URL}/property", json=data, timeout=5).json()
    except Exception:
        return {}


# ========= STATE =========
user_state = {}


# ========= HANDLERS =========
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_state.pop(update.effective_user.id, None)
    await update.message.reply_text(
        "🏠 *ESTA Недвижимость*\n\nЧто ищешь?",
        reply_markup=main_menu(), parse_mode="Markdown",
    )


async def handle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data or ""
    uid  = q.from_user.id

    if data.startswith("vip_"):
        await q.message.reply_text("🚀 VIP подключим — свяжитесь с менеджером")

    elif data.startswith("lead_"):
        listing_id = data[5:]
        user_state[uid] = {"step": "phone", "listing_id": listing_id}
        listing = next((l for l in SAMPLE if l["id"] == listing_id), None)
        title = listing["title"] if listing else "объект"
        await q.message.reply_text(
            f"📩 *Заявка на:* _{title}_\n\nОставь номер — агент перезвонит:",
            parse_mode="Markdown",
        )


async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid   = update.effective_user.id
    text  = (update.message.text or "").strip()
    state = user_state.get(uid, {})

    try:
        # ── Ожидаем телефон ──────────────────────────────────
        if state.get("step") == "phone":
            if is_phone(text):
                listing_id = state.get("listing_id")
                listing    = next((l for l in SAMPLE if l["id"] == listing_id), None)

                msg = f"🔥 *ГОРЯЧИЙ ЛИД*\n📞 {text}"
                if listing:
                    msg += f"\n🏠 {listing['title']}\n📍 {listing['city']}\n💰 {listing['price']:,} $"

                try:
                    await ctx.bot.send_message(MANAGER_ID, msg, parse_mode="Markdown")
                except Exception as e:
                    log.error(f"Cannot notify manager: {e}")

                send_lead_to_api(text, listing_id)

                await update.message.reply_text(
                    "✅ *Спасибо! Мы скоро свяжемся.*",
                    parse_mode="Markdown", reply_markup=main_menu(),
                )
                user_state.pop(uid, None)
            else:
                await update.message.reply_text(
                    "📞 Введи корректный номер\nНапример: *+373 69 123456*",
                    parse_mode="Markdown",
                )
            return

        # ── Кнопки ───────────────────────────────────────────
        if text == "🏠 Купить":
            user_state[uid] = {"step": "search", "deal": "sale"}
            await update.message.reply_text(
                "🏠 *Покупка*\n\nНапиши запрос: город, тип, бюджет 👇\n\n"
                "Например: _Тирасполь, дача, 25000_",
                parse_mode="Markdown",
            )
            return

        if text == "🔑 Аренда":
            user_state[uid] = {"step": "search", "deal": "rent"}
            await update.message.reply_text(
                "🔑 *Аренда*\n\nНапиши: город и бюджет 👇\n\n"
                "Например: _снять квартиру Тирасполь до 300$_",
                parse_mode="Markdown",
            )
            return

        if text == "🏦 Ипотека":
            await update.message.reply_text(
                "🏦 *Ипотека*\n\nНапиши доход и бюджет — подберу варианты",
                parse_mode="Markdown",
            )
            return

        if text == "📞 Связаться":
            user_state[uid] = {"step": "phone"}
            await update.message.reply_text("📞 Оставь номер телефона 👇")
            return

        # ── Продать: форма ───────────────────────────────────
        if text == "➕ Продать":
            user_state[uid] = {"step": "title"}
            await update.message.reply_text("✏️ *Введите заголовок:*", parse_mode="Markdown")
            return

        if state.get("step") == "title":
            user_state[uid] = {"step": "price", "title": text}
            await update.message.reply_text("💰 *Введите цену (только цифры):*", parse_mode="Markdown")
            return

        if state.get("step") == "price":
            price_str = re.sub(r"[^\d]", "", text)
            if not price_str or not price_str.isdigit():
                await update.message.reply_text("⚠️ Введи цену цифрами, например: *45000*", parse_mode="Markdown")
                return
            create_property_api({"title": state.get("title",""), "price": int(price_str), "deal_type": "sale"})
            await update.message.reply_text("✅ *Объявление добавлено!*", parse_mode="Markdown", reply_markup=main_menu())
            user_state.pop(uid, None)
            return

        # ── AI поиск ─────────────────────────────────────────
        if len(text) >= 3:
            thinking = await update.message.reply_text("🔍 Ищу подходящие варианты...")

            props, reply = await ai_search(text)

            try:
                await thinking.delete()
            except Exception:
                pass

            if props:
                await update.message.reply_text(reply, parse_mode="Markdown")
                for p in props[:3]:
                    await send_property(update, ctx, p)
                await update.message.reply_text("Хочешь узнать подробнее? Оставь номер 👇")
                user_state[uid] = {"step": "phone"}
            else:
                await update.message.reply_text(reply, parse_mode="Markdown")
            return

        await update.message.reply_text("Что ищешь?", reply_markup=main_menu())

    except Exception as e:
        log.error(f"Handler error uid={uid} text='{text}': {e}", exc_info=True)
        await update.message.reply_text("⚠️ Что-то пошло не так. Попробуй ещё раз.", reply_markup=main_menu())


# ========= MAIN =========
def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN is required")

    try:
        requests.get(f"https://api.telegram.org/bot{TOKEN}/deleteWebhook", timeout=5)
        time.sleep(1)
    except Exception:
        pass

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT, handle))

    log.info("ESTA AI BOT STARTED")
    log.info(f"Claude AI: {'ON' if ANTHROPIC_KEY else 'OFF (local NLU)'}")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
