import json
import time
import requests
import transform
import transform
import logging
from requests.exceptions import RequestException, ConnectionError, Timeout

from database import Database


class Downloader:
    baseURL:str
    headers:dict
    database:Database
    last_request:float

    def __init__(self, baseURL:str, database:Database=None, max_retries:int=10, retry_delay:float=20.0):
        self.baseURL = baseURL
        self.headers = {}
        self.database = database
        self.last_request = 0.0
        self.max_retries = max_retries
        self.retry_delay = retry_delay


        assert self.database is not None, "Database non specificato!"
        assert self.baseURL is not None, "URL non specificato!"

    def header(self, name:str, value:str):
        self.headers[name] = value

    def get(self, url:str) -> requests.Response:
        return self.request("GET", url)

    def post(self, url:str, data:dict) -> requests.Response:
        return self.request("POST", url, data)

    def request(self, method:str, url:str, data:dict=None, maxSecWait:float=0.0) -> requests.Response:
        elapsed = time.time() - self.last_request
        if elapsed < maxSecWait:
            time.sleep(maxSecWait - elapsed)

        data = json.dumps(data) if data is not None else None

        response = requests.request(method, self.baseURL + url, headers=self.headers, data=data)
        self.last_request = time.time()

        retries = 0
        while retries <= self.max_retries:
            try:
                response = requests.request(method, self.baseURL + url, headers=self.headers, data=data)
                self.last_request = time.time()

                match response.status_code:
                    case 200:
                        return response
                    case 404:
                        return None
                    case 429:  # Too Many Requests
                        retry_after = int(response.headers.get('Retry-After', self.retry_delay))
                        print(f"⚠️ Troppe richieste. Attendo {retry_after} secondi...")
                        time.sleep(retry_after)
                        retries += 1
                        continue
                    case _:
                        if retries < self.max_retries:
                            print(f"⚠️ Errore '{url}' {response.status_code}: {response.text}. Riprovo ({retries+1}/{self.max_retries})...")
                            retries += 1
                            time.sleep(self.retry_delay)
                            continue
                        raise Exception(f"❌ Error '{url}' {response.status_code}: {response.text}")
                
            except (ConnectionError, Timeout) as e:
                if retries < self.max_retries:
                    print(f"⚠️ Errore di connessione: {str(e)}. Riprovo ({retries+1}/{self.max_retries}) tra {self.retry_delay} secondi...")
                    retries += 1
                    time.sleep(self.retry_delay)
                    continue
                raise Exception(f"❌ Errore di connessione dopo {self.max_retries} tentativi: {str(e)}")
            except RequestException as e:
                if retries < self.max_retries:
                    print(f"⚠️ Errore di richiesta: {str(e)}. Riprovo ({retries+1}/{self.max_retries}) tra {self.retry_delay} secondi...")
                    retries += 1
                    time.sleep(self.retry_delay)
                    continue
                raise Exception(f"❌ Errore di richiesta dopo {self.max_retries} tentativi: {str(e)}")


class CapitalDownloader(Downloader):
    '''Downloader per dati storici di https://open-api.capital.com/'''

    def __init__(self, database:Database, api_key:str, max_retries:int=10, retry_delay:float=20.0):
        super().__init__("https://api-capital.backend-capital.com/api/v1/", database, max_retries, retry_delay)
        self.header("Content-Type", "application/json")
        self.header("X-CAP-API-KEY", api_key)

    def start_new_session(self, email:str, password:str):
        response = self.post("session", {"identifier": email, "password": password})
        head = response.headers
        self.header("CST", head.get("CST"))
        self.header("X-SECURITY-TOKEN", head.get("X-SECURITY-TOKEN"))

    def download_historical_data(self, epic:str, resolution:str, from_date:str, to_date:str, max_bars:int=1000):
        url = f"prices/{epic}?resolution={resolution}&from={from_date}&to={to_date}&max={max_bars}"
        response = self.request("GET", url, maxSecWait=0.1)
        if(response is None):
            return None

        data = response.json()
        data = transform.from_capital_history(epic, resolution, data["prices"])
        self.database.save_data_array(data)
        return data

    def download_epics(self):
        response = self.get("markets")
        data = response.json()
        data = transform.from_capital_markets(data["markets"])
        self.database.save_market_array(data)



class NewsDownloader(Downloader):
    '''Downloader per dati storici di https://newsapi.org/'''
    def __init__(self, database:Database, api_key:str):
        super().__init__("https://newsapi.org/v2/", database)
        self.header("Content-Type", "application/json")
        self.header("x-api-key", api_key)

    def download_news(self, query:str, from_date:str, to_date:str):
        url = f"everything?q={query}&from={from_date}&to={to_date}"
        response = self.get(url)
        news = response.json()
        news = transform.from_news_api(news["articles"])
        self.database.save_news_array(news)
