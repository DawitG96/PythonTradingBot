import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import talib

class TechnicalIndicators:
    """Classe per calcolare tutti gli indicatori tecnici"""
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calcola RSI"""
        return talib.RSI(df['close'].values, timeperiod=period)
    
    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std: float = 2) -> Dict[str, pd.Series]:
        """Calcola Bollinger Bands"""
        upper, middle, lower = talib.BBANDS(
            df['close'].values, 
            timeperiod=period, 
            nbdevup=std, 
            nbdevdn=std
        )
        
        return {
            'bb_upper': pd.Series(upper, index=df.index),
            'bb_middle': pd.Series(middle, index=df.index),
            'bb_lower': pd.Series(lower, index=df.index)
        }
    
    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calcola MACD"""
        macd, signal_line, histogram = talib.MACD(
            df['close'].values,
            fastperiod=fast,
            slowperiod=slow,
            signalperiod=signal
        )
        
        return {
            'macd': pd.Series(macd, index=df.index),
            'macd_signal': pd.Series(signal_line, index=df.index),
            'macd_histogram': pd.Series(histogram, index=df.index)
        }
    
    @staticmethod
    def calculate_support_resistance(df: pd.DataFrame, period: int = 20) -> Tuple[float, float]:
        """Calcola livelli di supporto e resistenza"""
        recent_data = df.tail(period)
        
        # Supporto: minimo dei minimi recenti
        support = recent_data['low'].min()
        
        # Resistenza: massimo dei massimi recenti
        resistance = recent_data['high'].max()
        
        return support, resistance
    
    @staticmethod
    def calculate_volume_indicator(df: pd.DataFrame, period: int = 20) -> str:
        """Calcola indicatore di volume"""
        if 'volume' not in df.columns or df['volume'].isna().all():
            return "UNKNOWN"
        
        recent_volume = df['volume'].tail(period)
        current_volume = df['volume'].iloc[-1]
        avg_volume = recent_volume.mean()
        
        if current_volume > avg_volume * 1.5:
            return "HIGH"
        elif current_volume < avg_volume * 0.5:
            return "LOW"
        else:
            return "NORMAL"

class TradingStrategies:
    """Implementazione delle strategie di trading"""
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
    
    def rsi_strategy(self, df: pd.DataFrame, rsi_oversold: int = 30, rsi_overbought: int = 70) -> Dict:
        """Strategia RSI"""
        rsi = self.indicators.calculate_rsi(df)
        current_rsi = rsi.iloc[-1]
        
        signal = "HOLD"
        probability = 0.5
        
        if current_rsi < rsi_oversold:
            signal = "BUY"
            probability = min(0.8, (rsi_oversold - current_rsi) / rsi_oversold + 0.5)
        elif current_rsi > rsi_overbought:
            signal = "SELL"
            probability = min(0.8, (current_rsi - rsi_overbought) / (100 - rsi_overbought) + 0.5)
        
        return {
            'signal': signal,
            'probability': probability,
            'rsi_value': current_rsi,
            'strategy': 'RSI'
        }
    
    def bollinger_strategy(self, df: pd.DataFrame) -> Dict:
        """Strategia Bollinger Bands"""
        bb = self.indicators.calculate_bollinger_bands(df)
        current_price = df['close'].iloc[-1]
        current_upper = bb['bb_upper'].iloc[-1]
        current_lower = bb['bb_lower'].iloc[-1]
        current_middle = bb['bb_middle'].iloc[-1]
        
        signal = "HOLD"
        probability = 0.5
        position = "MIDDLE"
        
        if current_price <= current_lower:
            signal = "BUY"
            position = "LOWER"
            probability = 0.7
        elif current_price >= current_upper:
            signal = "SELL"
            position = "UPPER"
            probability = 0.7
        elif current_price < current_middle:
            position = "LOWER_MIDDLE"
        elif current_price > current_middle:
            position = "UPPER_MIDDLE"
        
        return {
            'signal': signal,
            'probability': probability,
            'bollinger_position': position,
            'strategy': 'BOLLINGER'
        }
    
    def combined_strategy(self, df: pd.DataFrame) -> Dict:
        """Strategia combinata RSI + Bollinger + MACD"""
        rsi_result = self.rsi_strategy(df)
        bb_result = self.bollinger_strategy(df)
        macd = self.indicators.calculate_macd(df)
        
        # MACD Signal
        current_macd = macd['macd'].iloc[-1]
        current_signal = macd['macd_signal'].iloc[-1]
        macd_signal = "BUY" if current_macd > current_signal else "SELL"
        
        # Combinazione dei segnali
        signals = [rsi_result['signal'], bb_result['signal'], macd_signal]
        buy_votes = signals.count('BUY')
        sell_votes = signals.count('SELL')
        
        if buy_votes >= 2:
            final_signal = "BUY"
            probability = (rsi_result['probability'] + bb_result['probability']) / 2 + 0.1
        elif sell_votes >= 2:
            final_signal = "SELL"
            probability = (rsi_result['probability'] + bb_result['probability']) / 2 + 0.1
        else:
            final_signal = "HOLD"
            probability = 0.4
        
        # Calcola supporto e resistenza
        support, resistance = self.indicators.calculate_support_resistance(df)
        volume_indicator = self.indicators.calculate_volume_indicator(df)
        
        return {
            'signal': final_signal,
            'probability': min(0.9, probability),
            'rsi_value': rsi_result['rsi_value'],
            'bollinger_position': bb_result['bollinger_position'],
            'support_level': support,
            'resistance_level': resistance,
            'volume_indicator': volume_indicator,
            'macd_signal': macd_signal,
            'strategy': 'COMBINED'
        }