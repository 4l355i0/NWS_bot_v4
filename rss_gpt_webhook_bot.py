import os
import asyncio
import logging
from datetime import datetime
import feedparser
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("Missing TELEGRAM_TOKEN or CHAT_ID in environment variables.")

bot = Bot(token=TELEGRAM_TOKEN)
USER_ID = int(CHAT_ID)

# Lista di 40 feed RSS da monitorare
RSS_FEEDS = [
    "https://www.ilpost.it/feed/",
    "https://www.repubblica.it/rss/homepage/rss2.0.xml",
    "https://www.corriere.it/rss/homepage.xml",
    "https://www.ansa.it/sito/ansait_rss.xml",
    "https://www.ilsole24ore.com/rss/notizie.xml",
    "https://www.theguardian.com/world/rss",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://www.wired.com/feed/rss",
    "https://www.engadget.com/rss.xml",
    "https://techcrunch.com/feed/",
    "https://www.sciencedaily.com/rss/top.xml",
    "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    "https://www.reutersagency.com/feed/?best-topics=technology",
    "https://feeds.feedburner.com/oreilly/radar/atom",
    "https://www.huffpost.com/section/world-news/feed",
    "https://www.cnbc.com/id/100727362/device/rss/rss.html",
    "https://feeds.arstechnica.com/arstechnica/index/",
    "https://feeds.skynews.com/feeds/rss/world.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.forbes.com/investing/feed/",
    "https://www.bloomberg.com/feed/podcast/etf-report.xml",
    "https://rss.dw.com/rdf/rss-en-all",
    "https://feeds.feedburner.com/blogspot/MKuf",
    "https://www.politico.com/rss/politics08.xml",
    "https://feeds.feedburner.com/TechCrunch/",
    "https://www.economist.com/latest/rss.xml",
    "https://www.scientificamerican.com/rss/news/",
    "https://www.financialexpress.com/feed/",
    "https://indianexpress.com/section/world/feed/",
    "https://www.japantimes.co.jp/feed/",
    "https://www.globaltimes.cn/rss/world.xml",
    "https://www.rt.com/rss/news/",
    "https://abcnews.go.com/abcnews/internationalheadlines",
    "https://www.vox.com/rss/index.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://www.cnet.com/rss/news/",
    "https://rss.app/feeds/JU9JQXn8sN1jVbXf.xml",
    "https://www.marketwatch.com/rss/topstories",
    "https://feeds.skynews.com/feeds/rss/business.xml"
]

# Memorizza link già inviati per evitare duplicati
sent_links = set()

async def fetch_and_send_news():
    logging.info(f"Controllo RSS in corso alle {datetime.now()}")
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:2]:  # Prende solo le ultime 2 notizie per feed
                if entry.link not in sent_links:
                    message = f"<b>{entry.title}</b>\n{entry.link}"
                    await bot.send_message(chat_id=USER_ID, text=message, parse_mode='HTML')
                    sent_links.add(entry.link)
        except Exception as e:
            logging.error(f"Errore durante il fetch dal feed {feed_url}: {e}")

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(fetch_and_send_news, 'interval', minutes=15)
    scheduler.start()
    logging.info("BOT avviato. Invio news ogni 15 minuti.")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
