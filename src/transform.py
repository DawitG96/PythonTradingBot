
def from_capital_history(epic:str, resolution:str, data:list[dict]) -> dict:
    '''Trasforma i dati storici di Capital.com in tuple per il database'''

    return [ (
        epic,
        resolution,
        d["snapshotTimeUTC"],
        d["openPrice"].get("bid", -1.0),
        d["openPrice"].get("ask", -1.0),
        d["highPrice"].get("bid", -1.0),
        d["highPrice"].get("ask", -1.0),
        d["lowPrice"].get("bid", -1.0),
        d["lowPrice"].get("ask", -1.0),
        d["closePrice"].get("bid", -1.0),
        d["closePrice"].get("ask", -1.0),
        d["lastTradedVolume"]
    ) for d in data ]

def from_capital_markets(data:list[dict]) -> dict:
    '''Trasforma i dati dei mercati di Capital.com in tuple per il database'''
    return [ (
        d["epic"],
        d["symbol"],
        d["instrumentType"],
        d["instrumentName"]
    ) for d in data ]

def from_news_api(data:list[dict]) -> dict:
    '''Trasforma i dati delle news di NewsAPI in tuple per il database'''
    return [ (
        d["publishedAt"],
        d["source"]["name"],
        d["author"],
        d["title"],
        d["description"],
        d["url"],
        d["urlToImage"],
        d["content"]
    ) for d in data ]
