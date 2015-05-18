import datetime
from dam.DAMFactory import DAMFactory
from model.stockObjects import Stock
from lib.util import logger
from crawler import Crawler

class DataManager(object):
    def __init__(self, dbpath = "sqlite:///data/stock.sqlite"):
        self.history_start = datetime.datetime.strptime("2004-01-01", '%Y-%m-%d')
        self.dbpath = dbpath
        self.sqlDAM = DAMFactory.createDAM("sql", {'db': self.dbpath})
        self.eastmoneyDAM = DAMFactory.createDAM('eastfinance')
        self.crawler = Crawler(self.dbpath)

    def downloadAll(self, append=True):
        self.crawler.reset()
        logger.info("starting crawler in %s mode" % ("append" if append else "overwrite"))
        stocks = self.eastmoneyDAM.readAllStocks()
        symbol_str = ""
        for stock in stocks:
            symbol_str += "%s - %s\n" %(stock.symbol, stock.name)
            start = self.history_start
            end = datetime.datetime.now()
            stock_l = self.sqlDAM.readStock(stock.symbol)
            if stock_l is None:
                stock_l = Stock(stock.symbol, stock.name, 0)
                self.sqlDAM.writeStock(stock_l)
            else:
                history = self.sqlDAM.readQuotes(stock.symbol, self.history_start, end)
                if len(history) > 0:
                    start = history[-1].time + datetime.timedelta(days=1)
                    if (end - start).days < 1:
                        continue
            self.crawler.addStock(stock_l, start, end)
        self.sqlDAM.commit()
        logger.info("All stocks(%d): %s\n" % (len(stocks), symbol_str))
        self.crawler.start()
        self.crawler.poll()

    def loadAllStocks(self):
        return self.sqlDAM.readAllStocks()

    def loadStockAndHistory(self, symbol):
        stock = self.sqlDAM.readStock(symbol)
        if stock is None:
            return None
        stock.history = self.sqlDAM.readQuotes(stock.symbol, self.history_start, datetime.datetime.now())
        return stock
