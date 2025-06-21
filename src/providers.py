from tradingview_ta import TA_Handler, Interval
import yfinance as yf

class TradingViewAnalysis:
    """
    Fornisce l'analisi del sentiment tecnico da TradingView.
    """
    def get_sentiment(self, symbol: str, screener: str, exchange: str, interval: str = Interval.INTERVAL_1_DAY):
        """
        Ottiene il riepilogo dell'analisi tecnica.
        - symbol: Il ticker (es. "GOLD", "AAPL")
        - screener: Il mercato (es. "america", "forex", "crypto")
        - exchange: La borsa (es. "NASDAQ", "FX_IDC")
        """
        try:
            handler = TA_Handler(
                symbol=symbol,
                screener=screener,
                exchange=exchange,
                interval=interval
            )
            analysis = handler.get_analysis()
            return analysis.summary
        except Exception as e:
            print(f"⚠️ Impossibile ottenere l'analisi da TradingView per {symbol}: {e}")
            return None

class YahooFinanceNews:
    """
    Fornisce le notizie di mercato da Yahoo Finance.
    """
    def get_news(self, symbol: str):
        """
        Ottiene le notizie più recenti per un dato ticker.
        """
        try:
            ticker = yf.Ticker(symbol)
            return ticker.news
        except Exception as e:
            print(f"⚠️ Impossibile ottenere le notizie da Yahoo Finance per {symbol}: {e}")
            return []