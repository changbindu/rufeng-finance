'''
Created on Dec 4, 2011

@author: ppa
'''
from dam.DAMFactory import DAMFactory
from model.stockObjects import Tick, Quote, Stock
from threading import Thread
from threading import Lock
import time, datetime
import traceback

from lib.util import logger

MAX_TRY = 3

class Crawler(object):
    ''' collect quotes/ticks for a list of symbol '''
    def __init__(self, dbpath, poolsize = 5):
        ''' constructor '''
        self.stocks = []
        self.sqlDAM = DAMFactory.createDAM("sql", {'db': dbpath})
        self.yahooDAM = DAMFactory.createDAM("yahoo")
        self.poolsize = poolsize
        self.writeLock = Lock()
        self.failed = []
        self.succeeded = []
        self.threads = []
        self.counter = 0

    def addStock(self, stock, start, end):
        self.stocks.append((stock, start, end))

    def reset(self):
        self.symbols = []
        self.succeeded = []
        self.failed = []
        self.counter = 0

    def start(self):
        if len(self.threads) == 0:
            for i in range(0, self.poolsize):
                thread = Thread(name = "CrawlerThread%d" %i, target = self.__getAndSaveQuotes)
                thread.daemon = True
                self.threads.append(thread)
        for t in self.threads:
            t.start()

    def poll(self, timeout = None):
        for t in self.threads:
            t.join(timeout) # no need to block, because thread should complete at last
            if t.is_alive():
                logger.warning("Thread %s timeout" %t.name)

    def __getSaveOneStockQuotes(self, stock, start, end):
        ''' get and save data for one symbol '''
        lastExcp = None
        failCount = 0
        #try several times since it may fail
        while failCount < MAX_TRY:
            try:
                quotes = self.yahooDAM.readQuotes(stock.symbol, start, end)
            except BaseException as excp:
                failCount += 1
                lastExcp = excp
                logger.warning("Failed, %s: %s" % (excp, traceback.format_exc()))
                logger.info("Retry in 1 second")
                time.sleep(1)
            else:
                break

            if failCount >= MAX_TRY:
                raise BaseException("Can't retrieve historical data %s" % lastExcp)
        return quotes

    def __getAndSaveQuotes(self):
        ''' get and save data '''
        self.counter = 0
        while self.counter < len(self.stocks):
            stock = self.stocks[self.counter][0]
            start = self.stocks[self.counter][1]
            end = self.stocks[self.counter][2]
            try:
                quotes = self.__getSaveOneStockQuotes(stock, start, end)
            except KeyboardInterrupt as excp:
                logger.error("Interrupted while processing %s: %s" % (stock.symbol, excp))
                self.failed.append(stock)
                raise excp
            except BaseException as excp:
                logger.error("Error while processing %s: %s" % (stock.symbol, excp))
                logger.debug(traceback.format_exc())
                self.failed.append(stock)
            else:
                logger.info("Success processed %s" % stock.symbol)
                with self.writeLock: #dam is not thread safe
                    self.sqlDAM.writeQuotes(stock.symbol, quotes)
                    stock.price = quotes[-1].close
                    stock.lastUpdate = datetime.datetime.now()
                    self.sqlDAM.writeStock(stock)

                    self.counter += 1
                    if 0 == self.counter % (self.poolsize if self.poolsize < 20 else 20) \
                       or self.counter == len(self.stocks):
                        self.sqlDAM.commit()
                        logger.info("Processed %d/%d" % (self.counter, len(self.stocks)))
                self.succeeded.append(stock)
