
def from_capital_history(epic:str, resolution:str, data:list[dict]) -> dict:
    '''Trasforma i dati storici di Capital.com in tuple per il database'''
    return [ (
        epic,
        d["snapshotTimeUTC"],
        d["openPrice"]["bid"],
        d["openPrice"]["ask"],
        d["highPrice"]["bid"],
        d["highPrice"]["ask"],
        d["lowPrice"]["bid"],
        d["lowPrice"]["ask"],
        d["closePrice"]["bid"],
        d["closePrice"]["ask"],
        d["lastTradedVolume"]
    ) for d in data ]

def from_capital_markets(data:list[dict]) -> dict:
    '''Trasforma i dati dei mercati di Capital.com in tuple per il database'''
    return [ (
        d["epic"],
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
