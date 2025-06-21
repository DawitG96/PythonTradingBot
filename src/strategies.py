import pandas as pd
from ta.trend import SMAIndicator

def moving_average_crossover(df: pd.DataFrame, fast_period: int = 10, slow_period: int = 30) -> pd.DataFrame:
    """
    Aggiunge al DataFrame i segnali di BUY/SELL basati sul crossover di due medie mobili,
    utilizzando la libreria 'ta'.
    """
    # Assicurati che il DataFrame abbia una colonna 'close'
    if 'close' not in df.columns:
        raise ValueError("Il DataFrame deve contenere una colonna 'close'.")

    # Calcola la media mobile veloce
    fast_sma = SMAIndicator(close=df['close'], window=fast_period)
    df['SMA_fast'] = fast_sma.sma_indicator()

    # Calcola la media mobile lenta
    slow_sma = SMAIndicator(close=df['close'], window=slow_period)
    df['SMA_slow'] = slow_sma.sma_indicator()

    # Determina i punti di crossover
    crossover = (df['SMA_fast'] > df['SMA_slow']) & (df['SMA_fast'].shift(1) < df['SMA_slow'].shift(1))
    crossunder = (df['SMA_fast'] < df['SMA_slow']) & (df['SMA_fast'].shift(1) > df['SMA_slow'].shift(1))

    df['signal'] = "HOLD"
    df.loc[crossover, 'signal'] = "BUY"
    df.loc[crossunder, 'signal'] = "SELL"

    return df