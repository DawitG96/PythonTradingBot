import requests
import os
import json
import pandas as pd
from dotenv import load_dotenv
import datetime
import sys
import time

# Carica variabili da .env
load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")  # API key per le news
EPICS = os.getenv("EPICS").split(",")

def fetch_news(query, from_date, to_date):
    """Scarica news da NewsAPI o altre fonti"""
    url = f"https://newsapi.org/v2/everything?q={query}&from={from_date}&to={to_date}&sortBy=popularity&apiKey={NEWS_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json().get("articles", [])
    else:
        print(f"❌ Errore nelle news per {query}: {response.json()}")
        return []

def save_news(epic):
    """Scarica e salva news per un EPIC, con date allineate ai dati di mercato"""
    os.makedirs("datasets", exist_ok=True)
    df_list = []
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=365)  # 1 anno di dati

    while start_date < end_date:
        from_date = start_date.strftime("%Y-%m-%d")
        to_date = (start_date + datetime.timedelta(days=30)).strftime("%Y-%m-%d")

        news = fetch_news(epic, from_date, to_date)
        if news:
            df = pd.DataFrame(news)
            df["publishedAt"] = pd.to_datetime(df["publishedAt"])
            df_list.append(df)

            print(f"✅ Scaricate {len(news)} news per {epic} ({from_date} - {to_date})")

        start_date += datetime.timedelta(days=30)  # Avanzare di un mese per richiesta
        time.sleep(2)

    if df_list:
        final_df = pd.concat(df_list).sort_values("publishedAt")
        filename = f"datasets/{epic}_news.csv"
        final_df.to_csv(filename, index=False)
        print(f"✅ News salvate in {filename}")

if __name__ == "__main__":
    epic = sys.argv[1]  # Riceve l'EPIC come argomento
    save_news(epic)
