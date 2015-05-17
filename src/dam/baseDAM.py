'''
Created on Nov 9, 2011

@author: ppa
'''
import abc
from lib.errors import UfException, Errors

class BaseDAM(object):
    ''' base class for DAO '''
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        ''' constructor '''
        pass

    def listSymbols(self):
        ''' list all stocks in market, (symbol : name) '''
        raise UfException(Errors.UNDEFINED_METHOD, "listSymbols method is not defined")

    def readStock(self, symbol):
        ''' read quotes '''
        raise UfException(Errors.UNDEFINED_METHOD, "readStock method is not defined")

    def writeStock(self, Stock):
        ''' read quotes '''
        raise UfException(Errors.UNDEFINED_METHOD, "writeStock method is not defined")

    def readQuotes(self, symbol, start, end):
        ''' read quotes '''
        raise UfException(Errors.UNDEFINED_METHOD, "readQuotes method is not defined")

    def writeQuotes(self, symbol, quotes):
        ''' write quotes '''
        raise UfException(Errors.UNDEFINED_METHOD, "writeQuotes method is not defined")

    def readTicks(self, symbol, start, end):
        ''' read ticks '''
        raise UfException(Errors.UNDEFINED_METHOD, "readTicks method is not defined")

    def writeTicks(self, symbol, ticks):
        ''' read quotes '''
        raise UfException(Errors.UNDEFINED_METHOD, "writeTicks method is not defined")

    def readFundamental(self, symbol):
        ''' read fundamental '''
        raise UfException(Errors.UNDEFINED_METHOD, "readFundamental method is not defined")

    def writeFundamental(self, symbol, Fundamental):
        ''' write fundamental '''
        raise UfException(Errors.UNDEFINED_METHOD, "writeFundamental method is not defined")

    def setup(self, settings):
        ''' setup dam '''
        pass

    def commit(self):
        ''' commit write changes '''
        pass
