from dam.eastmoneyFinance import EastmoneyFinance
from lib.util import logger
from crawler import Crawler

class DataManager(object):
    def __init__(self):
        self.start = "20040101"
        self.end = "20150401"

    def updateAll(self):
        eastmoney = EastmoneyFinance()
        stocks = eastmoney.getAllStockSymbols()
        symbols = []
        for stock in stocks:
            symbols.append(stock)
        logger.info("All stocks(%d):\n%s" % (len(symbols), symbols))
        crawler = Crawler(symbols, self.start, self.end, 1)
        crawler.getAndSaveSymbols()

if __name__ == '__main__':
    dataManager = DataManager()
    dataManager.updateAll()
