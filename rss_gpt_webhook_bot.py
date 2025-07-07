import os
import asyncio
import feedparser
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder
import json
import time
from datetime import datetime, timedelta

seen_links_file = "seen_links.json"

# Carica seen_links da file se esiste
if os.path.exists(seen_links_file):
    with open(seen_links_file, "r") as f:
        seen_links = set(json.load(f))
else:
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

# i tuoi RSS qui
RSS_URLS = [
    "https://www.repubblica.it/rss/homepage/rss2.0.xml",
    "https://www.ansa.it/sito/ansait_rss.xml",
    "https://www.corriere.it/rss/homepage.xml",
    # altri...
]

async def send_news_periodically():
    await asyncio.sleep(10)
    while True:
        try:
            messages = []
            now = datetime.utcnow()
            yesterday = now - timedelta(days=1)
            new_links = set()

            for url in RSS_URLS:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    link = entry.get("link", "")
                    if not link or link in seen_links:
                        continue

                    # Controlla data pubblicazione
                    published = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        published = datetime.fromtimestamp(time.mktime(entry.published_parsed))
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        published = datetime.fromtimestamp(time.mktime(entry.updated_parsed))
                    
                    if published is None or published < yesterday:
                        continue

                    title = entry.get("title", "Nessun titolo")
                    messages.append(f"<b>{title}</b>\n{link}")
                    new_links.add(link)

            # Salva i nuovi link per persistenza
            seen_links.update(new_links)
            with open(seen_links_file, "w") as f:
                json.dump(list(seen_links), f)

            # Invio messaggi
            if messages:
                chunk = []
                chunk_len = 0
                for msg in messages:
                    if chunk_len + len(msg) + 2 > 4000:
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

                # Log per debug
                await bot.send_message(chat_id=CHAT_ID, text=f"✅ Inviate {len(messages)} notizie.")

            else:
                await bot.send_message(chat_id=CHAT_ID, text="Nessuna nuova notizia nelle ultime 24h.")

        except Exception as e:
            await bot.send_message(chat_id=CHAT_ID, text=f"Errore durante fetch o invio news: {e}")

        await asyncio.sleep(900)  # 15 min

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


