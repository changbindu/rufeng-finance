# coding=utf-8
__author__ = 'Du, Changbin <changbin.du@gmail.com>'


import math
import datetime, time
from queue import Queue
from threading import Thread
from pymongo import MongoClient
from pandas import DataFrame
import tushare as ts
import logging

import util
from stock import Stock, Index, StockCalendar


class LocalDataManager(object):
    """we use mongodb to cache data"""
    def __init__(self):
        client = MongoClient('localhost', 27017)
        self.db = client.rufeng_finance_database
        self.stock_collection = self.db.stocks
        self.indexes_collection = self.db.indexes

    def find_one_stock(self, code):
        dstock = self.stock_collection.find_one({'code': code})
        if dstock is None:
            return None
        return self.__from_dict(dstock)

    def find_stock(self, filter=None):
        slist = []
        cursor = self.stock_collection.find(filter)
        for dstock in cursor:
            slist.append(self.__from_dict(dstock))
        return  slist

    def save_stock(self, stock, fields=None):
        if fields is None:
            sdict = self.__to_dict(stock)
            result = self.stock_collection.replace_one({'code': stock.code}, sdict, True)
            return result
        else:
            update = {}
            for k in fields:
                v = stock[k]
                if isinstance(v, DataFrame):
                    v = v.to_dict(orient='index')
                update[k] = v
            result = self.stock_collection.update_one({'code': stock.code}, {'$set': update})
            return result

    def drop_stock(self):
        self.stock_collection.drop()

    @staticmethod
    def __from_dict(data):
        stock = Stock()
        for k, v in data.items():
            if k == '_id':
                continue
            elif data[k] is not None and k in ('hist_data'):
                stock.hist_data = DataFrame.from_dict(data[k], orient='index')
            else:
                stock[k] = v
        return stock

    @staticmethod
    def __to_dict(stock):
        tmp = {}
        for k in stock.__dict__:
            v = stock.__getattribute__(k)
            if v is not None and k in ('hist_data'):
                tmp[k] = v.to_dict(orient='index')
            else:
                tmp[k] = v
        return tmp

    def find_index(self, filter=None):
        ilist = []
        cursor = self.indexes_collection.find(filter)
        for dindex in cursor:
            ilist.append(self.__from_dict(dindex))
        return ilist

    def save_index(self, index):
        idict = self.__to_dict(index)
        result = self.indexes_collection.replace_one({'code': index.code}, idict, True)
        return result

    def drop_index(self):
        self.indexes_collection.drop()


class DataManager(object):
    def __init__(self):
        self._stocks = {}
        self._indexes = {}
        self._local_dm = LocalDataManager()

    @property
    def stocks(self):
        return self._stocks

    @property
    def indexes(self):
        return self._indexes

    def pick_data(self, max_num_threads = 20, force_update = False):
        """
        pick all necessary data from local database and from internet. This function will take a while.
        """
        logging.info('getting basics from tushare')
        self._init_stock_objs()

        # self.data_manager.drop_stock()
        # self.stocks = {key: self.stocks[key] for key in ['600233', '600130']}
        logging.info('totally there are %d listed companies', len(self._stocks))

        if not force_update:
            try:
                self.load_from_db()
            except KeyError as e:
                logging.warning('%s, drop database', str(e))
                self._local_dm.drop_stock()
        else:
            logging.info('force update all stocks, ignore local database')

        # self._pick_hist_data_and_save(max_num_threads)

        logging.info('get indexes from tushare')
        self._get_indexes()

        logging.info('getting last stock trading data')
        df = ts.get_today_all()
        self._extract_from_dataframe(df,
                    ignore=('changepercent', 'open', 'high', 'low', 'settlement', 'volume', 'turnoverratio', 'amount'),
                    remap={'trade': 'price', 'per': 'pe'})

        # calculate the report quarter
        report_date = datetime.date.today() - datetime.timedelta(days=60)
        report_quarter = math.ceil(report_date.month/3.0)

        logging.info('getting last report (%d quarter %d) from tushare', report_date.year, report_quarter)
        df = ts.get_report_data(report_date.year, report_quarter)
        self._extract_from_dataframe(df)

        logging.info('getting last profit data from tushare')
        df = ts.get_profit_data(report_date.year, report_quarter)
        self._extract_from_dataframe(df, ignore=('net_profits', 'roe', 'eps'))

        logging.info('getting last operation data from tushare')
        df = ts.get_operation_data(report_date.year, report_quarter)
        self._extract_from_dataframe(df)

        logging.info('getting last growth data from tushare')
        df = ts.get_growth_data(report_date.year, report_quarter)
        self._extract_from_dataframe(df)

        logging.info('getting last debtpaying data from tushare')
        df = ts.get_debtpaying_data(report_date.year, report_quarter)
        self._extract_from_dataframe(df)

        logging.info('getting last cashflow data from tushare')
        df = ts.get_cashflow_data(report_date.year, report_quarter)
        self._extract_from_dataframe(df)

        logging.info('getting history trading data from tushare')
        data_full = self._pick_hist_data_and_save(max_num_threads)  # anything that pulling data must before here

        self._remove_unavailable_stocks()

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

        return data_full

    def _init_stock_objs(self):
        logging.info('getting stock list from tushare')
        df = ts.get_stock_basics()
        for index, row in df.iterrows():
            stock = Stock()
            stock.code = index
            for col_name in df.columns:
                # we only trust these data
                if not col_name in ('name', 'industry', 'area', 'timeToMarket'):
                    continue
                if not hasattr(stock, col_name):
                    logging.warning('Stock obj has no attribute %s, skip', col_name)
                else:
                    value = row[col_name]
                    value = util.strQ2B(value).replace(' ', '') if isinstance(value, str) else value
                    stock.__setattr__(col_name, value)
            self._stocks[stock.code] = stock

    def _get_indexes(self):
        index_map = {'000001': 'sh', '399001': 'sz', '000300': 'hs300', '000016': 'sz50', '399101': 'zxb', '399005': 'cyb'}
        logging.info('get indexes info')
        df = ts.get_index()
        for i, row in df.iterrows():
            if row['code'] in index_map:
                index = Index()
                index.code = row['code']
                index.name = row['name']
                self._indexes[index.code] = index

        for code, index in self._indexes.items():
            logging.info('get all hist data of index %s' % str(index))
            df = ts.get_hist_data(index_map[code])
            logging.info('got %d days trading data' % len(df.index))
            index.hist_data = df
            self._local_dm.save_index(index)

    def load_from_db(self):
        """load stocks from local database only"""
        logging.info('try load stock data from local database')
        count = 0
        for stock in self._local_dm.find_stock():
            self._stocks[stock.code] = stock
            count += 1
        logging.info('loaded %d stocks', count)

        count = 0
        for index in self._local_dm.find_index():
            self._indexes[index.code] = index
            count += 1
        logging.info('loaded %d indexes', count)
        self._remove_unavailable_stocks()

    def _extract_from_dataframe(self, df, ignore=(), remap={}, special_handler={}):
        if df is None or not isinstance(df, DataFrame):
            logging.error('cannot get data or wrong data -> %s!', df)
            return
        for index, row in df.iterrows():
            code = row['code']
            if not code in self._stocks:
                logging.warning('stock %s missed?', code)
                continue
            stock = self._stocks[code]
            for col_name in df.columns:
                if col_name == 'code' or col_name in ignore:
                    continue
                if col_name in special_handler:
                    special_handler[col_name](stock, df, row[col_name])
                    continue
                real_field = col_name in remap and remap[col_name] or col_name
                if not hasattr(stock, real_field):
                    logging.warning('stock obj has no attribute %s, skip', col_name)
                else:
                    old = stock.__getattribute__(real_field)
                    new = isinstance(row[col_name], str) and util.strQ2B(row[col_name]).replace(' ', '') or row[col_name]
                    new = isinstance(new, float) and round(new, 2) or new
                    if old is not None and (isinstance(old, float) and not math.isnan(old)) and \
                       new is not None and (isinstance(new, float) and not math.isnan(new)) and \
                       old != new:
                        logging.info('field %s changed: old(%s) -> new(%s), %s', col_name, str(old), str(new), stock)
                    stock.__setattr__(real_field, new)

    def _remove_unavailable_stocks(self):
        stocks_to_remove = list()
        for code, stock in self._stocks.items():
            if stock.hist_data is None or len(stock.hist_data.index) == 0:
                stocks_to_remove.append(stock)
        for stock in stocks_to_remove:
            del self._stocks[stock.code]
            logging.warning('removed unavailable stock %s (maybe not IPO yet)', stock)
        logging.info('all %d available stocks will be analyzed', len(self._stocks))

    def _pick_hist_data_and_save(self, max_num_threads):
        threads = []
        squeue = Queue()
        today = datetime.date.today()
        update_to = StockCalendar().last_complete_trade_day()
        failed = False

        for code, stock in self._stocks.items():
            if stock.hist_data is None:
                squeue.put(stock)
            elif stock.last_update <= datetime.datetime(update_to.year, update_to.month, update_to.day):
                squeue.put(stock)
            else:
                logging.debug('stock %s already updated at %s', stock, stock.last_update)
        total_to_update = squeue.qsize()

        def __pick_history():
            while not squeue.empty():
                stock = squeue.get()
                start_from = today - datetime.timedelta(days=365)

                try:
                    logging.debug('[%d/%d]picking 1 year hist data of %s', total_to_update - squeue.qsize(),
                                total_to_update, stock)
                    hist = ts.get_hist_data(stock.code, start=str(start_from), end=str(update_to), ktype='D', retry_count=5, pause=0)
                    fq_factor = ts.get_fq_factor(stock.code, start=str(start_from), end=str(update_to))  # 前复权数据
                except IOError as e:
                    logging.error('exception: %s', str(e))
                    logging.error('cannot get hist/qfq data of %s', stock)
                    failed = True
                else:
                    if hist is None:
                        logging.warning('%s has no history data', stock)
                    elif fq_factor is None:
                        logging.warning('%s has no fq data', stock)
                    else:
                        stock.hist_data = hist.join(fq_factor)

                        stock.sanitize()
                        logging.debug('%s: %d days trading data', stock, len(stock.hist_data.index))
                        stock.last_update = datetime.datetime.now()
                        self._local_dm.save_stock(stock)
                squeue.task_done()

        num_threads = min(max_num_threads, int(squeue.qsize() / 2))
        logging.info('getting history data of %d stocks using %d threads', squeue.qsize(), num_threads)
        for i in range(0, num_threads):
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
        #while squeue.unfinished_tasks:
        #    time.sleep(1)
        squeue.join()
        t_delta = datetime.datetime.now() - t_start
        if (failed):
            logging.warning('failed to pick some stocks')
        else:
            logging.info('done getting history data by %d seconds', t_delta.days*24*3600 + t_delta.seconds)
        return not failed

    def list_availabe_stocks(self):
        logging.info('all %d available stocks will be analyzed', len(self._stocks))
        for code, stock in self._stocks.items():
            logging.info('%s: price %s, %d days trading data, last update at %s',
                         stock, stock.price, len(stock.hist_data.index), stock.last_update)

    def find_one_stock_from_db(self, code):
        return self._local_dm.find_one_stock(code)