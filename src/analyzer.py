# coding=utf-8
__author__ = 'Du, Changbin <changbin.du@gmail.com>'

import math
import logging
from threadpool import ThreadPool, makeRequests


class Analyzer(object):
    def __init__(self, stocks, indexes, config):
        self.stocks = stocks
        self.indexs = indexes

        self.config_min_hist_data = max(config['min_hist_data'], 10)
        self.config_max_price = config['max_price']
        self.config_max_nmc = config['max_nmc']
        self.config_max_mktcap = config['max_mktcap']
        self.config_max_pe = config['max_pe']
        self.config_exclude_gem = config['exclude_gem']
        self.config_exclude_suspension = config['exclude_suspension']
        self.config_exclude_st = config['exclude_st']
        self.config_min_d5_turnover_avg = config['min_d5_turnover_avg']
        self.config_position = config['position']

    def analyze(self, threads=1):
        self._selected = []
        global_status = self._analyze_index()

        pool = ThreadPool(threads)
        requests = makeRequests(self._analyze_single_stock, [s for _, s in self.stocks.items()])
        [pool.putRequest(req) for req in requests]
        pool.wait()

        return self._selected, global_status

    def _analyze_index(self):
        return False

    def _analyze_single_stock(self, stock):
        """return if this stock is good"""
        hist_data = stock.hist_data

        # 创业板
        if self.config_exclude_gem and stock.code.startswith('300'):
            logging.debug('%s: is in Growth Enterprise Market' % stock)
            return False

        # 停牌
        if self.config_exclude_suspension and math.isnan(stock.price):
            logging.debug('%s: is suspending' % stock)
            return False

        # ST
        if self.config_exclude_st and stock.name.startswith('*ST'):
            logging.debug('%s: is Special Treatment (ST)' % stock)
            return False

        if stock.hist_len < self.config_min_hist_data:
            logging.debug('%s: only %d days history data' % (stock, stock.hist_len))
            return False

        # 最新价格
        if hist_data.close[0] > self.config_max_price:
            logging.debug('%s: price is too high, %d RMB' % (stock, hist_data.close[0]))
            return False

        # 流通市值
        if stock.nmc is not None and stock.nmc/10000 > self.config_max_nmc:
            logging.debug('%s: circulated market value is too high, %dY RMB' % (stock, stock.nmc/10000))
            return False

        # 总市值
        if stock.mktcap is not None and stock.mktcap/10000 > self.config_max_mktcap:
            logging.debug('%s: total market cap value is too high, %dY RMB' % (stock, stock.mktcap/10000))
            return False

        # 市盈率
        if stock.pe is not None and stock.pe > self.config_max_pe:
            logging.debug('%s: pe is too high, %d' % (stock, stock.pe))
            return False

        # 5日平均换手率
        d5_avg = stock.get_turnover_avg(5)
        if d5_avg < self.config_min_d5_turnover_avg:
            logging.debug('%s: 5 days average turnover is too low, %.2f%%' % (stock, d5_avg))
            return False

        # delay this until we really need
        qfq_data = stock.qfq_data

        # 当前走势位置
        if stock.hist_len > 60:
            min = qfq_data.close[:60].min()
            hratio = (qfq_data.close[0]-min)/min
            if hratio > self.config_position[0]:
                logging.debug('%s: current price is higher than 60 days min %.2f %.2f%%' % (stock, min, hratio*100))
                return False
        if stock.hist_len > 420:
            max = qfq_data.close[:420].max()
            hratio = (max - qfq_data.close[0]) / qfq_data.close[0]
            if hratio < self.config_position[1]:
                logging.debug('%s: 420 days max %.2f is only higher than current %.2f%%' % (stock, max, hratio*100))
                return False

        self._selected.append(stock)
        return True
