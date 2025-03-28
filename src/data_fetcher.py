import os
import time

from datetime import datetime, timedelta, timezone
from database import Database
from downloaders import CapitalDownloader, NewsDownloader
from classes.logger import WithLogger

def fetch_trading(db:Database, epics:list[str], timeframes:list[str], max_retry:int=5, retry_delay_s:int=5):
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

    combinations = [(epic, resolution) for epic in epics for resolution in timeframes]
    logger = WithLogger(combinations, progress_file=".fetch_data.log")

    for epic, resolution in logger:
        to_date = db.get_oldest_date(epic, resolution)
        to_date = datetime.now(timezone.utc) if to_date is None else to_date
        from_date = to_date - capital_limits[resolution]
        retry = 0

        while True:
            try:
                from_date_str = from_date.strftime("%Y-%m-%dT%H:%M:%S")
                to_date_str = to_date.strftime("%Y-%m-%dT%H:%M:%S")
                str_to_print = f"{epic}:{resolution} da {from_date_str} a {to_date_str}"

                data = capital.download_historical_data(epic, resolution, from_date_str, to_date_str)
                retry = 0
                if data is None or data <= 0:
                    break
            except Exception as e:
                logger.print_with_time(f"\t❌ Errore {retry}/{max_retry} {str_to_print}: {e}")
                retry += 1
                if retry >= max_retry:
                    return

                time.sleep(retry_delay_s)
                continue

            logger.print_with_time(f"\t📊 Scaricato {str_to_print}...")

            to_date = db.get_oldest_date(epic, resolution) - timedelta(seconds=1)
            from_date = to_date - capital_limits[resolution]


def fetch_news(db:Database):
    '''Scarica le news dal servizio API'''
    raise NotImplementedError("Funzione non implementata")

    news_apikey = os.getenv("NEWS_APIKEY")
    news = NewsDownloader(db, news_apikey)
