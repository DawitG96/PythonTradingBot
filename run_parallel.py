import os
import multiprocessing
from dotenv import load_dotenv

# Carica gli EPIC dal file .env
load_dotenv()
EPICS = os.getenv("EPICS").split(",")

def run_fetch(epic):
    os.system(f"python3 fetch_data.py {epic}")

if __name__ == "__main__":
    with multiprocessing.Pool(len(EPICS)) as pool:
        pool.map(run_fetch, EPICS)
