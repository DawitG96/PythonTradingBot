import os
import multiprocessing

EPICS = os.getenv("EPICS").split(",")

def fetch_data(epic):
    os.system(f"python fetch_data.py {epic}")

def fetch_news(epic):
    os.system(f"python fetch_news.py {epic}")

if __name__ == "__main__":
    pool = multiprocessing.Pool(processes=len(EPICS) * 2)  # Parallelizza EPICS * 2 processi

    for epic in EPICS:
        pool.apply_async(fetch_data, (epic,))
        pool.apply_async(fetch_news, (epic,))

    pool.close()
    pool.join()
