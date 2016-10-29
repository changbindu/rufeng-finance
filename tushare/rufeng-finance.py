# coding=utf-8
__author__ = 'Du, Changbin <changbin.du@gmail.com>'

import sys
import logging.config, coloredlogs
from pandas import DataFrame
import tushare as ts

from Stock import Stock


class RufengFinance(object):
    def __init__(self, logger):
        self.logger = logger
        self.stocks = {}

    def main(self):
        logger.info('getting basics')
        df = ts.get_stock_basics()
        for index, row in df.iterrows():
            stock = Stock()
            stock.code = index
            for col_name in df.columns:
                if (not hasattr(stock, col_name)):
                    logger.warn('Stock obj has no attribute ' + col_name)
                stock.__setattr__(col_name, row[col_name])
            self.stocks[stock.code] = stock

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

        logger.info('getting history data')
        for code in self.stocks:
            df = ts.get_hist_data(code, start='2015-01-05', end='2015-01-09')
            self.stocks[code].hist_data = df

        # dump basics of all stocks
        for code in self.stocks:
            logger.debug(self.stocks[code])
        return 0

    def extract_from_dataframe(self, df):
        if df is None or not isinstance(df, DataFrame):
            logger.error("Cannot get date or wrong data!")
            return
        for index, row in df.iterrows():
            code = row['code']
            if not self.stocks.has_key(code):
                logger.warn('stock %s missed?', code)
                continue
            stock = self.stocks[code]
            for col_name in df.columns:
                if col_name == 'code':
                    continue
                if not hasattr(stock, col_name):
                    logger.warn('Stock obj has no attribute ' + col_name)
                else:
                    old = stock.__getattribute__(col_name)
                    new = row[col_name]
                    if old is not None and old != new:
                        logger.fatal('Currupted data from tushare, %s: old(%s) != new(%s)', col_name, str(old), str(new))
                stock.__setattr__(col_name, row[col_name])


if __name__ == '__main__':
    coloredlogs.DEFAULT_LOG_FORMAT = '%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s'
    coloredlogs.install(level='DEBUG')

    logger = logging.getLogger("root")
    ret = RufengFinance(logger).main()
    logger.info("exiting...")
    exit(ret)
