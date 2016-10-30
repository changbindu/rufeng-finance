# coding=utf-8
__author__ = 'Du, Changbin <changbin.du@gmail.com>'

import sys
import datetime
from queue import Queue
from threading import Thread
import logging.config, coloredlogs
from pandas import DataFrame
import tushare as ts

import util
from stock import Stock


class RufengFinance(object):
    def __init__(self, logger):
        self.logger = logger
        self.num_threads = 20
        self.stocks = {}

    def main(self):
        logger.info('getting basics')
        df = ts.get_stock_basics()
        for index, row in df.iterrows():
            stock = Stock()
            stock.code = index
            for col_name in df.columns:
                if not hasattr(stock, col_name):
                    # fix tushare
                    if col_name == 'esp':
                        stock.eps = row['esp']
                        continue
                    else:
                        logger.warn('Stock obj has no attribute ' + col_name)
                value = row[col_name]
                value = util.strQ2B(value).replace(' ', '') if isinstance(value, str) else value
                if isinstance(value, str) and value == 'nan':
                    value = None
                stock.__setattr__(col_name, value)
            self.stocks[stock.code] = stock

        #self.stocks = {key: self.stocks[key] for key in ['600233', '600130']}
        logger.info('totally there are %d listed companies', len(self.stocks))

        self.pick_hist_data()
        #tmp = self.stocks['600233'].to_dict()

        logger.info('getting last report')
        df = ts.get_report_data(2014, 3)
        self.extract_from_dataframe(df)

        logger.info('getting last profit data')
        df = ts.get_profit_data(2014, 3)
        self.extract_from_dataframe(df)

        logger.info('getting last operation data')
        df = ts.get_operation_data(2014, 3)
        self.extract_from_dataframe(df)

        logger.info('getting last growth data')
        df = ts.get_growth_data(2014, 3)
        self.extract_from_dataframe(df)

        logger.info('getting last debtpaying data')
        df = ts.get_debtpaying_data(2014, 3)
        self.extract_from_dataframe(df)

        logger.info('getting last cashflow data')
        df = ts.get_cashflow_data(2014, 3)
        self.extract_from_dataframe(df)

        self.pick_hist_data()

        stocks_to_remove = list()
        for code, stock in self.stocks.items():
            if stock.hist_data is None:
                stocks_to_remove.append(stock)
        for stock in stocks_to_remove:
            del self.stocks[stock.code]
            logger.warn('removed unavailable stock %s (maybe not IPO yet)', stock)

        # dump basics of all stocks
        logger.info('all %d available stocks:', len(self.stocks))
        for code, stock in self.stocks.items():
            stock.price = stock.hist_data[-1:]['close']
            logger.info('%s: %d trading days data', stock, len(stock.hist_data.index))
        return 0

    def extract_from_dataframe(self, df):
        if df is None or not isinstance(df, DataFrame):
            logger.error('cannot get date or wrong data -> %s!', df)
            return
        for index, row in df.iterrows():
            code = row['code']
            if not code in self.stocks:
                logger.warn('stock %s missed?', code)
                continue
            stock = self.stocks[code]
            for col_name in df.columns:
                if col_name == 'code':
                    continue
                if not hasattr(stock, col_name):
                    logger.warn('stock obj has no attribute ' + col_name)
                else:
                    old = stock.__getattribute__(col_name)
                    new = isinstance(row[col_name], str) and util.strQ2B(row[col_name]).replace(' ', '') or row[col_name]
                    if isinstance(new, str) and new == 'nan':
                        new = None
                    if old is not None and new is not None and old != new:
                        logger.fatal('corrupted data from tushare, %s: old(%s) != new(%s)', col_name, str(old), str(new))
                stock.__setattr__(col_name, row[col_name])

    def pick_hist_data(self):
        threads = []
        squeue = Queue()
        for code in self.stocks:
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
