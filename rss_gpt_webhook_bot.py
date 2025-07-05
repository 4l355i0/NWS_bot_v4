import os
import feedparser
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from openai import OpenAI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
USER_ID = os.getenv("USER_ID")  # il tuo telegram user id

if not TELEGRAM_TOKEN or not OPENAI_API_KEY or not WEBHOOK_URL or not USER_ID:
    raise ValueError("Missing TELEGRAM_TOKEN, OPENAI_API_KEY, WEBHOOK_URL or USER_ID in environment variables.")

openai = OpenAI(api_key=OPENAI_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)
app = FastAPI()
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
scheduler = AsyncIOScheduler()

RSS_FEEDS = [
    "https://www.ilfattoquotidiano.it/feed/",
    "https://www.repubblica.it/rss/homepage/rss2.0.xml",
    "https://www.corriere.it/rss/homepage.xml",
    "https://feeds.bbci.co.uk/news/rss.xml",
    "http://rss.cnn.com/rss/edition.rss",
    "https://www.aviationherald.com/rss.xml",
    "https://www.eventim.de/rss/new-events.rss",
    "https://www.ticketmaster.com/rss/new-events.rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://www.globalcyclingnetwork.com/rss",
    "https://www.formula1.com/content/fom-website/en/latest/all.xml",
]

sent_titles = set()

async def generate_gpt_summary(content: str) -> str:
    response = openai.chat.completions.create(
        model="gpt-4o-preview",
        messages=[
            {"role": "system", "content": "Sintetizza la notizia in 5 righe con 3 takeaway chiari in italiano."},
            {"role": "user", "content": content}
        ]
    )
    return response.choices[0].message.content.strip()

async def fetch_and_send_news():
    global sent_titles
    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)
        for entry in feed.entries[:2]:  # prendi max 2 notizie per feed
            if entry.title not in sent_titles:
                sent_titles.add(entry.title)
                content = f"Titolo: {entry.title}\nLink: {entry.link}\nDescrizione: {entry.get('summary', '')}"
                try:
                    summary = await generate_gpt_summary(content)
                    message = f"📰 <b>{entry.title}</b>\n{entry.link}\n\n{summary}"
                    await bot.send_message(chat_id=USER_ID, text=message, parse_mode='HTML')
                except Exception as e:
                    print(f"Errore durante la sintesi o invio notizia '{entry.title}': {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Sono il tuo bot GPT per le news.")

application.add_handler(CommandHandler("start", start))

@app.on_event("startup")
async def on_startup():
    await bot.delete_webhook()
    await bot.set_webhook(WEBHOOK_URL)
    scheduler.add_job(fetch_and_send_news, 'interval', hours=2)
    scheduler.start()

@app.post("/")
async def telegram_webhook(request: Request):
    json_data = await request.json()
    update = Update.de_json(json_data, bot)
    await application.update_queue.put(update)
    await application.process_update(update)
    return {"ok": True}
