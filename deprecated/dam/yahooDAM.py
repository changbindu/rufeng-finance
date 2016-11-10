'''
Created on Nov 9, 2011

@author: ppa
'''
from dam.baseDAM import BaseDAM
from dam.yahooFinance import YahooFinance

import logging
LOG = logging.getLogger()

class YahooDAM(BaseDAM):
    ''' Yahoo DAM '''

    def __init__(self):
        ''' constructor '''
        super(YahooDAM, self).__init__()
        self.__yf = YahooFinance()

    def readQuotes(self, symbol, start, end):
        ''' read quotes from Yahoo Financial'''
        if symbol is None:
            LOG.debug('Symbol is None')
            return None

        return self.__yf.getQuotes(symbol, start, end)
