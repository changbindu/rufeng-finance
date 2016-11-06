# coding=utf-8
__author__ = 'Du, Changbin <changbin.du@gmail.com>'

from pandas import DataFrame
import tushare as ts

import util
from stock import Stock, Index


class Analyzer(object):
    def __init__(self, logger=None, stocks=None, indexes=None):
        self.logger = logger
        self.stocks = stocks
        self.indexs = indexes

    def analyze(self):
        pass