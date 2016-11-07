# coding=utf-8
__author__ = 'Du, Changbin <changbin.du@gmail.com>'

import logging


class Analyzer(object):
    def __init__(self, stocks=None, indexes=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.stocks = stocks
        self.indexs = indexes

    def analyze(self):
        pass