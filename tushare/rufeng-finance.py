# coding=utf-8
__author__ = 'Du, Changbin <changbin.du@gmail.com>'

import sys
if sys.version_info < (3, 4):
    raise RuntimeError('at least Python 3.4 is required to run')
sys.path.insert(0, 'tushare')

import math
import datetime
from queue import Queue
from threading import Thread
import logging.config, coloredlogs
from pymongo import MongoClient
from pandas import DataFrame
import tushare as ts

import util
from stock import Stock


class DataManager(object):
    def __init__(self):
        client = MongoClient('localhost', 27017)
        self.db = client.rufeng_finance_database
        self.stock_collection = self.db.stocks
        self.indexes_collection = self.db.indexes

    def find_one_stock(self, code):
        cursor = self.stock_collection.find_one({'code': code})
        if cursor is None:
            return None
        return self._stock_from_dict(cursor[0])

    def find_stock(self, filter=None):
        slist = []
        cursor = self.stock_collection.find(filter)
        for dstock in cursor:
            slist.append(self._stock_from_dict(dstock))
        return  slist

    def save_stock(self, stock):
        stock.last_update = datetime.datetime.now()
        sdict = self._stock_to_dict(stock)
        result = self.stock_collection.replace_one({'code': stock.code}, sdict, True)
        return result

    def drop_stock(self):
        self.stock_collection.drop()

    @staticmethod
    def _stock_from_dict(data):
        stock = Stock()
        for k, v in data.items():
            if k == '_id':
                continue
            elif k == 'hist_data':
                stock.hist_data = DataFrame.from_dict(data[k], orient='index')
            else:
                stock[k] = v
        return stock

    @staticmethod
    def _stock_to_dict(stock):
        tmp = {}
        for key in stock.__dict__:
            if key == 'hist_data':
                tmp[key] = stock.hist_data.to_dict(orient='index')
            else:
                tmp[key] = stock.__getattribute__(key)
        return tmp


class RufengFinance(object):
    def __init__(self, logger):
        self.logger = logger
        self.num_threads = 20
        self.stocks = {}
        self.data_manager = DataManager()
        self.force_update = False

    def main(self):
        logger.info('getting basics from tushare')
        self.init_stock_objs()

        # self.data_manager.drop_stock()
        # self.stocks = {key: self.stocks[key] for key in ['600233', '600130']}
        logger.info('totally there are %d listed companies', len(self.stocks))

        if not self.force_update:
            logger.info('try load stock data from local database first')
            self.load_from_db()
        else:
            logger.info('force update all stocks to local database')

        logger.info('getting last trading data')
        df = ts.get_today_all()
        self.extract_from_dataframe(df,
                    ignore=('changepercent', 'open', 'high', 'low', 'settlement', 'volume', 'turnoverratio', 'amount'),
                    remap={'trade': 'price', 'per': 'pe'})

        # calculate the report quarter
        report_date = datetime.date.today() - datetime.timedelta(days=60)
        report_quarter = math.ceil(report_date.month/3.0)

        logger.info('getting last report (%d quarter %d) from tushare', report_date.year, report_quarter)
        df = ts.get_report_data(report_date.year, report_quarter)
        self.extract_from_dataframe(df)

        logger.info('getting last profit data from tushare')
        df = ts.get_profit_data(report_date.year, report_quarter)
        self.extract_from_dataframe(df, ignore=('net_profits', 'roe', 'eps'))

        logger.info('getting last operation data from tushare')
        df = ts.get_operation_data(report_date.year, report_quarter)
        self.extract_from_dataframe(df)

        logger.info('getting last growth data from tushare')
        df = ts.get_growth_data(report_date.year, report_quarter)
        self.extract_from_dataframe(df)

        logger.info('getting last debtpaying data from tushare')
        df = ts.get_debtpaying_data(report_date.year, report_quarter)
        self.extract_from_dataframe(df)

        logger.info('getting last cashflow data from tushare')
        df = ts.get_cashflow_data(report_date.year, report_quarter)
        self.extract_from_dataframe(df)

        logger.info('getting history trading data from tushare')
        self.pick_hist_data()

        stocks_to_remove = list()
        for code, stock in self.stocks.items():
            if stock.hist_data is None or len(stock.hist_data.index) == 0:
                stocks_to_remove.append(stock)
        for stock in stocks_to_remove:
            del self.stocks[stock.code]
            logger.warn('removed unavailable stock %s (maybe not IPO yet)', stock)

        # dump basics of all stocks
        logger.info('all %d available stocks, saving to local database', len(self.stocks))
        for code, stock in self.stocks.items():
            logger.info('%s: %d trading days data', stock, len(stock.hist_data.index))
            # stock.price = stock.hist_data[-1:]['close'][0]
            self.data_manager.save_stock(stock)

        '''
        # calculate qianfuquan data
        # deprecated due to precision issue

        for code, stock in self.stocks.items():
            for i in range(1, len(stock.hist_data.index)-1):
                b = stock.hist_data.at[stock.hist_data.index[i], 'close']
                a = stock.hist_data.at[stock.hist_data.index[i+1], 'close']
                p = stock.hist_data.at[stock.hist_data.index[i+1], 'p_change'] / 100.0

                q = (p*a+a)/b
                if q > 1.1:
                    print('%s chuq-uan %s: %s %s %s, 1/%s' % (stock, stock.hist_data.index[i], b, a, p, q))
        '''
        return 0

    def init_stock_objs(self):
        logger.info('getting stock basics from tushare')
        df = ts.get_stock_basics()
        for index, row in df.iterrows():
            stock = Stock()
            stock.code = index
            for col_name in df.columns:
                # we only trust these data
                if not col_name in ('name', 'industry', 'area'):
                    continue
                if not hasattr(stock, col_name):
                    logger.warn('Stock obj has no attribute %s, skip', col_name)
                else:
                    value = row[col_name]
                    value = util.strQ2B(value).replace(' ', '') if isinstance(value, str) else value
                    stock.__setattr__(col_name, value)
            self.stocks[stock.code] = stock

    def load_from_db(self):
        for stock in self.data_manager.find_stock():
            delta = datetime.datetime.now() - stock.last_update
            if delta < datetime.timedelta(hours=12):
                self.stocks[stock.code] = stock
                logger.debug('stock %s is already updated at %s', stock, stock.last_update)

    def extract_from_dataframe(self, df, ignore=(), remap={}, special_handler={}):
        if df is None or not isinstance(df, DataFrame):
            logger.error('cannot get data or wrong data -> %s!', df)
            return
        for index, row in df.iterrows():
            code = row['code']
            if not code in self.stocks:
                logger.warn('stock %s missed?', code)
                continue
            stock = self.stocks[code]
            for col_name in df.columns:
                if col_name == 'code' or col_name in ignore:
                    continue
                if col_name in special_handler:
                    special_handler[col_name](stock, df, row[col_name])
                    continue
                real_field = col_name in remap and remap[col_name] or col_name
                if not hasattr(stock, real_field):
                    logger.warn('stock obj has no attribute %s, skip', col_name)
                else:
                    old = stock.__getattribute__(real_field)
                    new = isinstance(row[col_name], str) and util.strQ2B(row[col_name]).replace(' ', '') or row[col_name]
                    new = isinstance(new, float) and round(new, 2) or new
                    if old is not None and (isinstance(old, float) and not math.isnan(old)) and \
                       new is not None and (isinstance(new, float) and not math.isnan(new)) and \
                       old != new:
                        logger.info('field %s changed: old(%s) -> new(%s), %s',
                                     col_name, str(old), str(new), stock)
                    stock.__setattr__(real_field, new)

    def pick_hist_data(self):
        threads = []
        squeue = Queue()
        for code, stock in self.stocks.items():
            if stock.hist_data is None:
                squeue.put(self.stocks[code])

        h_end = datetime.date.today()
        h_start = h_end - datetime.timedelta(days=365)

        def __pick_history():
            while not squeue.empty():
                stock = squeue.get()
                logger.debug('[%d/%d]picking hist data of %s', len(self.stocks) - squeue.qsize(),
                             len(self.stocks), stock)
                try:
                    hist = ts.get_hist_data(stock.code, start=str(h_start), end=str(h_end), ktype='D', retry_count=5, pause=0)
                    qfq = None # ts.get_h_data(stock.code, start=str(h_start), end=str(h_end))  # 前复权数据
                except Exception as e:
                    logger.error('exception: %s', str(e))
                    hist = qfq = None

                if hist is None:
                    logger.error('cannot get hist data of %s', stock)

                stock.hist_data = hist
                stock.hist_qfq = qfq
                squeue.task_done()

        logger.info('getting history data from %s to %s using %d threads', h_start, h_end, self.num_threads)
        for i in range(0, self.num_threads):
                thread = Thread(name = "PickingThread%d" % i, target=__pick_history)
                thread.daemon = True
                threads.append(thread)
        for t in threads:
            t.start()
        '''
       for t in threads:
            t.join(timeout=None) # no need to block, because thread should complete at last
            if t.is_alive():
                logger.warning("Thread %s timeout" %t.name)
       '''
        t_start = datetime.datetime.now()
        squeue.join()
        t_delta = datetime.datetime.now() - t_start
        logger.info('done getting history data by %d seconds', t_delta.days*24*3600 + t_delta.seconds)


if __name__ == '__main__':
    coloredlogs.DEFAULT_LOG_FORMAT = '%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s'
    coloredlogs.install(level='DEBUG')

    logger = logging.getLogger("root")
    ret = RufengFinance(logger).main()
    logger.info("exiting...")
    exit(ret)
