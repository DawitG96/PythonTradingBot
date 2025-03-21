import os
import argparse

from database import Database
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from downloaders import CapitalDownloader, NewsDownloader

# Controllo se le variabili d'ambiente sono state impostate
if not os.getenv("APP_TRADING_BOT"):
    print("Variabili di ambiente non impostate. Caricamento dal file .env...")
    if not load_dotenv():
        print("❌ File .env non trovato.\nCopia il file .env.example in .env e imposta le variabili d'ambiente.")
        exit(1)

# Configurazioni iniziali
DB_HOST = os.getenv("APP_DB_HOST", ":memory:") # default per SQLite in RAM
EPICS = os.getenv("APP_EPICS").split(",")
NEWS_APIKEY = os.getenv("NEWS_APIKEY")
CAPITAL_RESOLUTIONS = os.getenv("CAPITAL_RESOLUTIONS").split(",")
CAPITAL_APIKEY = os.getenv("CAPITAL_APIKEY")
CAPITAL_EMAIL = os.getenv("CAPITAL_EMAIL")
CAPITAL_PASSWORD = os.getenv("CAPITAL_PASSWORD")
CAPITAL_TIMEFRAME_LIMITS = {
    "MINUTE": timedelta(hours=16),
    "MINUTE_5": timedelta(hours=83),
    "MINUTE_15": timedelta(days=10),
    "HOUR": timedelta(days=41),
    "DAY": timedelta(days=900)
}



# ======= Funzioni del bot =======
def fetch_news(db:Database):
    '''Scarica le news dal servizio API'''

    news = NewsDownloader(db, NEWS_APIKEY)
    pass #TODO da implementare



def fetch_data(db:Database):
    '''Scarica dati storici dei trading'''

    capital = CapitalDownloader(db, CAPITAL_APIKEY)
    capital.start_new_session(CAPITAL_EMAIL, CAPITAL_PASSWORD)
    capital.download_epics()

    total = len(EPICS) * len(CAPITAL_RESOLUTIONS)
    completed = 0

    for epic in EPICS:
        for resolution in CAPITAL_RESOLUTIONS:
            print(f"⏳ Elaborazione {epic} ({resolution})...")

            to_date = db.get_oldest_date(epic, resolution)
            to_date = datetime.now(timezone.utc) if to_date is None else to_date
            from_date = to_date - CAPITAL_TIMEFRAME_LIMITS[resolution]

            while True:
                from_date_str = from_date.strftime("%Y-%m-%dT%H:%M:%S")
                to_date_str = to_date.strftime("%Y-%m-%dT%H:%M:%S")

                data = capital.download_historical_data(epic, resolution, from_date_str, to_date_str)
                if data is None:
                    break
                print(f"  📊 Scaricato {epic} da {from_date_str} a {to_date_str}...")

                to_date = db.get_oldest_date(epic, resolution) - timedelta(seconds=1)
                from_date = to_date - CAPITAL_TIMEFRAME_LIMITS[resolution]

            completed += 1
            print(f"📈 Progresso: {completed}/{total} ({completed/total*100:.2f}%)")

    print("✅ Download di tutti i dati completato!")




# ======= Main =======
arg = argparse.ArgumentParser(description="Bot di trading")
arg.add_argument("-f", "--fetch", help="Scarica i dati specificati [news, data]")
arguments = arg.parse_args()

database = Database(DB_HOST)
match arguments.fetch:
    case "news": fetch_news(database)
    case "data": fetch_data(database)
    case _:
        print("❌ Nessun comando specificato. Utilizzare -h per visualizzare l'help.")
        exit(1)
