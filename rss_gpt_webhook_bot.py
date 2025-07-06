import os
import asyncio
import feedparser
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes

seen_links = set()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TELEGRAM_TOKEN or not CHAT_ID or not WEBHOOK_URL:
    raise ValueError("Manca TELEGRAM_TOKEN, CHAT_ID o WEBHOOK_URL nelle env variables")

CHAT_ID = int(CHAT_ID)

app = FastAPI()
bot = Bot(token=TELEGRAM_TOKEN)
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

RSS_URLS = [
    "https://www.repubblica.it/rss/homepage/rss2.0.xml",
    "https://www.ansa.it/sito/ansait_rss.xml",
    "https://www.corriere.it/rss/homepage.xml",
    # ... aggiungi altri feed che vuoi
]

# Per evitare duplicati, teniamo un set in memoria

async def send_news_periodically():
    await asyncio.sleep(10)  # attesa all'avvio
    while True:
        try:
            messages = []
            for url in RSS_URLS:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    link = entry.get("link", "")
                    if link and link not in seen_links:
                        seen_links.add(link)
                        title = entry.get("title", "Nessun titolo")
                        messages.append(f"<b>{title}</b>\n{link}")
            
            # Dividi messaggi troppo lunghi (Telegram max 4096 char)
            if messages:
                chunk = []
                chunk_len = 0
                for msg in messages:
                    if chunk_len + len(msg) + 2 > 4000:  # buffer per sicurezza
                        text = "\n\n".join(chunk)
                        await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="HTML")
                        chunk = [msg]
                        chunk_len = len(msg) + 2
                    else:
                        chunk.append(msg)
                        chunk_len += len(msg) + 2
                if chunk:
                    text = "\n\n".join(chunk)
                    await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="HTML")

        except Exception as e:
            await bot.send_message(chat_id=CHAT_ID, text=f"Errore durante fetch o invio news: {e}")

        await asyncio.sleep(900)  # 15 minuti

@app.on_event("startup")
async def startup_event():
    await application.initialize()
    await application.start()
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

