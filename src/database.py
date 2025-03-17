import sqlite3

class Database:
    def __init__(self, db_name, epics):
        '''
        Initialize the database and create all the tables
        '''
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

        for epic in epics:
            #resolution,snapshotTime,snapshotTimeUTC,openPrice,closePrice,highPrice,lowPrice,lastTradedVolume
            self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {epic} (resolution TEXT, snapshotTimeUTC TEXT, openBid REAL, openAsk REAL, highBid REAL, highAsk REAL, lowBid REAL, lowAsk REAL, closeBid REAL, closeAsk REAL, lastTradedVolume INTEGER, PRIMARY KEY (resolution, snapshotTimeUTC))")
            #source,author,title,description,url,urlToImage,publishedAt,content
            self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {epic}_news (publishedAt TEXT, source TEXT, author TEXT, title TEXT, description TEXT, url TEXT, urlToImage TEXT, content TEXT, PRIMARY KEY (publishedAt, source))")
        self.conn.commit()

    def __del__(self):
        self.conn.close()

    def save_data_array(self, data, epic, resolution):
        dataOk = []
        for d in data:
            dataOk.append((
                resolution,
                d["snapshotTimeUTC"],
                d["openPrice"]["bid"],
                d["openPrice"]["ask"],
                d["highPrice"]["bid"],
                d["highPrice"]["ask"],
                d["lowPrice"]["bid"],
                d["lowPrice"]["ask"],
                d["closePrice"]["bid"],
                d["closePrice"]["ask"],
                d["lastTradedVolume"]
            ))
        self.cursor.executemany(f"INSERT OR IGNORE INTO {epic} (resolution, snapshotTimeUTC, openBid, openAsk, highBid, highAsk, lowBid, lowAsk, closeBid, closeAsk, lastTradedVolume) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", dataOk)
        self.conn.commit()

    def save_news_array(self, data, epic):
        dataOk = []
        for d in data:
            dataOk.append((
                d["publishedAt"],
                d["source"]["name"],
                d["author"],
                d["title"],
                d["description"],
                d["url"],
                d["urlToImage"],
                d["content"]
            ))
        self.cursor.executemany(f"INSERT OR IGNORE INTO {epic}_news (publishedAt, source, author, title, description, url, urlToImage, content) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", dataOk)
        self.conn.commit()



# This test will create a database with two tables: EUR_USD and GBP_USD
# The database will be deleted after the test
# The data are taken from the OANDA API and the News API and saved in the database
if __name__ == "__main__":
    db = Database(":memory:", ["EUR_USD", "GBP_USD"])

    data = [
        {
            "snapshotTimeUTC": "2021-10-01T00:00:00",
            "openPrice": {"bid": 1.0, "ask": 1.1},
            "highPrice": {"bid": 1.2, "ask": 1.3},
            "lowPrice": {"bid": 0.9, "ask": 1.0},
            "closePrice": {"bid": 1.1, "ask": 1.2},
            "lastTradedVolume": 1000
        },
        {
            "snapshotTimeUTC": "2021-10-02T00:00:00",
            "openPrice": {"bid": 1.1, "ask": 1.2},
            "highPrice": {"bid": 1.3, "ask": 1.4},
            "lowPrice": {"bid": 1.0, "ask": 1.1},
            "closePrice": {"bid": 1.2, "ask": 1.3},
            "lastTradedVolume": 2000
        }
    ]
    db.save_data_array(data, "EUR_USD", "H1")
    db.cursor.execute("SELECT * FROM EUR_USD")
    assert db.cursor.fetchall() == [
        ('H1', '2021-10-01T00:00:00', 1.0, 1.1, 1.2, 1.3, 0.9, 1.0, 1.1, 1.2, 1000),
        ('H1', '2021-10-02T00:00:00', 1.1, 1.2, 1.3, 1.4, 1.0, 1.1, 1.2, 1.3, 2000)
    ]

    news = [
        {
            "publishedAt": "2021-10-01T00:00:00",
            "source": {"name": "CNN"},
            "author": "John Doe",
            "title": "Title 1",
            "description": "Description 1",
            "url": "http://www.example.com",
            "urlToImage": "http://www.example.com/image.jpg",
            "content": "Content 1"
        },
        {
            "publishedAt": "2021-10-02T00:00:00",
            "source": {"name": "BBC"},
            "author": "Jane Doe",
            "title": "Title 2",
            "description": "Description 2",
            "url": "http://www.example.com",
            "urlToImage": "http://www.example.com/image.jpg",
            "content": "Content 2"
        }
    ]
    db.save_news_array(news, "GBP_USD")
    db.cursor.execute("SELECT * FROM GBP_USD_news")
    assert db.cursor.fetchall() == [
        ('2021-10-01T00:00:00', 'CNN', 'John Doe', 'Title 1', 'Description 1', 'http://www.example.com', 'http://www.example.com/image.jpg', 'Content 1'),
        ('2021-10-02T00:00:00', 'BBC', 'Jane Doe', 'Title 2', 'Description 2', 'http://www.example.com', 'http://www.example.com/image.jpg', 'Content 2')
    ]
