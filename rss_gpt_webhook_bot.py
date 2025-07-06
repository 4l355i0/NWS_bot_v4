import os
import asyncio
import feedparser
import pickle
import time
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder

# ====== CONFIG =======
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if not TELEGRAM_TOKEN or not CHAT_ID or not WEBHOOK_URL:
    raise ValueError("Manca TELEGRAM_TOKEN, CHAT_ID o WEBHOOK_URL nelle env variables")

CHAT_ID = int(CHAT_ID)
bot = Bot(token=TELEGRAM_TOKEN)

app = FastAPI()
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

RSS_URLS = [
    "https://www.repubblica.it/rss/homepage/rss2.0.xml",
    "https://www.ansa.it/sito/ansait_rss.xml",
    "https://www.corriere.it/rss/homepage.xml",
    # aggiungi altri feed
]

SEEN_LINKS_FILE = "seen_links.pkl"
try:
    with open(SEEN_LINKS_FILE, "rb") as f:
        seen_links = pickle.load(f)
except FileNotFoundError:
    seen_links = set()

# ====== FUNZIONE DI INVIO =======
async def send_news_periodically():
    await asyncio.sleep(10)
    while True:
        try:
            now = time.time()
            new_messages = []

            for url in RSS_URLS:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    link = entry.get("link", "")
                    title = entry.get("title", "Nessun titolo")
                    published = entry.get("published_parsed")

                    if link and link not in seen_links:
                        if published:
                            published_time = time.mktime(published)
                            if now - published_time > 60 * 60 * 24:  # ignoriamo articoli più vecchi di 24h
                                continue
                        seen_links.add(link)
                        new_messages.append(f"<b>{title}</b>\n{link}")

            # Salva lo stato dei link visti
            with open(SEEN_LINKS_FILE, "wb") as f:
                pickle.dump(seen_links, f)

            # Invio in blocchi gestendo lunghezza massima
            if new_messages:
                chunk = []
                chunk_len = 0
                for msg in new_messages:
                    if chunk_len + len(msg) + 2 > 4000:
                        text = "\n\n".join(chunk)
                        await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="HTML", disable_web_page_preview=True)
                        chunk = [msg]
                        chunk_len = len(msg) + 2
                    else:
                        chunk.append(msg)
                        chunk_len += len(msg) + 2
                if chunk:
                    text = "\n\n".join(chunk)
                    await bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="HTML", disable_web_page_preview=True)

        except Exception as e:
            await bot.send_message(chat_id=CHAT_ID, text=f"Errore fetch news: {e}")

        await asyncio.sleep(900)  # ogni 15 minuti

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

