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
    "https://www.repubblica.it/rss/homepage/rss2.0.xml",
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
    "https://www.ansa.it/sito/ansait_rss_mondo.xml",
    "https://www.repubblica.it/esteri/rss2.0.xml",
    "https://www.corriere.it/esteri/rss.xml",
    "https://www.lastampa.it/esteri/rss.xml",
    "https://www.rainews.it/dl/rainews/rss_esteri.xml",
    "https://www.ilpost.it/feed/",
    "https://www.ilpost.it/feed/tecnologia/",
    "https://www.wired.it/feed/",
    "https://www.tomshw.it/feed/",
    "https://www.repubblica.it/sport/rss2.0.xml",
    "https://www.corriere.it/sport/rss.xml",
    "https://www.lastampa.it/sport/rss.xml",
    "https://www.gazzetta.it/rss/home.xml",
    "https://www.ilsole24ore.com/rss/feed/sport.xml",
    "https://www.rainews.it/dl/rainews/rss_sport.xml",
    "https://www.tgcom24.mediaset.it/sport/rss.xml",
    "https://www.lanazione.it/rss",
    "https://www.ansa.it/sito/ansait_rss_cultura.xml",
    "https://www.repubblica.it/cultura/rss2.0.xml",
    "https://www.corriere.it/cultura/rss.xml",
    "https://www.lastampa.it/cultura/rss.xml",
    "https://www.ilsole24ore.com/rss/feed/cultura.xml",
    "https://aviationweek.com/rss.xml",
    "https://simpleflying.com/feed/",
    "https://www.flightglobal.com/feeds/rss",
    "https://airlinegeeks.com/feed/",
    "https://thepointsguy.com/aviation/feed/",
    "https://www.airliners.net/news/rss",
    "https://www.avweb.com/feed/",
    "https://atwonline.com/rss.xml",
    "https://www.aerotime.aero/rss",
    "https://aviationweek.com/rss.xml",
    "https://simpleflying.com/feed/",
    "https://www.flightglobal.com/feeds/rss",
    "https://airlinegeeks.com/feed/",
    "https://thepointsguy.com/aviation/feed/",
    "https://www.airliners.net/news/rss",
    "https://www.avweb.com/feed/",
    "https://atwonline.com/rss.xml",
    "https://www.aerotime.aero/rss",
     "https://www.cyclingnews.com/rss/news/",
    "https://www.cyclingweekly.com/feed",
    "https://feeds.feedburner.com/VeloNews/RSS",
    "https://www.velonews.com/feed/",
    "https://www.bikeradar.com/rss/news.xml",
    "https://road.cc/feeds/news",
    "https://pezcyclingnews.com/feed/",
    "https://www.cxmagazine.com/feed",  # cyclocross
    "https://www.velonews.com/culture/feed/",
    "https://www.velonews.com/events/feed/",
    "https://www.velonews.com/gear/feed/",
    "https://www.globalcyclingnetwork.com/rss",  # se attivo
    "https://cycling.today/feed/",
    "https://www.bikeworldnews.com/feed/",
    "https://www.pinkbike.com/rss/feed/news/",
    "https://cycling-passion.com/feed/",
    "https://www.cyclist.co.uk/news/rss",
    "https://www.bicycling.com/rss/all.xml",
    "https://www.bicycling.com/rss/news.xml",
    "https://www.bicycling.com/rss/fitness.xml",
    # aggiungi qui tutti i tuoi RSS
]

# Set per tracciare gli articoli già inviati (puoi usare URL o id)
sent_articles = set()

async def send_news():
    while True:
        new_messages = []
        for url in RSS_URLS:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                unique_id = entry.get('id') or entry.get('link')
                if unique_id and unique_id not in sent_articles:
                    sent_articles.add(unique_id)
                    title = entry.get('title', 'No Title')
                    link = entry.get('link', '')
                    new_messages.append(f"<b>{title}</b>\n{link}")
        if new_messages:
            news_text = "\n\n".join(new_messages)
            try:
                await bot.send_message(chat_id=USER_ID, text=news_text, parse_mode='HTML')
            except Exception as e:
                print(f"Errore invio news: {e}")
        else:
            print("Nessun nuovo articolo trovato.")
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


