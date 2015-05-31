__author__ = 'changbi'

import abc
from lib.errors import UfException, Errors
from baseSelector import BaseSelector

class StabilitySelector(BaseSelector):
    ''' base class for DAO '''
    __metaclass__ = abc.ABCMeta

    def select(self, stock):
        return True
