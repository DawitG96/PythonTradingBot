from database import Database
import requests

class Downloader:
    baseURL:str
    headers:dict
    database:Database

    def __init__(self, baseURL:str, database:Database=None):
        self.baseURL = baseURL
        self.headers = {}
        self.database = database

        assert self.database is not None, "Database non specificato!"
        assert self.baseURL is not None, "URL non specificato!"

    def header(self, name:str, value:str):
        self.headers[name] = value

    def get(self, url:str) -> requests.Response:
        return self.request("GET", url)

    def post(self, url:str, data:dict) -> requests.Response:
        return self.request("POST", url, data)

    def request(self, method:str, url:str, data:dict=None, maxRateSec:float=0.0) -> requests.Response:
        response = requests.request(method, url, headers=self.headers, data=data)

        match response.status_code:
            case 200:
                return response
            case 429: # TODO magari mettere un wait usando il paramentro maxRateSec e riprovare (?)
                raise Exception(f"❌ Rate limited '{url}' {response.status_code}: {response.text}")
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
        response = self.get(url)

        data = response.json()
        self.database.save_data_array(data.prices)



class NewsDownloader(Downloader):
    def __init__(self, database:Database, api_key:str):
        super().__init__("https://newsapi.org/v2/", database)
        self.header("Content-Type", "application/json")
        self.header("x-api-key", api_key)

    def download_news(self, query:str, from_date:str, to_date:str):
        url = f"everything?q={query}&from={from_date}&to={to_date}"
        response = self.get(url)

        news = response.json()
        self.database.save_news_array(news.articles)
