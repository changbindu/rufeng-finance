'''
Created on Dec 4, 2011

@author: ppa
'''
from dam.DAMFactory import DAMFactory
from threading import Thread
from threading import Lock

from lib.util import logger

MAX_TRY = 3

class Crawler(object):
    ''' collect quotes/ticks for a list of symbol '''
    def __init__(self, dbpath, poolsize = 5):
        ''' constructor '''
        self.symbols = []
        self.outputDAM = DAMFactory.createDAM("sql", {'db': dbpath})
        self.inputDAM = DAMFactory.createDAM("yahoo")
        self.poolsize = poolsize
        self.readLock = Lock()
        self.writeLock = Lock()
        self.failed = []
        self.succeeded = []
        self.threads = []
        self.counter = 0

    def addSymbol(self, symbol, start, end):
        self.symbols.append((symbol, start, end))

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

    def __getSaveOneSymbol(self, symbol, start, end):
        ''' get and save data for one symbol '''
        lastExcp = None
        with self.readLock: #dam is not thread safe
            failCount = 0
            #try several times since it may fail
            while failCount < MAX_TRY:
                try:
                    self.inputDAM.setSymbol(symbol)
                    quotes = self.inputDAM.readQuotes(start, end)
                except BaseException as excp:
                    failCount += 1
                    lastExcp = excp
                    logger.warning("Failed, %s" % excp)
                    logger.debug("Retry")
                else:
                    break

            if failCount >= MAX_TRY:
                raise BaseException("Can't retrieve historical data %s" % lastExcp)

        with self.writeLock: #dam is not thread safe
            self.outputDAM.setSymbol(symbol)
            self.outputDAM.writeQuotes(quotes)

    def __getAndSaveSymbols(self):
        ''' get and save data '''
        self.counter = 0
        while self.counter < len(self.symbols):
            symbol = self.symbols[self.counter]
            try:
                self.__getSaveOneSymbol(symbol[0], symbol[1], symbol[2])
            except KeyboardInterrupt as excp:
                logger.error("Interrupted while processing %s: %s" % (symbol, excp))
                self.failed.append(symbol)
                raise excp;
            except BaseException as excp:
                logger.error("Error while processing %s: %s" % (symbol, excp))
                self.failed.append(symbol)
            else:
                logger.info("Success processed %s" % symbol[0])
                self.succeeded.append(symbol)
            self.counter += 1
            if 0 == self.counter % 3:
                self.outputDAM.commit()
                logger.info("Processed %d/%d" %(self.counter, len(self.symbols)))

if __name__ == '__main__':
    dbpath = "sqlite:///data/stock.sqlite"
    crawler = Crawler(dbpath, 2)
    for symbol in ("002232", "300192", "600882"):
        crawler.addSymbol(symbol, "20150101", "20150401")
    crawler.start()
    crawler.poll()
    print("Sql database location: %s" % dbpath)
    print("Succeeded: %s" % crawler.succeeded)
    print("Failed: %s" % crawler.failed)
