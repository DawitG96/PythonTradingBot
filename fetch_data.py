import requests
import pandas as pd
import json
import os
import time
from dotenv import load_dotenv
import sys
from datetime import datetime, timedelta

# Carica variabili da .env
load_dotenv()
API_KEY = os.getenv("API_KEY")
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
BASE_URL = "https://api-capital.backend-capital.com"
EPICS = os.getenv("EPICS").split(",")
RESOLUTIONS = os.getenv("RESOLUTIONS").split(",")

HEADERS = {"X-CAP-API-KEY": API_KEY, "Content-Type": "application/json"}
SESSION_TOKEN = None

def start_new_session():
    """Autenticazione e acquisizione token di sessione."""
    global SESSION_TOKEN, SECURITY_TOKEN
    url = f"{BASE_URL}/api/v1/session"
    payload = json.dumps({"identifier": EMAIL, "password": PASSWORD})
    response = requests.post(url, headers=HEADERS, data=payload)

    if response.status_code == 200:
        SESSION_TOKEN = response.headers.get("CST")
        SECURITY_TOKEN = response.headers.get("X-SECURITY-TOKEN")
        HEADERS["CST"] = SESSION_TOKEN
        HEADERS["X-SECURITY-TOKEN"] = SECURITY_TOKEN
    else:
        print(f"❌ ERRORE {response.status_code}: {response.text}")
        sys.exit(1)

def fetch_historical_data(epic, resolution, end_date=None):
    """Scarica i dati storici, iterando nel passato per coprire tutto lo storico disponibile."""
    os.makedirs("datasets", exist_ok=True)
    filename = f"datasets/{epic}_{resolution}.csv"
    
    df_list = []
    max_bars = 1000  # Limite massimo di Capital.com per richiesta
    date_format = "%Y-%m-%dT%H:%M:%SZ"

    if end_date is None:
        end_date = datetime.utcnow()

    while True:
        end_timestamp = end_date.strftime(date_format)
        url = f"{BASE_URL}/api/v1/prices/{epic}?resolution={resolution}&max={max_bars}&to={end_timestamp}"
        response = requests.get(url, headers=HEADERS)

        if response.status_code == 200:
            data = response.json()["prices"]
            if not data:
                break  # Uscire se non ci sono più dati disponibili

            df = pd.DataFrame(data)
            df["snapshotTime"] = pd.to_datetime(df["snapshotTime"])
            df_list.append(df)

            print(f"✅ Scaricati {len(df)} dati per {epic} ({resolution}) fino a {end_timestamp}")
            
            end_date = df["snapshotTime"].min() - timedelta(seconds=1)  # Prossimo ciclo parte da qui
        else:
            print(f"❌ Errore EPIC {epic} ({resolution}): {response.json()}")
            break

        time.sleep(2)  # Evitare limitazioni API

    if df_list:
        final_df = pd.concat(df_list).sort_values("snapshotTime")
        final_df.to_csv(filename, index=False)
        print(f"✅ Dati salvati in {filename}")

if __name__ == "__main__":
    start_new_session()
    epic = sys.argv[1]  # Riceve l'EPIC come argomento
    for resolution in RESOLUTIONS:
        fetch_historical_data(epic, resolution)
