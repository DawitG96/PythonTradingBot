import json
import os
import sys
import time

from datetime import datetime, timedelta, timezone
from database import Database
from downloaders import CapitalDownloader, NewsDownloader

class WithLogger:
    def __init__(self, items:list, stream=sys.stdout, progress_file:str=None):
        self.stream = stream
        self.progress_file = progress_file
        if not self.load():
            self.items = items
            self.completed = 0
        self.total = len(self.items)
        self.start_time = time.time()

    def progress(self):
        self.completed += 1
        percent = self.completed / self.total
        delta = time.time() - self.start_time
        remaining = (delta / self.completed) * (self.total - self.completed)
        delta_str = str(timedelta(seconds=delta))[:-3]
        remaining_str = str(timedelta(seconds=remaining))[:-3]
        return f"🕒 [{delta_str}] Rimasto: {remaining_str} {self.completed}/{self.total} ({percent:.2%})"

    def print_with_time(self, string:str):
        now = datetime.now(timezone.utc)
        now_str = now.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        print(f"[{now_str}] - {string}", file=self.stream)

    def load(self):
        try:
            with open(self.progress_file, 'r') as f:
                data = json.load(f)
                self.completed = data.get('completed')
                self.items = data.get('items')
            self.print_with_time(f"⚠️ Riprendo da {self.completed}/{len(self.items)} elementi...")
            return True
        except Exception:
            return False

    def save(self):
        if self.progress_file is None:
            return
        with open(self.progress_file, 'w') as f:
            json.dump({'items': self.items, 'completed': self.completed}, f)

    def __iter__(self):
        for item in self.items[self.completed:]:
            self.print_with_time(f"⏳ Inizio elaborazione {item}...")
            yield item
            self.print_with_time(self.progress())
            self.save()
        self.print_with_time(f"✅ Elaborazione completata di {self.completed} elementi!")



def fetch_trading(db:Database, epics:list[str], timeframes:list[str]):
    '''Scarica dati storici dei trading'''
    capital_key = os.getenv("CAPITAL_APIKEY")
    capital_email = os.getenv("CAPITAL_EMAIL")
    capital_password = os.getenv("CAPITAL_PASSWORD")
    capital_limits = CapitalDownloader.get_timeframe_limit()

    capital = CapitalDownloader(db, capital_key)
    capital.start_new_session(capital_email, capital_password)
    capital.download_epics()

    if not epics:
        epics = db.get_all_epics()

    logger = WithLogger(epics, progress_file="epics_progress.json")
    for epic in logger:
        for resolution in timeframes:
            to_date = db.get_oldest_date(epic, resolution)
            to_date = datetime.now(timezone.utc) if to_date is None else to_date
            from_date = to_date - capital_limits[resolution]

            while True:
                from_date_str = from_date.strftime("%Y-%m-%dT%H:%M:%S")
                to_date_str = to_date.strftime("%Y-%m-%dT%H:%M:%S")

                data = capital.download_historical_data(epic, resolution, from_date_str, to_date_str)
                if data is None: #or data <= 0:
                    break
                logger.print_with_time(f"\t📊 Scaricato {epic}:{resolution} da {from_date_str} a {to_date_str}...")

                to_date = db.get_oldest_date(epic, resolution) - timedelta(seconds=1)
                from_date = to_date - capital_limits[resolution]


def fetch_news(db:Database):
    '''Scarica le news dal servizio API'''
    raise NotImplementedError("Funzione non implementata")

    news_apikey = os.getenv("NEWS_APIKEY")
    news = NewsDownloader(db, news_apikey)
