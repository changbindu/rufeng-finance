# coding=utf-8
__author__ = 'Du, Changbin <changbin.du@gmail.com>'

import logging


class Analyzer(object):
    def __init__(self, stocks=None, indexes=None):
        self.stocks = stocks
        self.indexs = indexes

    def analyze(self):
        selected = [s for _, s in self.stocks.items()]

        for stock in selected:
            if not self._analyze_single_stock(stock):
                selected.remove(stock)

        logging.info('list of good %d stocks:', len(selected))
        for stock in selected:
            logging.info('%s', stock)

    def _analyze_index(self):
        pass

    def _analyze_single_stock(self, stock):
        """return if this stock is good"""
        if stock.price > 30:
            logging.debug('%s: price too high, %d > 30', stock, stock.price)
            return False
        return True
