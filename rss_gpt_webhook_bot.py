import os
import asyncio
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import openai

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
USER_ID = int(os.getenv("CHAT_ID"))  # il tuo telegram user id

if not TELEGRAM_TOKEN or not OPENAI_API_KEY or not WEBHOOK_URL or not USER_ID:
    raise ValueError("Missing environment variables")

openai.api_key = OPENAI_API_KEY
bot = Bot(token=TELEGRAM_TOKEN)
app = FastAPI()
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Ti invierò le news ogni 15 minuti.")

application.add_handler(CommandHandler("start", start))

async def fetch_and_summarize_news():
    # Simulazione notizie
    sample_news = "Ultime notizie: esempio di notizia molto interessante."
    summary = sample_news + "\n\nTakeaway:\n1. Punto 1\n2. Punto 2\n3. Punto 3"
    return summary

async def news_loop():
    # Test iniziale per confermare connessione
    await bot.send_message(chat_id=USER_ID, text="✅ Bot avviato e pronto a inviarti le news ogni 15 minuti!")
    
    while True:
        message = await fetch_and_summarize_news()
        await bot.send_message(chat_id=USER_ID, text=message, parse_mode='HTML')
        await asyncio.sleep(900)  # 900 secondi = 15 minuti

@app.on_event("startup")
async def on_startup():
    await bot.delete_webhook()
    await bot.set_webhook(WEBHOOK_URL)
    asyncio.create_task(news_loop())

@app.post("/")
async def telegram_webhook(request: Request):
    json_data = await request.json()
    update = Update.de_json(json_data, bot)
    await application.update_queue.put(update)
    await application.process_update(update)
    return {"ok": True}
