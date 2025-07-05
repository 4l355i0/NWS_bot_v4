import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import openai

# Carica token da variabili ambiente
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Controllo di sicurezza
if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise ValueError("TELEGRAM_TOKEN or OPENAI_API_KEY not set in environment variables")

openai.api_key = OPENAI_API_KEY

# Configura logging
logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Ciao! Sono il tuo bot di notizie. Inviami una domanda per ricevere la sintesi con GPT.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-preview",
            messages=[{"role": "user", "content": user_text}],
            max_tokens=300
        )
        reply = response['choices'][0]['message']['content']
    except Exception as e:
        reply = f"Errore nella chiamata a OpenAI: {str(e)}"
    await update.message.reply_text(reply)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("echo", echo))
    app.run_polling()
