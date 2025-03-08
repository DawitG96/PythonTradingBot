import requests
import pandas as pd
import time

# CONFIGURAZIONE API
API_KEY = "TUO_API_KEY"
BASE_URL = "https://api-capital.backend-capital.com"

# HEADERS API
HEADERS = {
    "X-CAP-API-KEY": API_KEY,
    "Content-Type": "application/json"
}

# FUNZIONE PER SCARICARE I DATI STORICI
def fetch_historical_data(epic, resolution="MINUTE_5", max_bars=100):
    url = f"{BASE_URL}/api/v1/prices/{epic}?resolution={resolution}&max={max_bars}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        data = response.json()["prices"]
        df = pd.DataFrame(data)
        df["snapshotTime"] = pd.to_datetime(df["snapshotTime"])
        return df
    else:
        print("Errore:", response.json())
        return None

# ESEMPIO DI UTILIZZO
if __name__ == "__main__":
    EPIC = "IX.D.US100.CFD.IP"  # Nasdaq 100 CFD
    df = fetch_historical_data(EPIC, resolution="MINUTE_5", max_bars=200)

    if df is not None:
        print(df.head())
        df.to_csv("nasdaq_5min_data.csv", index=False)
        print("Dati salvati in nasdaq_5min_data.csv")
