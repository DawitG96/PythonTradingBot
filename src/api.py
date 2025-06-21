import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv

# Importa le tue funzioni di database, trasformazione e strategia
from .database import Database, HistoricalData, Markets
from .strategies import moving_average_crossover
from .transform import calculate_pivot_points
from .providers import TradingViewAnalysis, YahooFinanceNews # NUOVO IMPORT

# Carica le variabili d'ambiente per ottenere la stringa di connessione al DB
load_dotenv()
DB_URL = os.getenv("APP_DB_URL")
if not DB_URL:
    raise RuntimeError("La variabile d'ambiente APP_DB_URL non è impostata.")

# Crea un'istanza globale del database
db = Database(DB_URL)
tv_analysis = TradingViewAnalysis()
yf_news = YahooFinanceNews()

app = FastAPI(
    title="Trading Analysis API",
    description="API per ottenere analisi e segnali di trading."
)

@app.get("/analysis/{epic}")
def get_analysis(epic: str, timeframe: str = "DAY"):
    """
    Restituisce l'analisi completa per un dato epic,
    inclusi supporto, resistenza e segnali di strategia.
    """
    # 1. Carica i dati storici dal database in un DataFrame Pandas
    query = HistoricalData.select().where(
        (HistoricalData.epic == epic) &
        (HistoricalData.resolution == timeframe)
    ).order_by(HistoricalData.snapshotTimeUTC)

    if not query.exists():
        raise HTTPException(status_code=404, detail=f"Nessun dato trovato per l'epic '{epic}' con timeframe '{timeframe}'")

    df = pd.DataFrame(list(query.dicts()))

    # Rinomina le colonne per la compatibilità con le librerie di analisi
    df.rename(columns={
        'openBid': 'open',
        'highBid': 'high',
        'lowBid': 'low',
        'closeBid': 'close',
        'lastTradedVolume': 'volume'
    }, inplace=True)

    # 2. Applica le strategie e le trasformazioni
    df_with_pivots = calculate_pivot_points(df)
    df_with_signals = moving_average_crossover(df_with_pivots)

    # 3. Restituisci l'ultimo segnale e i dati rilevanti
    latest_data = df_with_signals.iloc[-1].to_dict()
    
    return {
        "epic": epic,
        "timeframe": timeframe,
        "latest_signal": latest_data.get("signal"),
        "details": latest_data
    }

@app.get("/market-info/{epic}")
def get_market_info(epic: str):
    """
    Restituisce il sentiment tecnico da TradingView e le notizie da Yahoo Finance
    per un dato epic.
    """
    # NOTA: Questa è una mappatura semplice. Potrebbe essere necessario renderla più complessa.
    # Ad esempio, per il forex, TradingView vuole "EURUSD", non "EUR/USD".
    symbol = epic.replace('/', '')

    # Mappatura approssimativa per lo screener di TradingView
    # Da migliorare in futuro con una logica più precisa
    if epic in ["GOLD", "SILVER", "OIL"]:
        screener = "cfd"
        exchange = "TVC"
    elif len(symbol) > 4 and symbol.isupper(): # Assumiamo sia una coppia di valute
        screener = "forex"
        exchange = "FX_IDC"
    else: # Assumiamo sia un'azione
        screener = "america"
        exchange = "NASDAQ" # Potrebbe essere necessario specificare (es. NYSE)

    try:
        sentiment = tv_analysis.get_sentiment(symbol, screener, exchange)
        news = yf_news.get_news(symbol)

        return {
            "epic": epic,
            "sentiment_summary": sentiment,
            "news": news
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante il recupero delle informazioni di mercato: {e}")


@app.get("/news/{query}")
def get_news_with_sentiment(query: str):
    """
    Scarica le notizie più recenti per una data query (es. un epic o un nome di azienda)
    e ne analizza il sentiment.
    """
    if not NEWS_API_KEY:
        raise HTTPException(status_code=500, detail="La chiave API per le notizie non è configurata nel server.")

    news_downloader = NewsDownloader(api_key=NEWS_API_KEY)
    articles = news_downloader.fetch_articles(query=query)

    if not articles:
        return {"query": query, "articles": []}

    results = []
    for article in articles:
        title = article.get('title')
        description = article.get('description')
        text_to_analyze = f"{title}. {description}"
        
        results.append({
            "title": title,
            "url": article.get('url'),
            "source": article.get('source', {}).get('name'),
            "publishedAt": article.get('publishedAt'),
            "sentiment": analyze_sentiment(text_to_analyze)
        })

    return {"query": query, "articles": results}

@app.get("/signals")
def get_all_signals(timeframe: str = "DAY"):
    """
    Scansiona tutti gli epic e restituisce quelli con un segnale di BUY o SELL.
    NOTA: Questa operazione può essere lenta se ci sono molti epic.
    """
    active_signals = []
    all_epics = [m.epic for m in Markets.select(Markets.epic).distinct()]

    for epic in all_epics:
        try:
            query = HistoricalData.select().where(
                (HistoricalData.epic == epic) &
                (HistoricalData.resolution == timeframe)
            ).order_by(HistoricalData.snapshotTimeUTC)

            if not query.exists():
                continue

            df = pd.DataFrame(list(query.dicts()))
            if df.empty:
                continue

            df.rename(columns={'closeBid': 'close'}, inplace=True)
            df_with_signals = moving_average_crossover(df)
            
            latest_signal = df_with_signals.iloc[-1].get("signal")

            if latest_signal in ["BUY", "SELL"]:
                active_signals.append({
                    "epic": epic,
                    "timeframe": timeframe,
                    "signal": latest_signal,
                    "timestamp": df_with_signals.iloc[-1].get("snapshotTimeUTC")
                })
        except Exception:
            # Ignora gli epic che generano errori durante l'analisi e continua
            continue

    return {"active_signals": active_signals}