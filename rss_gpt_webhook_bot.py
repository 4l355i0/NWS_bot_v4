import os
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import openai

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY or not WEBHOOK_URL:
    raise ValueError("Missing TELEGRAM_TOKEN, OPENAI_API_KEY, or WEBHOOK_URL in environment variables.")

openai.api_key = OPENAI_API_KEY
bot = Bot(token=TELEGRAM_TOKEN)
app = FastAPI()
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Sono il tuo bot GPT per le news.")

application.add_handler(CommandHandler("start", start))

@app.on_event("startup")
async def on_startup():
    await bot.initialize()                # <-- qui inizializzi il bot
    await application.initialize()
    await application.start()
    await bot.delete_webhook()
    await bot.set_webhook(WEBHOOK_URL)

@app.on_event("shutdown")
async def on_shutdown():
    await application.stop()
    await application.shutdown()
    await bot.close()                     # <-- chiudi il bot correttamente

@app.post("/")
async def telegram_webhook(request: Request):
    json_data = await request.json()
    update = Update.de_json(json_data, bot)
    await application.update_queue.put(update)
    await application.process_update(update)
    return {"ok": True}
