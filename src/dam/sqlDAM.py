'''
Created on Nov 9, 2011

@author: ppa
'''
from dam.baseDAM import BaseDAM
from model.stockObjects import Quote, Tick, Fundamental, Stock, Block
import sys, os

from sqlalchemy import Column, Integer, String, Float, DateTime, Sequence, ForeignKey, create_engine, and_
from sqlalchemy.orm import sessionmaker, scoped_session, relationship, joinedload
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

import logging
LOG = logging.getLogger()

class FundamentalSql(Base):
    __tablename__ = 'fundamental'

    stock_id = Column(Integer, primary_key = True)
    sector = Column(String(12))
    industry = Column(String(50))
    summary = Column(String(50))
    totalShare = Column(Integer)
    tradableShare = Column(Integer)
    priceEarning = Column(Float)
    netAsset = Column(Float)
    income = Column(Float)
    netIncome = Column(Float)

    def __init__(self, stock_id):
        ''' constructor '''
        self.stock_id = stock_id

class QuoteSql(Base):
    __tablename__ = 'quote'

    stock_id = Column(Integer, primary_key = True)
    time = Column(DateTime, primary_key = True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    adjClose = Column(Float) # price before the XD

    def __init__(self, stock_id, time, open, high, low, close, volume, adjClose):
        ''' constructor '''
        self.stock_id = stock_id
        self.time = time
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.adjClose = adjClose

    def __repr__(self):
        return "<Quote('%s', '%s','%s', '%s', '%s','%s', '%s', '%s')>" \
           % (self.stock_id, self.time, self.open, self.high, self.low, self.close, self.volume, self.adjClose)

class TickSql(Base):
    __tablename__ = 'tick'

    stock_id = Column(Integer, primary_key = True)
    time = Column(DateTime, primary_key = True)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)

    def __init__(self, stock_id, time, open, high, low, close, volume):
        ''' constructor '''
        self.stock_id = stock_id
        self.time = time
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume

    def __repr__(self):
        return "<Tick('%s', '%s', '%s', '%s', '%s', '%s', '%s')>" \
           % (self.stock_id, self.time, self.open, self.high, self.low, self.close, self.volume)

class StockSql(Base):
    __tablename__ = 'stock'

    id = Column(Integer, primary_key = True)
    symbol = Column(String(12), unique = True)
    name = Column(String(20))
    price = Column(Float)
    lastUpdate = Column(DateTime)

    def __init__(self, symbol, name, price):
        ''' constructor '''
        self.symbol = symbol
        self.name = name
        self.price = price

class SqlDAM(BaseDAM):
    '''
    SQL DAM
    '''
    def __init__(self, echo = False):
        ''' constructor '''
        super(SqlDAM, self).__init__()
        self.echo = echo
        self.engine = None
        self.readSession = None
        self.writeSession = None

    def setup(self, setting):
        ''' set up '''
        if 'db' not in setting:
            raise Exception("db not specified in setting")
        dir = os.path.split(os.path.realpath(setting['db'].strip("sqlite:///")))[0]
        if not os.path.exists(dir):
            os.makedirs(dir)
        self.engine = create_engine(setting['db'], echo = self.echo)
        self.readSession = scoped_session(sessionmaker(bind = self.engine))
        sessionMaker = sessionmaker(bind = self.engine)
        self.writeSession = sessionMaker()
        Base.metadata.create_all(self.engine, checkfirst = True)

    def readAllStocks(self):
        try:
            rows = self.readSession.query(StockSql)
        finally:
            self.readSession.remove()

        return [Stock(row.symbol, row.name, row.price) for row in rows]

    def __readStock(self, symbol):
        try:
            stocksql = self.readSession.query(StockSql).filter(and_(StockSql.symbol == symbol)).first()
        finally:
            self.readSession.remove()

        if stocksql is None:
            return None
        return stocksql

    def readStock(self, symbol):
        stocksql = self.__readStock(symbol)
        if stocksql is None:
            return None
        return Stock(stocksql.symbol, stocksql.name, stocksql.price)

    def writeStock(self, stock):
        ''' write quotes '''
        self.writeSession.add(StockSql(stock.symbol, stock.name, stock.price))

    def readQuotes(self, symbol, start, end):
        ''' read quotes '''
        if end is None:
            end = sys.maxint

        stockSql = self.__readStock(symbol)
        try:
            rows = self.readSession.query(QuoteSql).filter(and_(QuoteSql.stock_id == stockSql.id,
                                    QuoteSql.time >= start, QuoteSql.time < end))
        finally:
            self.readSession.remove()

        return [Quote(row.time, row.open, row.high, row.low, row.close, row.volume, row.adjClose) for row in rows]

    def writeQuotes(self, symbol, quotes):
        ''' write quotes '''
        stockSql = self.__readStock(symbol)
        self.writeSession.add_all([QuoteSql(stockSql.id, quote.time, quote.open, quote.high, quote.low,
                                quote.close, quote.volume, quote.adjClose) for quote in quotes])

    def commit(self):
        ''' commit changes '''
        self.writeSession.commit()

    def __del__(self):
        ''' destructor '''
        if self.readSession:
            self.readSession.close()
        if self.writeSession:
            self.writeSession.close()
