import requests
import os
import pandas as pd
import datetime
from dotenv import load_dotenv

# Carica variabili da .env
load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
EPICS = os.getenv("EPICS").split(",")

def fetch_news(query, from_date, to_date):
    """Scarica news da NewsAPI con gestione errori."""
    url = f"https://newsapi.org/v2/everything?q={query}&from={from_date}&to={to_date}&sortBy=popularity&apiKey={NEWS_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json().get("articles", [])
    elif response.status_code == 429:
        print("⚠️ Rate limit raggiunto, attesa di 10 secondi...")
        time.sleep(10)
        return fetch_news(query, from_date, to_date)
    else:
        print(f"❌ Errore nelle news per {query}: {response.json()}")
        return []

def save_news(epic):
    """Scarica e salva news per un EPIC."""
    to_date = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d")
    from_date = (datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=30)).strftime("%Y-%m-%d")

    news = fetch_news(epic, from_date, to_date)
    if news:
        df = pd.DataFrame(news)
        df["publishedAt"] = pd.to_datetime(df["publishedAt"])  # Uniformiamo il formato
        df.to_csv(f"datasets/{epic}_news.csv", index=False)
        print(f"✅ Salvate news in datasets/{epic}_news.csv")

if __name__ == "__main__":
    for epic in EPICS:
        save_news(epic)
