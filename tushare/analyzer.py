# coding=utf-8
__author__ = 'Du, Changbin <changbin.du@gmail.com>'

import sys
if sys.version_info < (3, 4):
    raise RuntimeError('at least Python 3.4 is required to run')
sys.path.insert(0, 'tushare')

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