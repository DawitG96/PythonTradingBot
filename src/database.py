import peewee
from datetime import datetime
from playhouse.db_url import connect
from peewee import Model, IntegerField, CharField, FloatField, CompositeKey, AutoField

class Markets(Model):
    id = AutoField()
    epic = CharField(16, index=True)
    symbol = CharField(16)
    instrumentType = CharField(32)
    instrumentName = CharField(256)

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
