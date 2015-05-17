'''
Created on Dec 4, 2011

@author: ppa
'''
from dam.DAMFactory import DAMFactory
from model.stockObjects import Tick, Quote, Stock
from threading import Thread
from threading import Lock
import time
import traceback

from lib.util import logger

MAX_TRY = 3

class Crawler(object):
    ''' collect quotes/ticks for a list of symbol '''
    def __init__(self, dbpath, poolsize = 5):
        ''' constructor '''
        self.stocks = []
        self.outputDAM = DAMFactory.createDAM("sql", {'db': dbpath})
        self.inputDAM = DAMFactory.createDAM("yahoo")
        self.poolsize = poolsize
        self.readLock = Lock()
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
        if (len(self.threads) == 0):
            for i in range(0, self.poolsize):
                thread = Thread(name = "CrawlerThread%d" %i, target = self.__getAndSaveSymbols())
                thread.daemon = True
                self.threads.append(thread)
        for t in self.threads:
            t.start()

    def poll(self, timeout = None):
        for t in self.threads:
            t.join(timeout) # no need to block, because thread should complete at last
            if t.is_alive():
                logger.warning("Thread %s timeout" %t.name)

    def __getSaveOneSymbol(self, stock, start, end):
        ''' get and save data for one symbol '''
        lastExcp = None
        with self.readLock: #dam is not thread safe
            failCount = 0
            #try several times since it may fail
            while failCount < MAX_TRY:
                try:
                    quotes = self.inputDAM.readQuotes(stock.symbol, start, end)
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

        with self.writeLock: #dam is not thread safe
            self.outputDAM.writeQuotes(stock.symbol, quotes)

    def __getAndSaveSymbols(self):
        ''' get and save data '''
        self.counter = 0
        while self.counter < len(self.stocks):
            stock = self.stocks[self.counter][0]
            start = self.stocks[self.counter][1]
            end = self.stocks[self.counter][2]
            try:
                self.__getSaveOneSymbol(stock, start, end)
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
                self.succeeded.append(stock)
            self.counter += 1
            if 0 == self.counter % 3:
                self.outputDAM.commit()
                logger.info("Processed %d/%d" % (self.counter, len(self.stocks)))
