import os
import asyncio
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import feedparser

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
USER_ID = int(os.getenv("CHAT_ID"))

if not TELEGRAM_TOKEN or not USER_ID:
    raise ValueError("TELEGRAM_TOKEN or CHAT_ID non settati")

app = FastAPI()
bot = Bot(token=TELEGRAM_TOKEN)
application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

RSS_URLS = [
    "https://www.repubblica.it/rss/homepage/rss2.0.xml",
    "https://www.ansa.it/sito/ansait_rss.xml",
    "https://www.corriere.it/rss/homepage.xml",
    "https://www.lastampa.it/rss.xml",
    "https://www.ilsole24ore.com/rss/feed/home.xml",
    "https://tg24.sky.it/rss.xml",
    "https://www.ilgiornale.it/rss.xml",
    "https://www.tgcom24.mediaset.it/rss/homepage.xml",
    "https://www.rainews.it/dl/rainews/rss.xml",
    "https://www.adnkronos.com/rss/home.xml",
    "https://www.ilmessaggero.it/rss/home.xml",
    "https://www.fanpage.it/rss",
    "https://www.quotidiano.net/rss",
    "https://www.ilfattoquotidiano.it/feed/",
    "https://www.ilmanifesto.it/feed/",
    # aggiungi altri RSS qui
]

sent_articles = set()

async def send_news():
    while True:
        print("Controllo feed RSS...")
        new_messages = []
        for url in RSS_URLS:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    unique_id = entry.get('id') or entry.get('link')
                    if unique_id and unique_id not in sent_articles:
                        sent_articles.add(unique_id)
                        title = entry.get('title', 'No Title')
                        link = entry.get('link', '')
                        new_messages.append(f"<b>{title}</b>\n{link}")
            except Exception as e:
                print(f"Errore durante il parsing del feed {url}: {e}")

        if new_messages:
            news_text = "\n\n".join(new_messages)
            try:
                # Suddivisione in chunk di max 4000 caratteri
                max_length = 4000
                parts = [news_text[i:i+max_length] for i in range(0, len(news_text), max_length)]
                for idx, part in enumerate(parts):
                    await bot.send_message(chat_id=USER_ID, text=part, parse_mode='HTML')
                    print(f"Inviato chunk {idx + 1}/{len(parts)}")
                print(f"Inviati {len(new_messages)} nuovi articoli.")
            except Exception as e:
                print(f"Errore invio news: {e}")
        else:
            print("Nessun nuovo articolo trovato.")
            try:
                await bot.send_message(chat_id=USER_ID, text="Controllo fatto: nessun nuovo articolo da inviare.")
            except Exception as e:
                print(f"Errore invio messaggio di check: {e}")

        await asyncio.sleep(15 * 60)  # 15 minuti

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Sono il tuo bot GPT per le news.")

application.add_handler(CommandHandler("start", start))

@app.on_event("startup")
async def on_startup():
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    await bot.send_message(chat_id=USER_ID, text="BOT avviato e pronto a mandarti notizie ogni 15 minuti")
    asyncio.create_task(send_news())

@app.post("/")
async def telegram_webhook(request: Request):
    json_data = await request.json()
    update = Update.de_json(json_data, bot)
    await application.update_queue.put(update)
    await application.process_update(update)
    return {"ok": True}
