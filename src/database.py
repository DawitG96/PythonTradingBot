import sqlite3
from datetime import datetime
from mysql.connector import connection

class Database:
    def __init__(self, db_host:str, db_name:str=None, db_user:str=None, db_password:str=None):
        '''
        Initialize the database and create all the tables
        '''

        if db_name is not None:
            self.conn = connection.MySQLConnection(user=db_user, password=db_password, host=db_host, database=db_name)
        else:
            self.conn = sqlite3.connect(db_host)
        self.cursor = self.conn.cursor()

        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS historical_data_DAY (epic TEXT, snapshotTimeUTC TEXT, openBid REAL, openAsk REAL, highBid REAL, highAsk REAL, lowBid REAL, lowAsk REAL, closeBid REAL, closeAsk REAL, lastTradedVolume INTEGER, PRIMARY KEY (epic, snapshotTimeUTC))")
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS historical_data_HOUR (epic TEXT, snapshotTimeUTC TEXT, openBid REAL, openAsk REAL, highBid REAL, highAsk REAL, lowBid REAL, lowAsk REAL, closeBid REAL, closeAsk REAL, lastTradedVolume INTEGER, PRIMARY KEY (epic, snapshotTimeUTC))")
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS historical_data_MINUTE_15 (epic TEXT, snapshotTimeUTC TEXT, openBid REAL, openAsk REAL, highBid REAL, highAsk REAL, lowBid REAL, lowAsk REAL, closeBid REAL, closeAsk REAL, lastTradedVolume INTEGER, PRIMARY KEY (epic, snapshotTimeUTC))")
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS historical_data_MINUTE_5 (epic TEXT, snapshotTimeUTC TEXT, openBid REAL, openAsk REAL, highBid REAL, highAsk REAL, lowBid REAL, lowAsk REAL, closeBid REAL, closeAsk REAL, lastTradedVolume INTEGER, PRIMARY KEY (epic, snapshotTimeUTC))")
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS historical_data_MINUTE (epic TEXT, snapshotTimeUTC TEXT, openBid REAL, openAsk REAL, highBid REAL, highAsk REAL, lowBid REAL, lowAsk REAL, closeBid REAL, closeAsk REAL, lastTradedVolume INTEGER, PRIMARY KEY (epic, snapshotTimeUTC))")
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS markets (epic TEXT PRIMARY KEY, instrumentType TEXT, instrumentName TEXT)")
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS news (publishedAt TEXT, source TEXT, author TEXT, title TEXT, description TEXT, url TEXT, urlToImage TEXT, content TEXT, PRIMARY KEY (publishedAt, source))")
        self.conn.commit()

    def __del__(self):
        self.conn.close()

    def save_data_array(self, data:list[tuple], resolution:str):
        self.cursor.executemany(f"INSERT OR IGNORE INTO historical_data_{resolution} (epic, snapshotTimeUTC, openBid, openAsk, highBid, highAsk, lowBid, lowAsk, closeBid, closeAsk, lastTradedVolume) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
        self.conn.commit()

    def save_market_array(self, data:list[tuple]):
        self.cursor.executemany(f"INSERT OR IGNORE INTO markets (epic, instrumentType, instrumentName) VALUES (?, ?, ?)", data)
        self.conn.commit()

    def save_news_array(self, data:list[tuple]):
        self.cursor.executemany(f"INSERT OR IGNORE INTO news (publishedAt, source, author, title, description, url, urlToImage, content) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", data)
        self.conn.commit()

    def get_oldest_date(self, epic:str, resolution:str):
        self.cursor.execute(f"SELECT MIN(snapshotTimeUTC) FROM historical_data_{resolution} WHERE epic = ?", (epic,))
        date = self.cursor.fetchone()[0]
        return None if date is None else datetime.fromisoformat(date)

    def import_from_sqlite(self, sqlite_db:str):
        '''Import data from a SQLite database to the current database'''
        if sqlite_db is None:
            raise ValueError("Please provide a SQLite database path.")
        
        # Se stiamo usando MySQL
        if isinstance(self.conn, sqlite3.Connection):
            raise ValueError("Cannot import from SQLite to SQLite. Please use a MySQL database connection.")

        self.cursor.execute("SELECT table_name FROM information_schema.tables")
        tables = self.cursor.fetchall()

        self.cursor.execute(f"ATTACH DATABASE ? AS sqlite_db", (sqlite_db,))
        for table in tables:
            self.cursor.execute(f"INSERT OR IGNORE INTO {table[0]} SELECT * FROM sqlite_db.{table[0]}")
        self.conn.commit()

# This test will create a database with two tables: EUR_USD and GBP_USD
# The database will be deleted after the test
# The data are taken from the OANDA API and the News API and saved in the database
if __name__ == "__main__":
    db = Database(":memory:")
    assert db.get_oldest_date("EUR_USD", "DAY") == None

    # Save data in the database
    data = [
        ('EUR_USD', '2021-10-01T00:00:00', 1.0, 1.1, 1.2, 1.3, 0.9, 1.0, 1.1, 1.2, 1000),
        ('EUR_USD', '2021-10-02T00:00:00', 1.1, 1.2, 1.3, 1.4, 1.0, 1.1, 1.2, 1.3, 2000),
    ]
    db.save_data_array(data, "DAY")
    db.cursor.execute("SELECT * FROM historical_data_DAY")
    assert db.cursor.fetchall() == data
    assert db.get_oldest_date("EUR_USD", "DAY") == datetime.fromisoformat("2021-10-01T00:00:00")

    # Save markets in the database
    markets = [
        ('EUR_USD', 'CURRENCY', 'Euro/US Dollar'),
        ('GBP_USD', 'CURRENCY', 'British Pound/US Dollar')
    ]
    db.save_market_array(markets)
    db.cursor.execute("SELECT * FROM markets")
    assert db.cursor.fetchall() == markets

    # Save news in the database
    news = [
        ('2021-10-01T00:00:00', 'CNN', 'John Doe', 'Title 1', 'Description 1', 'http://www.example.com', 'http://www.example.com/image.jpg', 'Content 1'),
        ('2021-10-02T00:00:00', 'BBC', 'Jane Doe', 'Title 2', 'Description 2', 'http://www.example.com', 'http://www.example.com/image.jpg', 'Content 2')
    ]
    db.save_news_array(news)
    db.cursor.execute("SELECT * FROM news")
    assert db.cursor.fetchall() == news
