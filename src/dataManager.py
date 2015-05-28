import datetime
from dam.DAMFactory import DAMFactory
from model.stockObjects import Stock
from lib.util import logger
from crawler import Crawler

class DataManager(object):
    def __init__(self, dbpath = "data/stock.sqlite"):
        self.history_start = datetime.datetime.strptime("2004-01-01", '%Y-%m-%d')
        self.dbpath = "sqlite:///" + dbpath
        self.sqlDAM = DAMFactory.createDAM("sql", {'db': self.dbpath})
        self.eastmoneyDAM = DAMFactory.createDAM('eastfinance')

    def __downloadStocks(self, stocks, append=True, threads=5):
        crawler = Crawler(self.dbpath, threads)
        crawler.reset()
        symbol_str = ""
        for stock in stocks:
            start = self.history_start
            end = datetime.datetime.now()
            stock_l = self.sqlDAM.readStock(stock.symbol)
            if stock_l is None:
                stock_l = Stock(stock.symbol, stock.name, 0)
                self.sqlDAM.writeStock(stock_l)
            else:
                if stock.lastUpdate is not None:
                    if (end - stock.lastUpdate).days < 1:
                        continue
                    else:
                        start = stock.lastUpdate
            symbol_str += "%s - %s\n" %(stock.symbol, stock.name)
            crawler.addStock(stock_l, start, end)
        # commit to create local new stock objects
        self.sqlDAM.commit()
        if crawler.getRemainCount() > 0:
            logger.info("All stocks to update(%d): \n%s" % (crawler.getRemainCount(), symbol_str))
            logger.info("starting crawler in %s mode with %d threads" % (("append" if append else "overwrite"), threads))
            crawler.start()
            crawler.poll()
        else:
            logger.info("no stock needs to update")

    def downloadStocks(self, symbols, append=True, threads=5):
        stocks = []
        for symbol in symbols:
            s = self.sqlDAM.readStock(symbol)
            if s is not None:
                stocks.append(s)
            else:
                logger.error("stock %s not found in database")
                return
        self.__downloadStocks(stocks, append=append, threads=threads)

    def downloadAll(self, localOnly=False, append=True, threads=5):
        if localOnly:
            logger.info("only update local stocks")
            stocks = self.sqlDAM.readAllStocks()
        else:
            stocks = self.eastmoneyDAM.readAllStocks()
        self.__downloadStocks(stocks, append=append, threads=threads)

    def loadAllStocks(self):
        return self.sqlDAM.readAllStocks()

    def loadStockAndHistory(self, symbol):
        stock = self.sqlDAM.readStock(symbol)
        if stock is None:
            return None
        stock.history = self.sqlDAM.readQuotes(stock.symbol, self.history_start, datetime.datetime.now())
        return stock
