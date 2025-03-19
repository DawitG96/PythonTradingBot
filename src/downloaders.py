from database import Database
import requests
import json

class Downloader():
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
        response = requests.get(self.baseURL + url, headers=self.headers)
        return self.handle_response(url, response)

    def post(self, url:str, data:dict) -> requests.Response:
        data = json.dumps(data)
        response = requests.post(self.baseURL + url, headers=self.headers, data=data)
        return self.handle_response(url, response)

    def handle_response(url:str, response:requests.Response) -> requests.Response:
        if response.status_code == 200:
            return response
        raise Exception(f"❌ Error '{url}' {response.status_code}: {response.text}")



class CapitalDownloader(Downloader):
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
        self.api_key = api_key

    def download_news(self, query:str, from_date:str, to_date:str):
        url = f"everything?apiKey={self.api_key}&q={query}&from={from_date}&to={to_date}&sortBy=popularity"
        response = self.get(url)

        news = response.json()
        self.database.save_news_array(news.articles)
