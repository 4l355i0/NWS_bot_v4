import logging
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import openai

# Configura il logging
logging.basicConfig(level=logging.INFO)

# Inserisci qui il tuo token bot Telegram e la chiave OpenAI
TELEGRAM_TOKEN = 'your-telegram-bot-token'
OPENAI_API_KEY = 'your-openai-api-key'

openai.api_key = OPENAI_API_KEY

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Sono il tuo bot di notizie.")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content": user_text}]
    )
    reply = response['choices'][0]['message']['content']
    await update.message.reply_text(reply)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("echo", echo))
    app.run_polling()
