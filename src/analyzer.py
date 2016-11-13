# coding=utf-8
__author__ = 'Du, Changbin <changbin.du@gmail.com>'

import math
import logging


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
        hist_data = stock.hist_data
        qfq_data = stock.qfq_data

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
            logging.debug('%s: price too high, %d RMB' % (stock, hist_data.close[0]))
            return False

        # 流通市值
        if stock.nmc is not None and stock.nmc/10000 > self.config_max_nmc:
            logging.debug('%s: circulated market value too high, %dY RMB' % (stock, stock.nmc/10000))
            return False

        # 总市值
        if stock.mktcap is not None and stock.mktcap/10000 > self.config_max_mktcap:
            logging.debug('%s: total market cap value too high, %dY RMB' % (stock, stock.mktcap/10000))
            return False

        # 市盈率
        if stock.pe is not None and stock.pe > self.config_max_pe:
            logging.debug('%s: pe too high, %d' % (stock, stock.pe))
            return False

        # 5日平均换手率
        d5_avg = stock.get_turnover_avg(5)
        if d5_avg < self.config_min_d5_turnover_avg:
            logging.debug('%s: 5 days average turnover too low, %.2f%%' % (stock, d5_avg))
            return False

        # 当前走势位置
        if stock.hist_len > 60:
            min = qfq_data.close[:60].min()
            hratio = (qfq_data.close[0]-min)/min
            if hratio > self.config_position[0]:
                logging.debug('%s: current price higher than 60 days min %.2f %.2f%%' % (stock, min, hratio*100))
                return False
        if stock.hist_len > 420:
            max = qfq_data.close[:420].max()
            hratio = (max - qfq_data.close[0]) / qfq_data.close[0]
            if hratio < self.config_position[1]:
                logging.debug('%s: 420 days max %.2f only higher than current %.2f%%' % (stock, max, hratio*100))
                return False

        return True
