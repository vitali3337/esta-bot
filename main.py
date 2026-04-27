from api import create_property, search_property
from ai import ai_funnel

user_state = {}

async def handle(update, ctx):
    user_id = update.effective_user.id
    text = update.message.text

    # --- ДОБАВЛЕНИЕ ---
    if text == "➕ Подать":
        user_state[user_id] = {"step": "title"}
        await update.message.reply_text("Введите заголовок:")
        return

    if user_id in user_state:
        s = user_state[user_id]

        if s["step"] == "title":
            s["title"] = text
            s["step"] = "price"
            await update.message.reply_text("Цена:")
            return

        if s["step"] == "price":
            s["price"] = text

            create_property({
                "title": s["title"],
                "price": s["price"],
                "deal_type": "sale"
            })

            await update.message.reply_text("✅ Добавлено")
            user_state.pop(user_id)
            return

    # --- ПОИСК ---
    if "квартира" in text.lower():
        data = search_property({})

        for p in data[:3]:
            await update.message.reply_text(
                f"{p['title']}\n💰 {p['price']}"
            )
        return

    # --- AI ---
    reply = await ai_funnel(text)
    await update.message.reply_text(reply)
