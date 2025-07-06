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

