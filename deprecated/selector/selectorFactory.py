'''
@author: changbin
'''

from lib.errors import Errors, UfException

class SelectorFactory(object):
    ''' selector factory '''
    @staticmethod
    def createSelector(selectorType, config = None):
        ''' create DAM '''
        if 'basic' == selectorType:
            from basicSelector import BasicSelector
            selector = BasicSelector()
        elif 'hot' == selectorType:
            from hotSelector import HotSelector
            selector = HotSelector()
        elif 'macd' == selectorType:
            from MACDSelector import MACDSelector
            selector = MACDSelector()
        elif 'stability' == selectorType:
            from stabilitySelector import StabilitySelector
            selector = StabilitySelector()
        elif 'topic' == selectorType:
            from topicSeletor import TopicSeletor
            selector = TopicSeletor()
        elif 'trend' == selectorType:
            from trendSelector import TrendSelector
            selector = TrendSelector()
        else:
            raise UfException(Errors.INVALID_DAM_TYPE,
                              "Selector type is invalid %s" % selectorType)

        selector.config = config
        return selector

    @staticmethod
    def getAvailableTypes():
        ''' return all available types '''
        return ['basic', 'hot', 'macd', 'stability', 'topic', 'trend']
