import os
import asyncio
import feedparser
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes

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
sent_links = set()

async def send_message_chunks(text: str):
    MAX_LEN = 4000  # un po' sotto i 4096 per sicurezza
    chunks = []
    while text:
        chunk = text[:MAX_LEN]
        # Cerca di non spezzare nel mezzo di un link o parola
        last_newline = chunk.rfind('\n')
        if last_newline > 100:
            chunk = chunk[:last_newline]
        chunks.append(chunk)
        text = text[len(chunk):]
    for chunk in chunks:
        await bot.send_message(chat_id=CHAT_ID, text=chunk, parse_mode="HTML")
        await asyncio.sleep(0.5)  # piccolo delay per sicurezza

async def send_news_periodically():
    await asyncio.sleep(10)
    while True:
        try:
            messages = []
            new_links = set()
            for url in RSS_URLS:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    title = entry.get("title", "Nessun titolo")
                    link = entry.get("link", "")
                    if link and link not in sent_links:
                        messages.append(f"<b>{title}</b>\n{link}")
                        new_links.add(link)

            if messages:
                # Se è troppo lungo, puoi spezzare in più messaggi, oppure limitare le news qui
                text = "\n\n".join(messages)
                await send_message_chunks(text)
                sent_links.update(new_links)
            else:
                await bot.send_message(chat_id=CHAT_ID, text="Nessuna news nuove da inviare.")

        except Exception as e:
            error_msg = f"Errore durante fetch o invio news: {e}"
            print(error_msg)
            await bot.send_message(chat_id=CHAT_ID, text=error_msg)

        await asyncio.sleep(900)

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

