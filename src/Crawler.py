'''
Created on Dec 4, 2011

@author: ppa
'''
from dam.DAMFactory import DAMFactory

from os import path
import traceback
import time

from threading import Thread
from threading import Lock

from lib.util import logger

THREAD_TIMEOUT = 5
MAX_TRY = 3

class Crawler(object):
    ''' collect quotes/ticks for a list of symbol '''
    def __init__(self, symbols, start, end, poolsize = 5):
        ''' constructor '''
        self.symbols = symbols
        self.sqlLocation = None
        self.outputDAM = DAMFactory.createDAM("sql", self.__getOutputDamSetting())
        self.inputDAM = DAMFactory.createDAM("yahoo")
        self.start = start
        self.end = end
        self.poolsize = poolsize
        self.readLock = Lock()
        self.writeLock = Lock()
        self.failed = []
        self.succeeded = []

    def __getOutputDamSetting(self):
        self.sqlLocation = 'sqlite:///%s' % self.__getOutputSql()
        logger.info("Sqlite location: %s" % self.sqlLocation)
        return {'db': self.sqlLocation}

    def __getOutputSql(self):
        return path.join("./" "data", "stock.sqlite")

    def __getSaveOneSymbol(self, symbol):
        ''' get and save data for one symbol '''
        try:
            lastExcp = None
            with self.readLock: #dam is not thread safe
                failCount = 0
                #try several times since it may fail
                while failCount < MAX_TRY:
                    try:
                        self.inputDAM.setSymbol(symbol)
                        quotes = self.inputDAM.readQuotes(self.start, self.end)

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

        except BaseException as excp:
            logger.error("Error while processing %s: %s" % (symbol, excp))
            self.failed.append(symbol)
        else:
            logger.info("Processed %s" % symbol)
            self.succeeded.append(symbol)

    def getAndSaveSymbols(self):
        ''' get and save data '''
        counter = 0
        rounds = 0

        if self.poolsize > 1:
            while counter < len(self.symbols):
                size = len(self.symbols) - counter
                if self.poolsize < size:
                    size = self.poolsize
                symbols = self.symbols[counter: counter + size]
                threads = []
                for symbol in symbols:
                    thread = Thread(name = symbol, target = self.__getSaveOneSymbol, args = [symbol])
                    thread.daemon = True
                    thread.start()
                    threads.append(thread)

                for thread in threads:
                    thread.join(THREAD_TIMEOUT) # no need to block, because thread should complete at last
                    if thread.is_active():
                        logger.warning("Thread timeout")

                #can't start another thread to do commit because for sqlLite, only object for the same thread can be commited
                if 0 == rounds % 3:
                    self.outputDAM.commit()

                counter += size
                rounds += 1
                time.sleep(5)
        else:
            for symbol in self.symbols:
                self.__getSaveOneSymbol(symbol)
                self.outputDAM.commit()

if __name__ == '__main__':
    crawler = Crawler(["002232.ss", "300192.ss", "600882.ss"], "20150101", "20150401", 1)
    crawler.getAndSaveSymbols()
    print("Sqlite location: %s" % crawler.sqlLocation)
    print("Succeeded: %s" % crawler.succeeded)
    print("Failed: %s" % crawler.failed)

