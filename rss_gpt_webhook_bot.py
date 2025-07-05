import os
import logging
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

import openai

# Imposta logging
logging.basicConfig(level=logging.INFO)

# Recupera chiavi in sicurezza
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")  # Es: https://tuobot.onrender.com

if not TELEGRAM_TOKEN or not OPENAI_API_KEY or not WEBHOOK_URL:
    raise ValueError("Missing TELEGRAM_TOKEN, OPENAI_API_KEY, or WEBHOOK_URL in environment variables.")

# Configura OpenAI
openai.api_key = OPENAI_API_KEY

# Configura FastAPI
app = FastAPI()

# Configura bot Telegram
bot = Bot(token=TELEGRAM_TOKEN)
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Bot news GPT attivo via webhook!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4o-preview",
            messages=[{"role": "user", "content": user_text}],
            max_tokens=300
        )
        reply = completion.choices[0].message.content
    except Exception as e:
        reply = f"Errore GPT: {e}"
    await update.message.reply_text(reply)

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

# FastAPI endpoint per Telegram
@app.post("/")
async def webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot)
    await application.update_queue.put(update)
    return {"ok": True}

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(f"{WEBHOOK_URL}")

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()
