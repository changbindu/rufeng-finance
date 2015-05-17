import datetime
from dam.DAMFactory import DAMFactory
from model.stockObjects import Stock
from lib.util import logger
from crawler import Crawler

class DataManager(object):
    def __init__(self, dbpath = "sqlite:///data/stock.sqlite"):
        self.start = datetime.datetime.strptime("2004-01-01", '%Y-%m-%d')
        self.end = datetime.datetime.now()
        self.dbpath = dbpath
        self.sqlDAM = DAMFactory.createDAM("sql", {'db': self.dbpath})
        self.eastmoneyDAM = DAMFactory.createDAM('eastfinance')
        self.crawler = Crawler(self.dbpath)

    def downloadAll(self, append=True):
        self.crawler.reset()
        symbols = self.eastmoneyDAM.listSymbols()
        symbol_str = ""
        for symbol in symbols:
            name = symbols[symbol]
            symbol_str += "%s - %s\n" %(symbol, name)
            stock = self.sqlDAM.readStock(symbol)
            if stock is None:
                stock = Stock(symbol, name, 0)
                self.sqlDAM.writeStock(stock)
            self.crawler.addStock(stock, self.start, self.end)
        self.sqlDAM.commit();
        logger.info("All stocks(%d): %s\n" %(len(symbols), symbol_str))
        self.crawler.start()
        self.crawler.poll()

    def loadStock(self, symbol):
        stock = self.sqlDAM.readStock(symbol)
        stock.history = self.sqlDAM.readQuotes(stock.symbol, self.start, self.end)
        return stock
