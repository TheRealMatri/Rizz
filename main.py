import asyncio
from aiohttp import web, ClientSession
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, MessageHandler, filters,
    ContextTypes, CommandHandler, CallbackQueryHandler
)
from PIL import Image
import pytesseract
import requests

# Tokens & API keys
BOT_TOKEN = "8099304831:AAEd1J_q-DFcJCMPksYnTXbcF9D6ohNyv4Q"
OPENROUTER_API_KEY = "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"

# User state
user_chats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне скриншот переписки, и я помогу тебе с рилзовым ответом 😉")

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_path = f"{user_id}_chat.png"
    await file.download_to_drive(file_path)

    text = pytesseract.image_to_string(Image.open(file_path), lang="rus")
    user_chats[user_id] = text.strip()

    keyboard = [
        [InlineKeyboardButton("💬 Лёгкий рилз", callback_data="small")],
        [InlineKeyboardButton("🔥 Средний рилз", callback_data="medium")],
        [InlineKeyboardButton("💦 Супер рилз", callback_data="super")]
    ]

    await update.message.reply_text(
        "Выбери уровень рилза:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    level = query.data
    convo = user_chats.get(user_id, "")

    style = {
        "small": "Лёгкий, игривый и милый флирт",
        "medium": "Немного пошлый, игривый и уверенный флирт",
        "super": "Дерзкий, пошлый, сексуальный флирт, вызывающий возбуждение"
    }[level]

    prompt = f"""
Ты — мастер флирта. Тебе дан диалог между парнем и девушкой на русском языке.

Диалог:
{convo}

Создай один короткий, флиртующий, {style.lower()} ответ от парня, чтобы продолжить разговор. Ответ должен быть на русском языке и в том же тоне.
"""

    response = query_llm(prompt)
    await query.message.reply_text(f"💬 Твой рилз:\n\n{response.strip()}")

    # Ask for new screenshot again
    await query.message.reply_text("Если хочешь ещё — отправь следующий скриншот переписки! 😈")

def query_llm(prompt):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "google/gemma-3-12b-it:free",
        "messages": [{"role": "user", "content": prompt}]
    }

    res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
    return res.json()["choices"][0]["message"]["content"]


# --- KEEP ALIVE SETUP ---

async def handle_root(request):
    return web.Response(text="Bot is alive!")

async def keep_alive():
    async with ClientSession() as session:
        while True:
            try:
                await session.get("http://localhost:8080/")
            except Exception:
                pass
            await asyncio.sleep(180)  # 3 minutes

async def main():
    # Start aiohttp web server
    app_web = web.Application()
    app_web.add_routes([web.get("/", handle_root)])

    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

    # Start Telegram bot
    app_telegram = ApplicationBuilder().token(BOT_TOKEN).build()
    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(MessageHandler(filters.PHOTO, handle_image))
    app_telegram.add_handler(CallbackQueryHandler(button_handler))

    # Run keep_alive task in background
    asyncio.create_task(keep_alive())

    # Run telegram bot
    await app_telegram.run_polling()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
