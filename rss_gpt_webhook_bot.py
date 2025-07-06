import os
import asyncio
import aiohttp
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
    "https://www.ilmessaggero.it/rss/home.xml",
    "https://www.ilfattoquotidiano.it/feed/",
    "https://www.gazzetta.it/rss/home.xml",
    "https://www.ilsole24ore.com/rss/feed/sport.xml",
    "https://www.skysports.com/rss/12040",
    "https://www.cyclingnews.com/rss/news/",
    "https://www.velonews.com/feed/",
    "https://www.bikeradar.com/rss/news.xml",
    "https://aviationweek.com/rss.xml",
    "https://simpleflying.com/feed/",
    "https://www.flightglobal.com/feeds/rss",
    "https://rsshub.app/youtube/channel/UC_A--fhX5gea0i4UtpD99Gg",
    "https://rsshub.app/youtube/channel/UC-r_56iJkAF0nIeX-5dleRQ",
    
    # aggiungi altri RSS qui
]

async def fetch_feed(session, url):
    try:
        async with session.get(url, timeout=20) as response:
            content = await response.read()
            feed = feedparser.parse(content)
            return feed.entries
    except Exception as e:
        print(f"Errore fetch {url}: {e}")
        return []

async def send_news_periodically():
    await asyncio.sleep(10)  # attesa avvio
    while True:
        try:
            messages = []
            async with aiohttp.ClientSession() as session:
                tasks = [fetch_feed(session, url) for url in RSS_URLS]
                results = await asyncio.gather(*tasks)

                for entries in results:
                    for entry in entries:
                        link = entry.get("link", "")
                        if link and link not in seen_links:
                            seen_links.add(link)
                            title = entry.get("title", "Nessun titolo")
                            messages.append(f"<b>{title}</b>\n{link}")

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
                print(f"Inviate {len(messages)} notizie nuove.")
            else:
                print("Nessuna nuova notizia trovata.")

        except Exception as e:
            print(f"Errore generale durante fetch o invio news: {e}")
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


