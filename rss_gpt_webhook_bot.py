import os
import asyncio
import feedparser
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

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
    "https://www.ilpost.it/feed/",
    "https://www.iltempo.it/rss.jsp",
    "https://www.ilfoglio.it/rss.jsp",
    "https://www.ilriformista.it/feed/",
    "https://www.huffingtonpost.it/feeds/index.xml",
    "http://feeds.bbci.co.uk/news/rss.xml",
    "http://rss.cnn.com/rss/edition.rss",
    "https://www.theguardian.com/world/rss",
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "https://feeds.washingtonpost.com/rss/world",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.reutersagency.com/feed/?best-topics=world&post_type=best",
    "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    "https://www.lemonde.fr/rss/une.xml",
    "https://www.elmundo.es/rss/portada.xml",
    "https://www.lefigaro.fr/rss/figaro_actualites.xml",
    "https://www.spiegel.de/international/index.rss",
    "https://www.dw.com/en/top-stories/s-9097/rss",
    "https://www.japantimes.co.jp/feed/",
    "https://www.hindustantimes.com/rss/topnews/rssfeed.xml",
    "https://www.smh.com.au/rss/feed.xml",
    "https://www.straitstimes.com/news/world/rss.xml",
    "https://www.bangkokpost.com/rss/data/topstories.xml",
    "https://english.alarabiya.net/.mrss/en.xml",
    "https://www.independent.co.uk/news/uk/rss",
    "https://www.gazzetta.it/rss/home.xml",
    "https://www.corriere.it/sport/rss.xml",
    "https://www.repubblica.it/sport/rss2.0.xml",
    "https://www.lastampa.it/sport/rss.xml",
    "https://www.tgcom24.mediaset.it/sport/rss.xml",
    "https://www.rainews.it/dl/rainews/rss_sport.xml",
    "https://www.ilsole24ore.com/rss/feed/sport.xml",
    "https://www.skysports.com/rss/12040",
    "http://www.espn.com/espn/rss/news",
    "https://www.sportingnews.com/us/rss",
    "https://www.goal.com/feeds/en/news",
    "https://www.olympic.org/news/rss",
    "https://www.marca.com/en/rss.xml",
    "https://www.lequipe.fr/rss/actu_rss.xml",
    "https://www.sportmediaset.mediaset.it/rss/rss-generale_1.xml",
    "https://www.bbc.co.uk/sport/0/football/rss.xml",
    "https://www.cyclingnews.com/rss/news/",
    "https://www.velonews.com/feed/",
    "https://www.bikeradar.com/rss/news.xml",
    "https://pezcyclingnews.com/feed/",
     "https://aviationweek.com/rss.xml",
    "https://simpleflying.com/feed/",
    "https://www.flightglobal.com/feeds/rss",
    "https://airlinegeeks.com/feed/",
    "https://thepointsguy.com/aviation/feed/",
    "https://www.airliners.net/news/rss",
    "https://www.avweb.com/feed/",
    "https://atwonline.com/rss.xml",
    "https://www.aerotime.aero/rss",
    "https://runwaygirlnetwork.com/feed/",
    "https://pitchfork.com/rss/news/",
    "https://www.rollingstone.com/music/music-news/feed/",
    "https://www.billboard.com/feed/",
    "https://www.nme.com/news/music/feed",
    "https://www.stereogum.com/feed/",
    "https://www.musicradar.com/rss/news",
    "https://consequence.net/feed/",
    "https://www.popmatters.com/feed/",
    "https://www.spin.com/feed/",
    "https://www.factmag.com/feed/",
    # aggiungi altri RSS qui
]

# Per gestire duplicati
sent_links = set()

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
    await asyncio.sleep(10)  # Attesa breve all'avvio
    global sent_links

    while True:
        try:
            messages = []
            for url in RSS_FEEDS:
                feed = feedparser.parse(url)
                if feed.entries:
                    entry = feed.entries[0]
                    title = entry.get("title", "Nessun titolo")
                    link = entry.get("link", "")

                    # Evita duplicati
                    if link not in sent_links:
                        sent_links.add(link)
                        # Limita la lunghezza del titolo per sicurezza
                        title = (title[:200] + "...") if len(title) > 200 else title
                        messages.append(f"<b>{title}</b>\n{link}")

            if messages:
                # Divide in blocchi se supera 4096 caratteri
                text = "\n\n".join(messages)
                chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
                for chunk in chunks:
                    await bot.send_message(chat_id=CHAT_ID, text=chunk, parse_mode="HTML")
            else:
                print("Nessuna nuova notizia trovata.")

        except Exception as e:
            print(f"Errore durante fetch o invio news: {e}")

        await asyncio.sleep(900)  # 15 minuti
