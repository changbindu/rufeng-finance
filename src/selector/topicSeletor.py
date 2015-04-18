__author__ = 'changbi'

import abc
from lib.errors import UfException, Errors
from select.baseSelector import BaseSelector

class TopicSeletor(BaseSelector):
    ''' base class for DAO '''
    __metaclass__ = abc.ABCMeta

    def select(self):
        ''' read quotes '''
        raise UfException(Errors.UNDEFINED_METHOD, "select method is not defined")
