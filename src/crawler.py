'''
Created on Dec 4, 2011

@author: ppa
'''
from dam.DAMFactory import DAMFactory
from model.stockObjects import Tick, Quote, Stock
from threading import Thread
from threading import Lock
from Queue import Queue
import time, datetime
import traceback

from lib.errors import Errors, UfException
from lib.util import logger

MAX_TRY = 3

class Crawler(object):
    ''' collect quotes/ticks for a list of symbol '''
    def __init__(self, dbpath, poolsize = 5):
        ''' constructor '''
        self.stockQueue = Queue()
        self.sqlDAM = DAMFactory.createDAM("sql", {'db': dbpath})
        self.yahooDAM = DAMFactory.createDAM("yahoo")
        self.poolsize = poolsize
        self.writeLock = Lock()
        self.failed = []
        self.succeeded = []
        self.threads = []
        self.counter = 0

    def addStock(self, stock, start, end):
        self.stockQueue.put((stock, start, end))

    def reset(self):
        self.symbols = []
        self.succeeded = []
        self.failed = []
        self.counter = 0
        self.poll()

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
        self.sqlDAM.commit()

    def getRemainCount(self):
        return self.stockQueue.qsize()

    def __getSaveOneStockQuotes(self, stock, start, end):
        ''' get and save data for one symbol '''
        lastExcp = None
        failCount = 0
        quotes = None
        #try several times since it may fail
        while failCount < MAX_TRY:
            try:
                quotes = self.yahooDAM.readQuotes(stock.symbol, start, end)
            except BaseException as excp:
                failCount += 1
                lastExcp = excp
                if isinstance(excp, UfException) and excp.getCode() == Errors.NETWORK_404_ERROR:
                    raise BaseException("Failed, stock %s not found" % stock.symbol)
                else:
                    logger.warning("Failed, %s" % (excp))
                logger.info("Retry in 1 second")
                time.sleep(1)
            else:
                break

            if failCount >= MAX_TRY:
                raise BaseException("Can't retrieve historical data %s" % lastExcp)
        return quotes

    def __getAndSaveQuotes(self):
        ''' get and save data '''
        while not self.stockQueue.empty():
            item = self.stockQueue.get_nowait()
            stock = item[0]
            start = item[1]
            end = item[2]
            try:
                quotes = self.__getSaveOneStockQuotes(stock, start, end)
            except KeyboardInterrupt as excp:
                logger.error("Interrupted while processing %s: %s" % (stock.symbol, excp))
                self.failed.append(stock)
                raise excp
            except BaseException as excp:
                logger.error("Error while processing %s: %s" % (stock.symbol, excp))
                #logger.debug(traceback.format_exc())
                self.failed.append(stock)
            else:
                logger.info("Success processed %s" % stock.symbol)
                with self.writeLock: #dam is not thread safe
                    self.sqlDAM.writeQuotes(stock.symbol, quotes)
                    stock.price = quotes[-1].close
                    stock.lastUpdate = datetime.datetime.now()
                    self.sqlDAM.writeStock(stock)

                    self.counter += 1
                    if 0 == self.counter % (self.poolsize if self.poolsize < 20 else 20):
                        self.sqlDAM.commit()
                        logger.info("Processed %d, remain %d" % (self.counter, self.stockQueue.qsize()))
                self.succeeded.append(stock)
            finally:
                self.stockQueue.task_done()
