# coding=utf-8
__author__ = 'Du, Changbin <changbin.du@gmail.com>'

import sys
if sys.version_info < (3, 4):
    raise RuntimeError('at least Python 3.4 is required to run')
sys.path.insert(0, 'tushare')

import math
import time
import datetime
from threading import Thread
import logging.config, coloredlogs
import tushare as ts

import util


class Stock(object):
    def __init__(self):
        self.code = None
        self.name = None
        self.config = {}

    def __str__(self):
        return '%s(%s)' % (self.code, self.name)

class StockMonitor(object):
    def __init__(self, logger, stock_configs):
        self.logger = logger
        self.stocks = {}
        for k, v in stock_configs.items():
            stock = Stock()
            stock.code = k
            stock.config = v
            self.stocks[k] = stock
        self.thread = Thread(name="MonitorThread", target=self._monitor_func)

    def start_and_join(self):
        self._get_stock_names()
        sstr = ''
        for code, stock in self.stocks.items():
            sstr += str(stock) + ' '
        logger.info('start monitor: ' + sstr)
        self.thread.start()
        self.thread.join()

    def _get_stock_names(self):
        logger.info('getting stock basics from tushare')
        df = ts.get_stock_basics()
        for index, row in df.iterrows():
            if index in self.stocks:
                self.stocks[index].name = util.strQ2B(row['name']).replace(' ', '')


    def _monitor_func(self):
        while True:
            today = datetime.date.today()
            indexes = ts.get_realtime_quotes(['sh', 'sz', 'hs300', 'sz50', 'zxb', 'cyb'])
            for code, stock in self.stocks.items():
                quotes = ts.get_realtime_quotes(code)
                self._monitor_policy(stock, quotes.to_dict(orient='index')[0], indexes)
            time.sleep(3)

    def _monitor_policy(self, stock, quotes, indexes):
        if float(quotes['price']) > stock.config['high']:
            logger.info('%s: price high than %s now' % (stock, stock.config['high']))


if __name__ == '__main__':
    coloredlogs.DEFAULT_LOG_FORMAT = '%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s'
    coloredlogs.install(level='DEBUG')
    logger = logging.getLogger("root")

    stock_configs = {
        '002341': {'high': 20.0, 'low': 19.0, 'up_percent': 5.0, 'down_percent': -5.0},
        '300195': {'high': 19.0, 'low': 18.0, 'up_percent': 5.0, 'down_percent': -5.0},
    }

    StockMonitor(logger, stock_configs).start_and_join()
    logger.info("exiting...")
