import datetime
from dam.DAMFactory import DAMFactory
from lib.util import logger
from crawler import Crawler

class DataManager(object):
    def __init__(self, dbpath = "sqlite:///data/stock.sqlite"):
        self.start = "20040101"
        self.end = self.__dateToStr(datetime.datetime.now())
        self.dbpath = dbpath
        self.sqlDAM = DAMFactory.createDAM("sql", {'db': self.dbpath})
        self.eastmoneyDAM = DAMFactory.createDAM('eastfinance')
        self.crawler = Crawler(self.dbpath)

    def downloadAll(self, append=True):
        self.crawler.reset()
        stocks = self.eastmoneyDAM.listSymbols()
        symbols = ""
        for stock in stocks:
            symbols += "%s - %s\n" %(stock, stocks[stock])
            self.crawler.addSymbol(stock, self.start, self.end)
        logger.info("All stocks(%d): %s\n" %(len(stocks), symbols))
        self.crawler.start()
        self.crawler.poll()

    @staticmethod
    def __dateToStr(date):
        return date.strftime('%Y%m%d')

if __name__ == '__main__':
    dataManager = DataManager()
    print(" will download date from %s to %s" %(dataManager.start, dataManager.end))
    dataManager.downloadAll()
