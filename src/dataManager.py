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

    def downloadAll(self, localOnly=False, append=True, threads=5):
        crawler = Crawler(self.dbpath, threads)
        crawler.reset()
        if localOnly:
            stocks = self.sqlDAM.readAllStocks()
        else:
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
                if (stock.lastUpdate is not None) and (end - stock.lastUpdate).days < 1:
                    continue
            crawler.addStock(stock_l, start, end)
        # commit to create local new stock objects
        self.sqlDAM.commit()
        logger.info("All stocks(%d): %s\n" % (len(stocks), symbol_str))
        logger.info("starting crawler in %s mode with %d threads" % (("append" if append else "overwrite"), threads))
        crawler.start()
        crawler.poll()

    def loadAllStocks(self):
        return self.sqlDAM.readAllStocks()

    def loadStockAndHistory(self, symbol):
        stock = self.sqlDAM.readStock(symbol)
        if stock is None:
            return None
        stock.history = self.sqlDAM.readQuotes(stock.symbol, self.history_start, datetime.datetime.now())
        return stock
