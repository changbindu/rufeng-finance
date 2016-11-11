# coding=utf-8
__author__ = 'Du, Changbin <changbin.du@gmail.com>'

import logging


class Analyzer(object):
    def __init__(self, stocks=None, indexes=None):
        self.stocks = stocks
        self.indexs = indexes

    def analyze(self):
        selected = [s for _, s in self.stocks.items()]
        global_status = False

        for stock in selected:
            if not self._analyze_single_stock(stock):
                selected.remove(stock)

        return selected, global_status

    def _analyze_index(self):
        pass

    def _analyze_single_stock(self, stock):
        """return if this stock is good"""
        # 当前价格
        if stock.price > 30:
            logging.debug('%s: price too high, %d > 30 RMB', stock, stock.price)
            return False

        # 流通市值
        if stock.nmc is not None and stock.nmc/10000 > 100:
            logging.debug('%s: nmc too high, %dY > %dY RMB', stock, stock.nmc/10000, 100)
            return False

        # 市盈率
        if stock.pe is not None and stock.pe > 400:
            logging.debug('%s: pe too high, %d > %d RMB', stock, stock.pe, 400)
            return False

        # 创业板
        if stock.code.startswith('300'):
            logging.debug('%s: is in Growth Enterprise Market', stock)
            return False

        # 5日平均换手率
        if stock.hist_len > 5:
            t5_avg = sum(stock.hist_data.turnover[0:5]/5)
            if t5_avg < 3.0:
                logging.debug('%s: 5 days average turnover %s lower than %s',stock, t5_avg, 3.0)
                return False

        # 当前走势位置
        if stock.hist_len > 60:
            min = stock.hist_data.close[:60].min()
            hratio = (stock.price-min)/min
            if hratio > 0.6:
                logging.debug('%s: current price higher than 60 days min %s %s%%', stock, min, hratio*100)
                return False

        return True
