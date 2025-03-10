import requests
import os
import json
import pandas as pd
from dotenv import load_dotenv
import datetime

# Carica variabili da .env
load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")  # API key per le news
EPICS = os.getenv("EPICS").split(",")

def fetch_news(query, from_date, to_date):
    """Scarica news da NewsAPI."""
    url = f"https://newsapi.org/v2/everything?q={query}&from={from_date}&to={to_date}&sortBy=popularity&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()["articles"]
        return data
    else:
        print(f"❌ Errore nelle news: {response.json()}")
        return []

def save_news(epic):
    """Scarica e salva news per un EPIC."""
    to_date = datetime.date.today().strftime("%Y-%m-%d")
    from_date = (datetime.date.today() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")

    news = fetch_news(epic, from_date, to_date)
    if news:
        df = pd.DataFrame(news)
        df.to_csv(f"datasets/{epic}_news.csv", index=False)
        print(f"✅ Salvate news in datasets/{epic}_news.csv")

if __name__ == "__main__":
    for epic in EPICS:
        save_news(epic)
