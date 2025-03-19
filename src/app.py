import os
import argparse
import time

from database import Database
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from downloaders import CapitalDownloader, NewsDownloader

# Controllo se le variabili d'ambiente sono state impostate
if not os.getenv("APP_TRADING_BOT"):
    print("❌ Variabili di ambiente per il bot di trading non impostate.")
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
    # Imposta data di fine come due giorni fa

    total_epic_resolutions = len(EPICS) * len(CAPITAL_RESOLUTIONS)
    completed = 0

    for epic in EPICS:
        for resolution in CAPITAL_RESOLUTIONS:
            print(f"⏳ Elaborazione {epic} ({resolution})...")

            to_date = datetime.now(timezone.utc) - timedelta(days=2)
            from_date = to_date - CAPITAL_TIMEFRAME_LIMITS[resolution]
            prev_to_date = None

            try:
                while True:

                    from_date_str = from_date.strftime("%Y-%m-%dT%H:%M:%S")
                    to_date_str = to_date.strftime("%Y-%m-%dT%H:%M:%S")

                    print(f"  📊 Scarico dati da {from_date_str} a {to_date_str}...")
                    capital.download_historical_data(epic, resolution, from_date_str, to_date_str)

                    oldest_record = database.get_least_recent_date(epic, resolution)
                    new_to_date = datetime.fromisoformat(oldest_record) - timedelta(seconds=1)

                    if prev_to_date and new_to_date >= prev_to_date:
                        print(f"  ⚠️ Nessun nuovo dato più vecchio disponibile per {epic} ({resolution}), prossima risoluzione.")
                        break

                    prev_to_date = new_to_date
                    to_date = new_to_date
                    from_date = to_date - CAPITAL_TIMEFRAME_LIMITS[resolution]

                    if to_date < datetime(1950, 1, 1):
                        print(f"  🏁 Raggiunto il limite temporale per {epic} ({resolution})")
                        break

                    time.sleep(0.1)

            except Exception as e:
                print(f"❌ Errore durante il download dei dati: {e}")

            completed += 1
            print(f"📈 Progresso: {completed}/{total_epic_resolutions} ({completed/total_epic_resolutions*100:.2f}%)")

    print("✅ Download di tutti i dati completato!")




# ======= Main =======
# TODO da implementare

# Argomenti dal line di comando per il bot
# Eventuali argomenti da aggiungere (per esempio scarica solo le news/trading, ecc.)
arg = argparse.ArgumentParser(description="Bot di trading")
#arguments = arg.parse_args()

database = Database(DB_HOST)
fetch_data(database)
