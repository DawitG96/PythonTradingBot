import os
import json
import time
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

# Carica variabili da .env
load_dotenv()
API_KEY = os.getenv("API_KEY")
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
BASE_URL = "https://api-capital.backend-capital.com"

EPICS = os.getenv("EPICS").split(",")  # Lista EPIC separati da virgola
RESOLUTIONS = os.getenv("RESOLUTIONS").split(",")  # Timeframe disponibili

TIMEFRAME_LIMITS = {
    "MINUTE": timedelta(hours=16),
    "MINUTE_5": timedelta(hours=83),
    "MINUTE_15": timedelta(days=10),
    "HOUR": timedelta(days=41),
    "DAY": timedelta(days=900)
}

HEADERS = {
    "X-CAP-API-KEY": API_KEY,
    "Content-Type": "application/json"
}

SESSION_TOKEN = None

def start_new_session():
    """Autenticazione API"""
    global SESSION_TOKEN, SECURITY_TOKEN
    url = f"{BASE_URL}/api/v1/session"
    payload = json.dumps({"identifier": EMAIL, "password": PASSWORD})
    response = requests.post(url, headers=HEADERS, data=payload)

    if response.status_code == 200:
        SESSION_TOKEN = response.headers.get("CST")
        SECURITY_TOKEN = response.headers.get("X-SECURITY-TOKEN")
        HEADERS["CST"] = SESSION_TOKEN
        HEADERS["X-SECURITY-TOKEN"] = SECURITY_TOKEN
        print(f"✅ Autenticazione OK!")
    else:
        print(f"❌ ERRORE {response.status_code}: {response.text}")

def fetch_historical_data(epic, resolution, from_date, to_date, max_bars=1000):
    """Scarica i dati storici"""
    url = f"{BASE_URL}/api/v1/prices/{epic}?resolution={resolution}&from={from_date}&to={to_date}&max={max_bars}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        data = response.json().get("prices", [])
        if not data:
            return None
        df = pd.DataFrame(data)
        df["snapshotTime"] = pd.to_datetime(df["snapshotTime"])
        return df
    else:
        print(f"❌ Errore {epic} ({resolution}): {response.json()}")
        return None

def format_datetime(dt):
    """Formatta la data per l'API"""
    return dt.strftime("%Y-%m-%dT%H:%M:%S")

def save_data(df, epic, resolution):
    """Salva i dati in un unico file CSV con append"""
    os.makedirs("datasets", exist_ok=True)
    filename = f"datasets/{epic}_{resolution}.csv"

    # Se il file esiste, fai append, altrimenti scrivi normalmente
    if os.path.exists(filename):
        df.to_csv(filename, mode='a', header=False, index=False)
    else:
        df.to_csv(filename, index=False)

    print(f"📂 Dati salvati in {filename} (nuove righe: {len(df)})")

def process_data(epic, resolution, to_date):
    """Scarica i dati progressivamente con append"""
    from_date = to_date - TIMEFRAME_LIMITS[resolution]
    prev_to_date = None  # Per evitare loop infinito

    while True:
        print(f"⏳ Scarico {epic} ({resolution}) da {from_date} a {to_date}...")
        data = fetch_historical_data(epic, resolution, format_datetime(from_date), format_datetime(to_date))

        if data is None or data.empty:
            print(f"✅ Dati completi per {epic} ({resolution}), stop.")
            break

        save_data(data, epic, resolution)

        # Aggiorna il nuovo `to_date`
        new_to_date = (data["snapshotTime"].min() - timedelta(seconds=1)).replace(tzinfo=timezone.utc)

        if new_to_date == prev_to_date:
            print(f"❌ Nessun nuovo dato disponibile, interrompo il download per {epic} ({resolution}).")
            break

        prev_to_date = new_to_date
        to_date = new_to_date
        from_date = to_date - TIMEFRAME_LIMITS[resolution]

        time.sleep(0.1)  # Rispetta il rate limit

def main():
    """Scarica i dati alternando gli EPIC"""
    start_new_session()
    
    to_date = datetime.now(timezone.utc) - timedelta(days=2)

    while True:
        completed = 0  # Conta quanti EPIC hanno terminato il download
        
        for epic in EPICS:
            for resolution in RESOLUTIONS:
                process_data(epic, resolution, to_date)
                completed += 1

        if completed == len(EPICS) * len(RESOLUTIONS):
            break

if __name__ == "__main__":
    main()
