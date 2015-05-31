__author__ = 'changbi'

from selector.selectorFactory import SelectorFactory

class SelectEngine(object):
    def __init__(self):
        self.globallMarketData = None

    def select(self, stock):
        selectors = []
        for type in SelectorFactory.getAvailableTypes():
            selector = SelectorFactory.createSelector(type)
            selector.globalMarketData = selector.globalMarketData
            selectors.append(selector)
        for selector in selectors:
            if not selector.select(stock):
                return False
        return True
