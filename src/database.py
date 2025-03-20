import sqlite3

class Database:
    def __init__(self, db_name):
        '''
        Initialize the database and create all the tables
        '''
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS historical_data (epic TEXT, resolution TEXT, snapshotTimeUTC TEXT, openBid REAL, openAsk REAL, highBid REAL, highAsk REAL, lowBid REAL, lowAsk REAL, closeBid REAL, closeAsk REAL, lastTradedVolume INTEGER, PRIMARY KEY (epic, resolution, snapshotTimeUTC))")
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS markets (epic TEXT PRIMARY KEY, instrumentType TEXT, instrumentName TEXT)")
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS news (publishedAt TEXT, source TEXT, author TEXT, title TEXT, description TEXT, url TEXT, urlToImage TEXT, content TEXT, PRIMARY KEY (publishedAt, source))")
        self.conn.commit()

    def __del__(self):
        self.conn.close()

    def save_data_array(self, data:list[tuple]):
        self.cursor.executemany(f"INSERT OR IGNORE INTO historical_data (epic, resolution, snapshotTimeUTC, openBid, openAsk, highBid, highAsk, lowBid, lowAsk, closeBid, closeAsk, lastTradedVolume) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
        self.conn.commit()

    def save_market_array(self, data:list[tuple]):
        self.cursor.executemany(f"INSERT OR IGNORE INTO markets (epic, instrumentType, instrumentName) VALUES (?, ?, ?)", data)
        self.conn.commit()

    def save_news_array(self, data:list[tuple]):
        self.cursor.executemany(f"INSERT OR IGNORE INTO news (publishedAt, source, author, title, description, url, urlToImage, content) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", data)
        self.conn.commit()

    def get_least_recent_date(self, epic, resolution):
        self.cursor.execute(f"SELECT MIN(snapshotTimeUTC) FROM historical_data WHERE epic = ? AND resolution = ?", (epic, resolution))
        return self.cursor.fetchone()[0]



# This test will create a database with two tables: EUR_USD and GBP_USD
# The database will be deleted after the test
# The data are taken from the OANDA API and the News API and saved in the database
if __name__ == "__main__":
    db = Database(":memory:")

    # Save data in the database
    data = [
        ('EUR_USD', 'H1', '2021-10-01T00:00:00', 1.0, 1.1, 1.2, 1.3, 0.9, 1.0, 1.1, 1.2, 1000),
        ('EUR_USD', 'H1', '2021-10-02T00:00:00', 1.1, 1.2, 1.3, 1.4, 1.0, 1.1, 1.2, 1.3, 2000),
    ]
    db.save_data_array(data)
    db.cursor.execute("SELECT * FROM historical_data")
    assert db.cursor.fetchall() == [
        ('EUR_USD', 'H1', '2021-10-01T00:00:00', 1.0, 1.1, 1.2, 1.3, 0.9, 1.0, 1.1, 1.2, 1000),
        ('EUR_USD', 'H1', '2021-10-02T00:00:00', 1.1, 1.2, 1.3, 1.4, 1.0, 1.1, 1.2, 1.3, 2000)
    ]
    assert db.get_least_recent_date("EUR_USD", "H1") == "2021-10-01T00:00:00"

    # Save markets in the database
    markets = [
        ('EUR_USD', 'CURRENCY', 'Euro/US Dollar'),
        ('GBP_USD', 'CURRENCY', 'British Pound/US Dollar')
    ]
    db.save_market_array(markets)
    db.cursor.execute("SELECT * FROM markets")
    assert db.cursor.fetchall() == [
        ('EUR_USD', 'CURRENCY', 'Euro/US Dollar'),
        ('GBP_USD', 'CURRENCY', 'British Pound/US Dollar')
    ]

    # Save news in the database
    news = [
        ('2021-10-01T00:00:00', 'CNN', 'John Doe', 'Title 1', 'Description 1', 'http://www.example.com', 'http://www.example.com/image.jpg', 'Content 1'),
        ('2021-10-02T00:00:00', 'BBC', 'Jane Doe', 'Title 2', 'Description 2', 'http://www.example.com', 'http://www.example.com/image.jpg', 'Content 2')
    ]
    db.save_news_array(news)
    db.cursor.execute("SELECT * FROM news")
    assert db.cursor.fetchall() == [
        ('2021-10-01T00:00:00', 'CNN', 'John Doe', 'Title 1', 'Description 1', 'http://www.example.com', 'http://www.example.com/image.jpg', 'Content 1'),
        ('2021-10-02T00:00:00', 'BBC', 'Jane Doe', 'Title 2', 'Description 2', 'http://www.example.com', 'http://www.example.com/image.jpg', 'Content 2')
    ]
