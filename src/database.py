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
