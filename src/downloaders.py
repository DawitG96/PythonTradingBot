import json
import time
import requests
import transform

from database import Database


class Downloader:
    baseURL:str
    headers:dict
    database:Database
    last_request:float

    def __init__(self, baseURL:str, database:Database=None):
        self.baseURL = baseURL
        self.headers = {}
        self.database = database
        self.last_request = 0.0

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
        super().__init__("https://api-capital.backend-capital.com/api/v1/", database)
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
