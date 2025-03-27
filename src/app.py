import os
import sys
import time
import json
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



def fetch_data(db:Database, epics:list[str], interactive:bool=True):
    '''Scarica dati storici dei trading'''

    capital = CapitalDownloader(db, CAPITAL_APIKEY, max_retries=10, retry_delay=20.0)
    
    # Tentativo di login con retry
    login_success = False
    login_attempts = 0
    max_login_attempts = 3
    
    while not login_success and login_attempts < max_login_attempts:
        try:
            capital.start_new_session(CAPITAL_EMAIL, CAPITAL_PASSWORD)
            login_success = True
        except Exception as e:
            login_attempts += 1
            if login_attempts >= max_login_attempts:
                print(f"❌ Impossibile effettuare il login dopo {max_login_attempts} tentativi: {str(e)}")
                return
            print(f"⚠️ Errore durante il login: {str(e)}. Riprovo ({login_attempts}/{max_login_attempts})...")
            time.sleep(5)
    
    try:
        capital.download_epics()
    except Exception as e:
        print(f"⚠️ Errore durante il download degli epics: {str(e)}")
        # Continua comunque con gli epic esistenti

    # Determina se siamo in modalità interattiva o in background
    is_background = not sys.stdin.isatty() or not interactive
    if not epics:
        epics = db.get_all_epics()
        if not is_background:
            proceed = input(f"Ci sono {len(epics)} epics da scaricare. Vuoi continuare? (s/n): ")
            if proceed.lower() != 's':
                print("❌ Operazione annullata dall'utente.")
                return
        else:
            print(f"Modalità automatica: scaricando {len(epics)} epics...")


    total = len(epics) * len(CAPITAL_RESOLUTIONS)
    completed = 0
    start = time.time()

    # Salvataggio dello stato per ripresa
    progress_file = "download_progress.json"
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                progress = json.load(f)
                if is_background or input(f"Trovato progresso precedente. Riprendere da {progress['epic']} ({progress['resolution']})? (s/n): ").lower() == 's':
                    # Trova l'indice da cui riprendere
                    epic_index = epics.index(progress['epic'])
                    resolution_index = CAPITAL_RESOLUTIONS.index(progress['resolution'])
                    # Conteggia quanti item sono già stati completati
                    completed = epic_index * len(CAPITAL_RESOLUTIONS) + resolution_index
                    # Riorganizza la lista degli epics per continuare da dove eravamo rimasti
                    epics = epics[epic_index:]
                    # Se non è il primo resolution dell'epic, salta quelli già completati
                    if resolution_index > 0:
                        current_epic = epics.pop(0)
                        epics.insert(0, current_epic)  # Rimetti l'epic corrente all'inizio
                        CAPITAL_RESOLUTIONS_REMAINING = CAPITAL_RESOLUTIONS[resolution_index:]
                        
                        # Elabora l'epic corrente con le resolution rimanenti
                        for resolution in CAPITAL_RESOLUTIONS_REMAINING:
                            download_data_for_epic(capital, db, current_epic, resolution)
                            completed += 1
                            save_progress(progress_file, current_epic, resolution, completed, total, start)
                        
                        # Ora continua con il resto degli epics normalmente
                        epics = epics[1:]  # Rimuovi l'epic già elaborato
        except (json.JSONDecodeError, ValueError, IndexError) as e:
            print(f"⚠️ Errore nel file di progresso: {str(e)}. Si riprende dall'inizio.")

    for epic in epics:
        for resolution in CAPITAL_RESOLUTIONS:
            try:
                download_data_for_epic(capital, db, epic, resolution)
                completed += 1
                save_progress(progress_file, epic, resolution, completed, total, start)
            except Exception as e:
                print(f"❌ Errore durante il download di {epic} ({resolution}): {str(e)}")
                # Salva il progresso per poi riprendere in seguito
                save_progress(progress_file, epic, resolution, completed, total, start)
                if not is_background:
                    if input("Continuare con il prossimo epic/resolution? (s/n): ").lower() != 's':
                        print("❌ Operazione interrotta dall'utente.")
                        return
                else:
                    print("Modalità automatica: continuando con il prossimo...")
                    # Aggiungiamo un ritardo prima di riprovare in modalità automatica
                    time.sleep(30)

    # Rimuovi il file di progresso quando tutto è completato
    if os.path.exists(progress_file):
        os.remove(progress_file)
    print("✅ Download di tutti i dati completato!")

def download_data_for_epic(capital, db, epic, resolution):
    """Funzione helper per scaricare i dati per un singolo epic e resolution"""
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
        print(f"\t📊 Scaricato {epic} da {from_date_str} a {to_date_str}...")

        to_date = db.get_oldest_date(epic, resolution) - timedelta(seconds=1)
        from_date = to_date - CAPITAL_TIMEFRAME_LIMITS[resolution]

def save_progress(file_path, epic, resolution, completed, total, start_time):
    """Salva lo stato corrente del download per una potenziale ripresa"""
    percent = completed / total
    delta = time.time() - start_time
    remaining = (delta / completed) * (total - completed) if completed > 0 else 0
    delta_str = str(timedelta(seconds=delta))[:-3]
    remaining_str = str(timedelta(seconds=remaining))[:-3]
    print(f"🕒 [{delta_str}] Rimasto: {remaining_str} {completed}/{total} ({percent:.2%})")
    
    with open(file_path, 'w') as f:
        json.dump({
            'epic': epic,
            'resolution': resolution,
            'completed': completed,
            'total': total,
            'timestamp': time.time()
        }, f)




# ======= Main =======
arg = argparse.ArgumentParser(description="Bot di trading")
arg.add_argument("-e", "--epics", help="Epic dei dati da scaricare, lasciare vuoto per tutti", nargs="*", default=[])
arg.add_argument("-n", "--news", help="Scarica le news", action="store_true")
arg.add_argument("-a", "--auto", help="Modalità automatica senza richieste di input", action="store_true")
arguments = arg.parse_args()

if not len(sys.argv) > 1:
    print("❌ Nessun comando specificato. Utilizzare -h per visualizzare l'help.")
    exit(1)

try:
    database = Database(DB_URL)
    interactive = not arguments.auto
    arguments.epics != None and fetch_data(database, arguments.epics, interactive)
    arguments.news and fetch_news(database)
except KeyboardInterrupt:
    print("\n❌ Operazione annullata dall'utente.")
