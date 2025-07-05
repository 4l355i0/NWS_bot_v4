import os
import asyncio
import feedparser
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")  # il tuo telegram user id
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TELEGRAM_TOKEN or not CHAT_ID or not WEBHOOK_URL:
    raise ValueError("Manca TELEGRAM_TOKEN, CHAT_ID o WEBHOOK_URL nelle env variables")

CHAT_ID = int(CHAT_ID)

app = FastAPI()
bot = Bot(token=TELEGRAM_TOKEN)
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

RSS_FEEDS = [
    "https://www.repubblica.it/rss/homepage/rss2.0.xml",
    "https://rss.corriere.it/corriere-it/rss/homepage.xml",
    "https://www.rainews.it/rss/rainews-it.xml",
    "https://www.ansa.it/sito/ansait_rss.xml",
    "https://www.lastampa.it/rss/homepage.xml",
    "https://www.ilsole24ore.com/rss/rsshome.xml",
    "https://www.ilfattoquotidiano.it/feed/",
    "https://www.ilgiornale.it/rss.xml",
    "https://www.tgcom24.mediaset.it/rss/homepage.xml",
    "https://www.ilpost.it/feed/",
    "https://www.huffingtonpost.it/feeds/index.xml",
    "https://www.adnkronos.com/rss/",
    "https://www.affaritaliani.it/rss/rss.xml",
    "https://www.iltempo.it/rss.xml",
    "https://www.ilmanifesto.it/feed/",
    "https://www.avvenire.it/rss/feed.xml",
    "https://www.larepubblica.it/rss/rsshome.xml",
    "https://www.corriere.it/rss/homepage.xml",
    "https://www.tuttosport.com/rss/homepage.xml",
    "https://sport.sky.it/rss",
    "https://www.gazzetta.it/rss/homepage.xml",
    "https://www.ilsecoloxix.it/rss.xml",
    "https://www.ilmessaggero.it/rss.xml",
    "https://www.ilgiornaleditalia.org/feed/",
    "https://www.ilriformista.it/feed/",
    "https://www.ilfattoquotidiano.it/feed/",
    "https://www.ilfoglio.it/rss",
    "https://www.liberoquotidiano.it/rss.xml",
    "https://www.iltempo.it/rss.xml",
    "https://www.iltempo.it/rss.xml",
    "https://www.tg24.sky.it/rss",
    "https://www.ilpost.it/feed/",
    "https://www.repubblica.it/rss/homepage/rss2.0.xml",
    "https://www.lanuovasardegna.it/rss",
    "https://www.ilgiornale.it/rss.xml",
    "https://www.tgcom24.mediaset.it/rss/homepage.xml",
    "https://www.affaritaliani.it/rss/rss.xml",
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Ti invierò le news ogni 15 minuti.")

application.add_handler(CommandHandler("start", start))

@app.on_event("startup")
async def startup_event():
    await bot.delete_webhook()
    await bot.set_webhook(WEBHOOK_URL)
    asyncio.create_task(send_news_periodically())

@app.post("/")
async def telegram_webhook(request: Request):
    json_data = await request.json()
    update = Update.de_json(json_data, bot)
    await application.update_queue.put(update)
    await application.process_update(update)
    return {"ok": True}

async def send_news_periodically():
    await asyncio.sleep(10)  # aspetta un attimo all'avvio
    while True:
        try:
            messages = []
            for url in RSS_FEEDS:
                feed = feedparser.parse(url)
                if feed.entries:
                    entry = feed.entries[0]
                    title = entry.get("title", "Nessun titolo")
                    link = entry.get("link", "")
                    messages.append(f"<b>{title}</b>\n{link}")
            if messages:
                text = "\n\n".join(messages)
                await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="HTML")
        except Exception as e:
            print(f"Errore durante fetch o invio news: {e}")

        await asyncio.sleep(900)  # 15 minuti

