import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

from database import Database, TradingPositions, TradingStrategies, PortfolioConfig, HistoricalData
from advanced_strategies import TradingStrategies as Strategies

logger = logging.getLogger(__name__)

class TradingSystem:
    """Sistema di trading con backtesting e simulazione"""
    
    def __init__(self, db: Database):
        self.db = db
        self.strategies = Strategies()
        self.portfolio = self.get_or_create_portfolio()
    
    def get_or_create_portfolio(self) -> PortfolioConfig:
        """Ottiene o crea il portfolio virtuale"""
        try:
            return PortfolioConfig.get(PortfolioConfig.is_active == True)
        except PortfolioConfig.DoesNotExist:
            return PortfolioConfig.create(
                name="Virtual Portfolio",
                initial_capital=10000.0,
                current_capital=10000.0,
                max_position_size=1000.0,
                risk_percentage=2.0
            )
    
    def get_market_data(self, epic: str, timeframe: str = "HOUR", limit: int = 100) -> pd.DataFrame:
        """Ottiene dati di mercato dal database"""
        query = HistoricalData.select().where(
            (HistoricalData.epic == epic) &
            (HistoricalData.resolution == timeframe)
        ).order_by(HistoricalData.snapshotTimeUTC.desc()).limit(limit)
        
        if not query.exists():
            raise ValueError(f"Nessun dato trovato per {epic} ({timeframe})")
        
        df = pd.DataFrame(list(query.dicts()))
        df.rename(columns={
            'openBid': 'open',
            'highBid': 'high',
            'lowBid': 'low',
            'closeBid': 'close',
            'lastTradedVolume': 'volume'
        }, inplace=True)
        
        # Ordina per data crescente
        df = df.sort_values('snapshotTimeUTC')
        df['snapshotTimeUTC'] = pd.to_datetime(df['snapshotTimeUTC'])
        df.set_index('snapshotTimeUTC', inplace=True)
        
        return df
    
    def analyze_epic(self, epic: str, strategy_type: str = "COMBINED") -> Dict:
        """Analizza un epic con la strategia specificata"""
        try:
            df = self.get_market_data(epic)
            
            if strategy_type == "RSI":
                result = self.strategies.rsi_strategy(df)
            elif strategy_type == "BOLLINGER":
                result = self.strategies.bollinger_strategy(df)
            else:  # COMBINED
                result = self.strategies.combined_strategy(df)
            
            result.update({
                'epic': epic,
                'current_price': df['close'].iloc[-1],
                'timestamp': df.index[-1],
                'analysis_time': datetime.now()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Errore nell'analisi di {epic}: {e}")
            return {'error': str(e)}
    
    def should_open_position(self, analysis: Dict) -> bool:
        """Determina se aprire una posizione basandosi sull'analisi"""
        if analysis.get('error'):
            return False
        
        signal = analysis.get('signal')
        probability = analysis.get('probability', 0)
        
        # Apri posizione solo se:
        # 1. Il segnale è BUY o SELL
        # 2. La probabilità è superiore al 60%
        # 3. Abbiamo capitale disponibile
        return (
            signal in ['BUY', 'SELL'] and
            probability > 0.6 and
            self.portfolio.current_capital > self.portfolio.max_position_size
        )
    
    def open_position(self, analysis: Dict) -> Optional[TradingPositions]:
        """Apre una nuova posizione"""
        if not self.should_open_position(analysis):
            return None
        
        epic = analysis['epic']
        
        # Controlla se esiste già una posizione aperta per questo epic
        existing = TradingPositions.select().where(
            (TradingPositions.epic == epic) &
            (TradingPositions.is_open == True)
        )
        
        if existing.exists():
            logger.info(f"Posizione già aperta per {epic}")
            return None
        
        # Calcola la size della posizione
        position_size = min(
            self.portfolio.max_position_size,
            self.portfolio.current_capital * (self.portfolio.risk_percentage / 100)
        )
        
        # Crea la posizione
        position = TradingPositions.create(
            epic=epic,
            entry_time=analysis['timestamp'],
            entry_price=analysis['current_price'],
            position_type=analysis['signal'],
            position_size=position_size,
            rsi_value=analysis.get('rsi_value'),
            bollinger_position=analysis.get('bollinger_position'),
            support_level=analysis.get('support_level'),
            resistance_level=analysis.get('resistance_level'),
            volume_indicator=analysis.get('volume_indicator'),
            success_probability=analysis['probability']
        )
        
        # Aggiorna il capitale
        self.portfolio.current_capital -= position_size
        self.portfolio.save()
        
        logger.info(f"Posizione aperta: {epic} {analysis['signal']} @ {analysis['current_price']}")
        return position
    
    def check_and_close_positions(self) -> List[TradingPositions]:
        """Controlla e chiude le posizioni aperte se necessario"""
        open_positions = TradingPositions.select().where(TradingPositions.is_open == True)
        closed_positions = []
        
        for position in open_positions:
            should_close, reason = self.should_close_position(position)
            
            if should_close:
                closed_position = self.close_position(position, reason)
                if closed_position:
                    closed_positions.append(closed_position)
        
        return closed_positions
    
    def should_close_position(self, position: TradingPositions) -> Tuple[bool, str]:
        """Determina se chiudere una posizione"""
        try:
            # Ottieni i dati attuali
            df = self.get_market_data(position.epic, limit=10)
            current_price = df['close'].iloc[-1]
            
            # Calcola profit/loss attuale
            if position.position_type == "BUY":
                current_pl = (current_price - position.entry_price) / position.entry_price
            else:  # SELL
                current_pl = (position.entry_price - current_price) / position.entry_price
            
            # Stop Loss: -5%
            if current_pl <= -0.05:
                return True, "STOP_LOSS"
            
            # Take Profit: +10%
            if current_pl >= 0.10:
                return True, "TAKE_PROFIT"
            
            # Controllo segnali di strategia
            analysis = self.analyze_epic(position.epic)
            if analysis.get('signal') == 'HOLD' or analysis.get('probability', 0) < 0.4:
                return True, "STRATEGY_SIGNAL"
            
            # Controllo time-based: chiudi dopo 24 ore se in perdita
            if datetime.now() - position.entry_time > timedelta(hours=24) and current_pl < 0:
                return True, "TIME_LIMIT"
            
            return False, ""
            
        except Exception as e:
            logger.error(f"Errore nel controllo posizione {position.id}: {e}")
            return True, "ERROR"
    
    def close_position(self, position: TradingPositions, reason: str) -> Optional[TradingPositions]:
        """Chiude una posizione"""
        try:
            df = self.get_market_data(position.epic, limit=1)
            current_price = df['close'].iloc[-1]
            
            # Calcola profit/loss
            if position.position_type == "BUY":
                pl_amount = (current_price - position.entry_price) * (position.position_size / position.entry_price)
            else:  # SELL
                pl_amount = (position.entry_price - current_price) * (position.position_size / position.entry_price)
            
            pl_percentage = (pl_amount / position.position_size) * 100
            
            # Aggiorna la posizione
            position.exit_time = datetime.now()
            position.exit_price = current_price
            position.profit_loss = pl_amount
            position.profit_loss_percentage = pl_percentage
            position.is_open = False
            position.close_reason = reason
            position.updated_at = datetime.now()
            position.save()
            
            # Aggiorna il capitale
            self.portfolio.current_capital += position.position_size + pl_amount
            self.portfolio.save()
            
            logger.info(f"Posizione chiusa: {position.epic} P&L: {pl_amount:.2f} ({pl_percentage:.2f}%)")
            return position
            
        except Exception as e:
            logger.error(f"Errore nella chiusura posizione {position.id}: {e}")
            return None
    
    def get_portfolio_summary(self) -> Dict:
        """Ottiene il riepilogo del portfolio"""
        total_positions = TradingPositions.select().count()
        open_positions = TradingPositions.select().where(TradingPositions.is_open == True).count()
        closed_positions = TradingPositions.select().where(TradingPositions.is_open == False)
        
        total_pl = sum([p.profit_loss for p in closed_positions if p.profit_loss])
        winning_trades = [p for p in closed_positions if p.profit_loss and p.profit_loss > 0]
        
        return {
            'initial_capital': self.portfolio.initial_capital,
            'current_capital': self.portfolio.current_capital,
            'total_pl': total_pl,
            'total_positions': total_positions,
            'open_positions': open_positions,
            'closed_positions': len(list(closed_positions)),
            'winning_trades': len(winning_trades),
            'win_rate': len(winning_trades) / len(list(closed_positions)) * 100 if closed_positions else 0
        }