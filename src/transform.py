import pandas as pd

def calculate_pivot_points(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcola i Pivot Points standard basati sui dati del giorno precedente.
    Questa funzione si aspetta un DataFrame con colonne 'high', 'low', 'close'.
    """
    # Il Pivot Point si basa sui dati del periodo precedente
    prev_high = df['high'].shift(1)
    prev_low = df['low'].shift(1)
    prev_close = df['close'].shift(1)

    # Calcolo dei Pivot Points
    pivot = (prev_high + prev_low + prev_close) / 3
    df['resistance'] = (2 * pivot) - prev_low
    df['support'] = (2 * pivot) - prev_high
    
    return df



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
