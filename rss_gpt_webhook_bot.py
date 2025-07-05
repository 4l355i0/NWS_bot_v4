import os
import asyncio
import feedparser
import openai
from fastapi import FastAPI
from telegram import Bot
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USER_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY or not USER_ID:
    raise ValueError("Missing TELEGRAM_TOKEN, OPENAI_API_KEY, or CHAT_ID in environment variables.")

openai.api_key = OPENAI_API_KEY
bot = Bot(token=TELEGRAM_TOKEN)
app = FastAPI()

RSS_FEEDS = [
    "https://www.ilfattoquotidiano.it/feed/",
    "https://www.repubblica.it/rss/homepage/rss2.0.xml",
    "https://www.corriere.it/rss/homepage.xml",
    "https://www.bbc.co.uk/news/10628494",
    "https://rss.cnn.com/rss/edition.rss",
]

async def fetch_and_summarize():
    all_entries = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
            all_entries.append(f"{entry.title}\n{entry.link}")
    
    news_text = "\n\n".join(all_entries)
    
    completion = openai.ChatCompletion.create(
        model="gpt-4o-preview",
        messages=[
            {"role": "system", "content": "Sintetizza in italiano le seguenti notizie in modo chiaro e conciso."},
            {"role": "user", "content": news_text}
        ]
    )
    summary = completion.choices[0].message.content
    await bot.send_message(chat_id=USER_ID, text=f"📰 Sintesi notizie:\n\n{summary}", parse_mode='HTML')

async def periodic_task():
    while True:
        try:
            await fetch_and_summarize()
        except Exception as e:
            await bot.send_message(chat_id=USER_ID, text=f"Errore durante il fetch: {e}")
        await asyncio.sleep(900)  # 15 minuti

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_task())
    await bot.send_message(chat_id=USER_ID, text="🤖 BOT avviato: ti invierò news ogni 15 minuti.")

@app.get("/")
def home():
    return {"status": "OK", "message": "Bot RSS-GPT attivo."}
