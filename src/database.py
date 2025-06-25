import peewee
from datetime import datetime
from playhouse.db_url import connect
from peewee import Model, IntegerField, CharField, FloatField, CompositeKey, AutoField, DateTimeField, BooleanField, ForeignKeyField
from playhouse.fields import JSONField

class Markets(Model):
    id = AutoField()
    epic = CharField(primary_key=True)
    instrumentName = CharField()
    instrumentType = CharField()
    marketStatus = CharField()
    marketCap = FloatField(null=True)
    revenue = FloatField(null=True)
    peRatio = FloatField(null=True)
    dividend = FloatField(null=True)
    sector = CharField(null=True)
    country = CharField(null=True)
    currency = CharField(null=True)
    updated_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'markets'

class TradingStrategies(BaseModel):
    """Configurazione delle strategie di trading"""
    id = AutoField(primary_key=True)
    name = CharField()  # Es: "RSI_BOLLINGER_COMBO"
    epic = CharField()
    strategy_type = CharField()  # RSI, BOLLINGER, MACD, COMBO
    parameters = JSONField()  # Parametri specifici della strategia
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'trading_strategies'

class TradingPositions(BaseModel):
    """Posizioni di trading simulate"""
    id = AutoField(primary_key=True)
    epic = CharField()
    strategy_id = ForeignKeyField(TradingStrategies, backref='positions')
    
    # Dati di apertura
    entry_time = DateTimeField()
    entry_price = FloatField()
    position_type = CharField()  # BUY o SELL
    position_size = FloatField()  # Quantità investita
    
    # Dati tecnici al momento dell'apertura
    rsi_value = FloatField(null=True)
    bollinger_position = CharField(null=True)  # UPPER, LOWER, MIDDLE
    support_level = FloatField(null=True)
    resistance_level = FloatField(null=True)
    volume_indicator = CharField(null=True)  # HIGH, LOW, NORMAL
    
    # Dati di chiusura
    exit_time = DateTimeField(null=True)
    exit_price = FloatField(null=True)
    profit_loss = FloatField(null=True)
    profit_loss_percentage = FloatField(null=True)
    
    # Metadati
    is_open = BooleanField(default=True)
    close_reason = CharField(null=True)  # STOP_LOSS, TAKE_PROFIT, STRATEGY_SIGNAL
    success_probability = FloatField(null=True)  # Probabilità di successo calcolata
    
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'trading_positions'

class PortfolioConfig(BaseModel):
    """Configurazione del portfolio virtuale"""
    id = AutoField(primary_key=True)
    name = CharField(default="Virtual Portfolio")
    initial_capital = FloatField()
    current_capital = FloatField()
    max_position_size = FloatField()  # Massimo per singola posizione
    risk_percentage = FloatField(default=2.0)  # % di rischio per operazione
    check_interval = IntegerField(default=30)  # Secondi tra controlli
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'portfolio_config'
        
class HistoricalData(Model):
    epic = CharField(16)
    resolution = CharField(16)
    snapshotTimeUTC = CharField(32)
    openBid = FloatField()
    openAsk = FloatField()
    highBid = FloatField()
    highAsk = FloatField()
    lowBid = FloatField()
    lowAsk = FloatField()
    closeBid = FloatField()
    closeAsk = FloatField()
    lastTradedVolume = IntegerField()
    support = peewee.FloatField(null=True)
    resistance = peewee.FloatField(null=True)
    sentiment = peewee.FloatField(null=True) # Es: da -1.0 (negativo) a 1.0 (positivo)

    class Meta:
        primary_key = CompositeKey('epic', 'resolution', 'snapshotTimeUTC')

class News(Model):
    publishedAt = CharField(32)
    source = CharField(64)
    author = CharField(64)
    title = CharField(256)
    description = CharField(256)
    url = CharField(256)
    urlToImage = CharField(256)
    content = CharField()

    class Meta:
        primary_key = CompositeKey('publishedAt', 'source')

class Database:
    db:peewee.Database

    def __init__(self, db_URL:str):
        '''
        Initialize the database and create all the tables
        The input url must be in the format "mysql://user:password@host/dbname" or "sqlite://path/to/db"
        '''
        self.db = connect(db_URL)
        self.db.connect()

        models = [HistoricalData, Markets, News]
        for model in models:
            model._meta.database = self.db
        self.db.create_tables(models)

    def save_data_array(self, data:list[tuple]):
        with self.db.atomic():
            cursor = HistoricalData.insert_many(data).on_conflict_ignore().execute()
            return cursor

    def save_market_array(self, data:list[tuple]):
        '''Save markets in the database with format (epic, symbol, instrumentType, instrumentName) it will truncate the table before inserting the new data'''
        with self.db.atomic():
            Markets.truncate_table()
            cursor = Markets.insert_many(data).execute()
            return cursor

    def save_news_array(self, data:list[tuple]):
        with self.db.atomic():
            cursor = News.insert_many(data).on_conflict_ignore().execute()
            return cursor

    def has_epics(self):
        '''Check if the database has any epic'''
        return Markets.select().exists()

    def get_all_epics(self):
        '''Get all the epics in the database'''
        return [m.epic for m in Markets.select()]

    def get_oldest_date(self, epic:str, resolution:str):
        '''Get the oldest date for a given epic and resolution'''
        date = HistoricalData.select(HistoricalData.snapshotTimeUTC).where(HistoricalData.epic == epic, HistoricalData.resolution == resolution).order_by(HistoricalData.snapshotTimeUTC).limit(1)
        date = date.scalar()
        return None if date is None else datetime.fromisoformat(date)

# This test will create a database with two tables: EUR_USD and GBP_USD
# The database will be deleted after the test
# The data are taken from the OANDA API and the News API and saved in the database
if __name__ == "__main__":
    db = Database("sqlite:///:memory:")
    assert db.get_oldest_date("EUR_USD", "DAY") == None

    # Save data in the database
    data = [
        ('EUR_USD', 'DAY', '2021-10-01T00:00:00', 1.0, 1.1, 1.2, 1.3, 0.9, 1.0, 1.1, 1.2, 1000),
        ('EUR_USD', 'DAY', '2021-10-02T00:00:00', 1.1, 1.2, 1.3, 1.4, 1.0, 1.1, 1.2, 1.3, 2000),
    ]
    db.save_data_array(data)
    all = list(HistoricalData.select().tuples())
    assert all == data, all
    assert db.get_oldest_date("EUR_USD", "DAY") == datetime.fromisoformat("2021-10-01T00:00:00")

    # Save markets in the database with format (epic, symbol, instrumentType, instrumentName)
    markets = [
        ('EUR_USD', 'EUR_USD', 'CURRENCY', 'Euro/US Dollar'),
        ('GBP_USD', 'GBP_USD', 'CURRENCY', 'British Pound/U.S. Dollar')
    ]
    db.save_market_array(markets)
    all = list(Markets.select().tuples())
    assert all == [(i+1, *m) for i, m in enumerate(markets)] 
    all = db.get_all_epics()
    assert all == ['EUR_USD', 'GBP_USD']

    # Save news in the database
    news = [
        ('2021-10-01T00:00:00', 'CNN', 'John Doe', 'Title 1', 'Description 1', 'http://www.example.com', 'http://www.example.com/image.jpg', 'Content 1'),
        ('2021-10-02T00:00:00', 'BBC', 'Jane Doe', 'Title 2', 'Description 2', 'http://www.example.com', 'http://www.example.com/image.jpg', 'Content 2')
    ]
    db.save_news_array(news)
    all = list(News.select().tuples())
    assert all == news
