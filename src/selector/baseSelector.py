'''
@author: changbin
'''
import abc
from lib.errors import UfException, Errors

class BaseSelector(object):
    ''' base class for DAO '''
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        ''' constructor '''
        self.globalMarketData = None

    def select(self, stock):
        ''' read quotes '''
        raise UfException(Errors.UNDEFINED_METHOD, "select method is not defined")
