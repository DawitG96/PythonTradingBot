import os
import multiprocessing
from dotenv import load_dotenv

# Carica il file .env
load_dotenv()

# Verifica EPICS
epics_str = os.getenv("EPICS")
if not epics_str:
    raise ValueError("❌ ERRORE: Variabile EPICS non trovata nel file .env!")

EPICS = epics_str.split(",")

def fetch_data(epic):
    os.system(f"python3 fetch_data.py {epic}")

def fetch_news(epic):
    os.system(f"python3 fetch_news.py {epic}")

if __name__ == "__main__":
    pool = multiprocessing.Pool(processes=len(EPICS) * 2)  # Parallelizza EPICS * 2 processi

    for epic in EPICS:
        pool.apply_async(fetch_data, (epic,))

    pool.close()
    pool.join()
