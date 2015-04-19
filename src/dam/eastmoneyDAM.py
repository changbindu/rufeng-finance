'''
Created on Nov 9, 2011

@author: ppa
'''
from dam.baseDAM import BaseDAM
from dam.eastmoneyFinance import EastmoneyFinance

import logging
LOG = logging.getLogger()

class EastmoneyDAM(BaseDAM):
    ''' Yahoo DAM '''

    def __init__(self):
        ''' constructor '''
        super(EastmoneyDAM, self).__init__()
        self.__ef = EastmoneyFinance()

    def listSymbols(self):
        ''' list all stocks in market '''
        return self.__ef.getAllStockSymbols()
