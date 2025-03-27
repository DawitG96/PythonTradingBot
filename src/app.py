import os
import sys
import time
import argparse

from database import Database
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from downloaders import CapitalDownloader, NewsDownloader

# Controllo se le variabili d'ambiente sono state impostate
if not os.getenv("APP_TRADING_BOT"):
    print("Variabili di ambiente non impostate. Caricamento dal file .env...")
    if not load_dotenv():
        print("❌\tFile .env non trovato.\nCopia il file .env.example in .env e imposta le variabili d'ambiente.")
        exit(1)

# Configurazioni iniziali
DB_URL = os.getenv("APP_DB_URL")
NEWS_APIKEY = os.getenv("NEWS_APIKEY")
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



def fetch_data(db:Database, epics:list[str], timeframes:list[str]):
    '''Scarica dati storici dei trading'''
    capital = CapitalDownloader(db, CAPITAL_APIKEY)
    capital.start_new_session(CAPITAL_EMAIL, CAPITAL_PASSWORD)
    capital.download_epics()

    if not epics:
        epics = db.get_all_epics()

    total = len(epics)
    completed = 0
    start = time.time()

    for epic in epics:
        print(f"⏳ Inizio elaborazione {epic}...")
        for resolution in timeframes:
            to_date = db.get_oldest_date(epic, resolution)
            to_date = datetime.now(timezone.utc) if to_date is None else to_date
            from_date = to_date - CAPITAL_TIMEFRAME_LIMITS[resolution]

            while True:
                from_date_str = from_date.strftime("%Y-%m-%dT%H:%M:%S")
                to_date_str = to_date.strftime("%Y-%m-%dT%H:%M:%S")

                data = capital.download_historical_data(epic, resolution, from_date_str, to_date_str)
                if data is None or data <= 0:
                    break
                print(f"\t📊 Scaricato {epic}:{resolution} da {from_date_str} a {to_date_str}...")

                to_date = db.get_oldest_date(epic, resolution) - timedelta(seconds=1)
                from_date = to_date - CAPITAL_TIMEFRAME_LIMITS[resolution]

        completed += 1
        percent = completed / total
        delta = time.time() - start
        remaining = (delta / completed) * (total - completed)
        delta_str = str(timedelta(seconds=delta))[:-3]
        remaining_str = str(timedelta(seconds=remaining))[:-3]
        print(f"🕒 [{delta_str}] Rimasto: {remaining_str} {completed}/{total} ({percent:.2%})")

    print("✅ Download di tutti i dati completato!")




# ======= Main =======
arg = argparse.ArgumentParser(description="Bot di trading")
grp = arg.add_argument_group()
grp.add_argument("-e", "--epics", help="Epic dei dati da scaricare, lasciare vuoto per tutti", nargs="*")
grp.add_argument("-t", "--timeframe", help="Timeframe dei dati da scaricare, lasciare vuoto per DAY", nargs="*", choices=CAPITAL_TIMEFRAME_LIMITS, default="DAY")
arg.add_argument("-n", "--news", help="Scarica le news", action="store_true")
arguments = arg.parse_args()

if not len(sys.argv) > 1:
    print("❌ Nessun comando specificato. Utilizzare -h per visualizzare l'help.")
    exit(1)

try:
    database = Database(DB_URL)
    arguments.epics != None and fetch_data(database, arguments.epics, arguments.timeframe)
    arguments.news and fetch_news(database)
except KeyboardInterrupt:
    print("\n❌ Operazione annullata dall'utente.")
