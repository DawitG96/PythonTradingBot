import json
import time
import requests
import transform

from database import Database


class Downloader:
    baseURL:str
    session: requests.Session
    database:Database
    last_request:float
    rate_limit_per_second: int

    def __init__(self, baseURL:str, database:Database=None, rate_limit_per_second:int = 10):
        self.baseURL = baseURL
        self.session = requests.Session()
        self.database = database
        self.last_request = 0.0
        self.rate_limit_per_second = rate_limit_per_second

        assert self.database is not None, "Database non specificato!"
        assert self.baseURL is not None, "URL non specificato!"

    def header(self, name:str, value:str):
        self.session.headers[name] = value

    def get(self, url:str) -> requests.Response:
        return self.request("GET", url, maxSecWait=(1 / self.rate_limit_per_second))

    def post(self, url:str, data:dict) -> requests.Response:
        return self.request("POST", url, data, maxSecWait=(1 / self.rate_limit_per_second))

    def request(self, method:str, url:str, data:dict=None, maxSecWait:float=0.0) -> requests.Response:
        elapsed = time.time() - self.last_request
        if elapsed < maxSecWait:
            time.sleep(maxSecWait - elapsed)

        data = json.dumps(data) if data is not None else None
        response = self.session.request(method, self.baseURL + url, data=data)
        self.last_request = time.time()

        match response.status_code:
            case 200:
                return response
            case 404:
                return None
            # TODO gestire eventualmente altri codici di errore
            case _:
                raise Exception(f"❌ Error '{url}' {response.status_code}: {response.text}")



class CapitalDownloader(Downloader):
    '''Downloader per dati storici di https://open-api.capital.com/'''

    def __init__(self, database:Database, api_key:str):
        super().__init__("https://api-capital.backend-capital.com/api/v1/", database, rate_limit_per_second=8)
        self.header("Content-Type", "application/json")
        self.header("X-CAP-API-KEY", api_key)

    def start_new_session(self, email:str, password:str):
        response = self.post("session", {"identifier": email, "password": password})
        head = response.headers
        self.header("CST", head.get("CST"))
        self.header("X-SECURITY-TOKEN", head.get("X-SECURITY-TOKEN"))

    def download_historical_data(self, epic:str, resolution:str, from_date:str, to_date:str, max_bars:int=1000):
        relative_url = f"prices/{epic}?resolution={resolution}&from={from_date}&to={to_date}"
        
        try:
            # Usa il metodo get() della classe base che ora gestisce gli errori
            response = self.get(relative_url)
        except Exception as e:
            # Gestisce specificamente l'errore di rate-limiting (429) per riprovare
            if "429" in str(e):
                print("⚠️ Troppe richieste. Attendo 20 secondi...")
                time.sleep(20)
                return self.download_historical_data(epic, resolution, from_date, to_date)
            else:
                # Per tutti gli altri errori (incluso il 500), solleva di nuovo l'eccezione per fermare lo script.
                print(f"❌ Errore critico durante il download dei dati storici per {epic}.")
                raise e

        # Se la risposta è None (es. 404), significa che non ci sono dati.
        if response is None:
            return []

        prices = response.json().get('prices', [])
        if not prices:
            return []

        # Trasformazione dei dati per allinearli al modello del database
        data = []
        for p in prices:
            # Salta i record incompleti che potrebbero essere restituiti dall'API
            if p.get('openPrice') is None or p.get('closePrice') is None or p.get('highPrice') is None or p.get('lowPrice') is None:
                continue

            # Gestisce i due possibili formati di prezzo (dizionario bid/ask o singolo valore)
            open_price = p['openPrice']
            close_price = p['closePrice']
            high_price = p['highPrice']
            low_price = p['lowPrice']

            if isinstance(open_price, dict):
                open_bid = open_price.get('bid')
                open_ask = open_price.get('ask')
                if open_bid is None and open_ask is not None: open_bid = open_ask
                if open_ask is None and open_bid is not None: open_ask = open_bid

                close_bid = close_price.get('bid')
                close_ask = close_price.get('ask')
                if close_bid is None and close_ask is not None: close_bid = close_ask
                if close_ask is None and close_bid is not None: close_ask = close_bid

                high_bid = high_price.get('bid')
                high_ask = high_price.get('ask')
                if high_bid is None and high_ask is not None: high_bid = high_ask
                if high_ask is None and high_bid is not None: high_ask = high_bid

                low_bid = low_price.get('bid')
                low_ask = low_price.get('ask')
                if low_bid is None and low_ask is not None: low_bid = low_ask
                if low_ask is None and low_bid is not None: low_ask = low_bid

                # Se dopo la correzione uno dei valori è ancora None (es. dict vuoto), il record non è valido.
                if open_bid is None or close_bid is None or high_bid is None or low_bid is None:
                    continue
            else:
                open_bid = open_ask = open_price
                close_bid = close_ask = close_price
                high_bid = high_ask = high_price
                low_bid = low_ask = low_price

            data.append((
                epic,
                resolution,
                p['snapshotTimeUTC'],
                open_bid,
                open_ask,
                close_bid,
                close_ask,
                high_bid,
                high_ask,
                low_bid,
                low_ask,
                p['lastTradedVolume']
            ))
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
