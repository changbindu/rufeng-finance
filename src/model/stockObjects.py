'''
Created on Nov 6, 2011

@author: ppa
'''
import json
from collections import namedtuple
from lib.errors import UfException, Errors
from enum import Enum

class Fundamental(object):
    ''' fundamental class '''
    def __init__(self):
        self.sector = None
        self.industry = None
        self.summary = None
        self.totalShare = 0
        self.tradableShare = 0
        self.priceEarning = 0
        self.netAsset = 0
        self.income = 0
        self.netIncome = 0

class Tick(object):
    ''' tick class '''
    def __init__(self, time, open, high, low, close, volume):
        ''' constructor '''
        self.time = time # DateTime
        self.open = float(open)
        self.high = float(high)
        self.low = float(low)
        self.close = float(close)
        self.volume = int(volume)

    def __str__(self):
        ''' convert to string '''
        return json.dumps({"time": self.time,
                           "open": self.open,
                           "high": self.high,
                           "low": self.low,
                           "close": self.close,
                           "volume": self.volume})

    @staticmethod
    def fromStr(string):
        ''' convert from string'''
        d = json.loads(string)
        return Tick(d['time'], d['open'], d['high'],
                    d['low'], d['close'], d['volume'], d['adjClose'])

class Quote(object):
    ''' tick class '''
    def __init__(self, time, open, high, low, close, volume, adjClose):
        ''' constructor '''
        self.time = time # DateTime
        self.open = 0 if ("-" == open) else float(open)
        self.high = 0 if ("-" == high) else float(high)
        self.low = 0 if ("-" == low) else float(low)
        self.close = 0 if ("-" == close) else float(close)
        self.volume = int(volume)
        self.adjClose = adjClose

    def __str__(self):
        ''' convert to string '''
        return json.dumps({"time": self.time,
                           "open": self.open,
                           "high": self.high,
                           "low": self.low,
                           "close": self.close,
                           "volume": self.volume,
                           "adjClose": self.adjClose})

    @staticmethod
    def fromStr(string):
        ''' convert from string'''
        d = json.loads(string)
        return Quote(d['time'], d['open'], d['high'],
                     d['low'], d['close'], d['volume'], d['adjClose'])

class Stock(object):
    ''' stock class'''
    def __init__(self, symbol, name, price, lastUpdate=None):
        self.symbol = symbol
        self.name = name
        self.price = price
        self.fundamental = None
        self.history = None
        self.lastUpdate = lastUpdate

class Block(Stock):
    ''' stock bock '''
    pass
