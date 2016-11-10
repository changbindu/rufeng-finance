'''
Created on Nov 9, 2011

@author: ppa
'''
from dam.baseDAM import BaseDAM
from dam.eastmoneyFinance import EastmoneyFinance
from model.stockObjects import Stock

import logging
LOG = logging.getLogger()

class EastmoneyDAM(BaseDAM):
    ''' Yahoo DAM '''

    def __init__(self):
        ''' constructor '''
        super(EastmoneyDAM, self).__init__()
        self.__ef = EastmoneyFinance()

    def readAllStocks(self):
        ''' list all stocks in market '''
        symbols = self.__ef.getAllStockSymbols()
        return [Stock(s, symbols[s], 0.0) for s in symbols]
