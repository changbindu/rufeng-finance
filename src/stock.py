# coding=utf-8
__author__ = 'Du, Changbin <changbin.du@gmail.com>'

import json
import datetime
import logging
from collections import MutableMapping
import numpy as np
from pandas import DataFrame

class StockBase(object):
    def __init__(self, code=None, name=None):
        # Basic info
        self.code = code  # 代码
        self.name = name  # 名称

        # data and update info
        self.last_update = None
        self.hist_data = None # DataFrame

    def __str__(self):
        ''' convert to string '''
        return json.dumps({"code": self.code,
                           "name": self.name,
                          }, ensure_ascii = False)

    def __getitem__(self, key):
        if key not in self.__dict__:
            raise KeyError
        return self.__getattribute__(key)

    def __setitem__(self, key, value):
        if key not in self.__dict__:
            raise KeyError('key %s is invalid' % key)
        return self.__setattr__(key, value)

    def __delitem__(self, key):
        raise NotImplementedError

    def __len__(self):
        return len(self.__dict__)

    def __iter__(self):
        return self.__dict__.__iter__()

    def sanitize(self):
        if self.hist_data is not None:
            # self.hist_data.index = self.hist_data.index.map(np.datetime64)
            self.hist_data.index = self.hist_data.index.map(str)
            self.hist_data.sort_index(ascending=False, inplace=True)

    def check(self):
        pass

    @property
    def hist_len(self):
        return self.hist_data is None and 0 or self.hist_data.index.size

    @property
    def hist_max(self):
        return self.hist_data.high.max()

    @property
    def hist_min(self):
        return self.hist_data.low.min()

    @property
    def hist_start_date(self):
        return np.datetime64(self.hist_data.index[-1], 'D')

    @property
    def hist_last_date(self):
        return np.datetime64(self.hist_data.index[0], 'D')

    @property
    def ma30(self):
        return self._get_ma(30)

    @property
    def ma60(self):
        return self._get_ma(60)

    @property
    def ma120(self):
        return self._get_ma(120)

    @property
    def ma240(self):
        return self._get_ma(240)

    def _get_ma(self, window):
        df = self.hist_data[['open', 'close', 'low', 'high', 'volume', 'turnover']].sort_index(ascending=True)
        r = df.rolling(window=window)
        df = r.mean()
        df.sort_index(ascending=False, inplace=True)
        return df

    def get_hist_date(self, loc):
        return self.hist_data.index[loc]

    def get_turnover_avg(self, days):
        return self.hist_data.turnover[0:days].mean()


class Stock(StockBase):
    st_prefix = ('*ST', 'ST', 'S*ST', 'SST')

    ''' stock class'''
    def __init__(self, code=None, name=None):
        super(Stock, self).__init__(code=code, name=name)
        # Basics
        self.industry = None # 所属行业
        self.area = None # 地区
        self.pe = None # 市盈率
        self.outstanding = None # 流通股本
        self.nmc = None # 流通市值(万元)
        self.totals = None # 总股本(万)
        self.mktcap = None # 总市值(万元)
        self.totalAssets = None # 总资产(万)
        self.liquidAssets = None # 流动资产
        self.fixedAssets = None # 固定资产
        self.reserved = None # 公积金
        self.reservedPerShare = None # 每股公积金
        self.eps = None # 每股收益
        self.eps_yoy = None # 每股收益同比( %)
        self.bvps = None # 每股净资
        self.pb = None # 市净率
        self.timeToMarket = None # 上市日期
        self.roe = None # 净资产收益率( %)
        self.epcf = None # 每股现金流量(元)
        self.net_profits = None # 净利润(万元)
        self.profits_yoy = None # 净利润同比( %)
        self.net_profit_ratio = None # 净利率( %)
        self.gross_profit_rate = None # 毛利率( %)
        self.business_income = None # 营业收入(百万元)
        self.bips = None # 每股主营业务收入(元)
        self.distrib = None # 分配方案
        self.report_date = None # 发布日期
        self.arturnover = None # 应收账款周转率(次)
        self.arturndays = None # 应收账款周转天数(天)
        self.inventory_turnover = None # 存货周转率(次)
        self.inventory_days = None # 存货周转天数(天)
        self.currentasset_turnover = None # 流动资产周转率(次)
        self.currentasset_days = None # 流动资产周转天数(天)
        self.mbrg = None # 主营业务收入增长率( %)
        self.nprg = None # 净利润增长率( %)
        self.nav = None # 净资产增长率
        self.targ = None # 总资产增长率
        self.epsg = None # 每股收益增长率
        self.seg = None # 股东权益增长率
        self.currentratio = None # 流动比率
        self.quickratio = None # 速动比率
        self.cashratio = None # 现金比率
        self.icratio = None # 利息支付倍数
        self.sheqratio = None # 股东权益比率
        self.adratio = None # 股东权益增长率
        self.cf_sales = None # 经营现金净流量对销售收入比率
        self.rateofreturn = None # 资产的经营现金流量回报率
        self.cf_nm = None # 经营现金净流量与净利润的比率
        self.cf_liabilities = None # 经营现金净流量对负债比率
        self.cashflowratio = None # 现金流量比率

        self.price = float('NaN')

    def sanitize(self):
        super(Stock, self).sanitize()

    @property
    def qfq_data(self):
        """warning: calculate qfq data is expensive"""
        max_factor = self.hist_data.factor[0]

        df = self.hist_data[['open', 'close', 'low', 'high']]
        df = df.div(max_factor/self.hist_data.factor, axis='index')
        df = df.join(self.hist_data[['volume', 'turnover', 'factor']])
        df.sort_index(ascending=False, inplace=True)

        assert df.index.size == self.hist_data.index.size
        return df

    def get_hist_value(self, column, date):
        return self.hist_data[column][date]

    def check(self):
        if self.hist_data.size == 0:
            logging.warning('no data in hist_data')
            return False
        df_nan = self.hist_data[self.hist_data.isnull().any(axis=1)]
        if df_nan.index.size > 0:
            logging.warning('found nan in hist_data\n%s' % df_nan)
            return False

        if self.hist_data.index.has_duplicates:
            logging.warning('found duplicates\n%s' % self.hist_data.index.get_duplicates())
            return False
        return True


class Index(StockBase):
    index_name_map = {'000001': ('sh', '上证指数'),
                      '399001': ('sz', '深圳成指'),
                      '000300': ('hs300', '沪深300指数'),
                      '000016': ('sz50', '上证50'),
                      '399101': ('zxb', '中小板'),
                      '399005': ('cyb', '创业板')
                      }

    def __init__(self, code=None, name=None, symbol=None):
        super(Index, self).__init__(code=code, name=name)
        self.symbol = symbol


class StockCalendar(object):
    def __init__(self):
        pass

    def is_trading_day(self, date=datetime.date.today()):
        # quick check
        if date.weekday() > 5:
            return False
        # check from history
        #if str(date) not in self.sz_index.hist_date.index:
        #        return False
        return True

    def is_trading_now(self):
        if not self.is_trading_day():
            return False
        now = datetime.now()
        t1 = datetime(now.year, now.month, now.day, 9, 30)
        t2 = datetime(now.year, now.month, now.day, 11, 30)
        t3 = datetime(now.year, now.month, now.day, 13, 0)
        t4 = datetime(now.year, now.month, now.day, 15, 0)

        def time_in(t, t1, t2):
            return (t-t1).total_seconds() >= 0 and (t2-t).total_seconds() > 0

        return time_in(now, t1, t2) or time_in(now, t3, t4)

    def last_completed_trade_day(self):
        today = datetime.date.today()
        if self.is_trading_day() and datetime.datetime.now().hour > 13:
            return today
        for i in range(1, 7):
            date = today-datetime.timedelta(days=i)
            if self.is_trading_day(date):
                return date
