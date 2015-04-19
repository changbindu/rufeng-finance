'''
Created on Dec 21, 2010

@author: changbin
'''
from bs4 import BeautifulSoup
import urllib.request
import re

from model.stockObjects import ChinaStockSymbol

class EastmoneyFinance(object):
    def getAllStockSymbols(self):
        """
        Get all china stock symbols.
        Returns a dictionary.
        """
        stocks = {}
        url = 'http://quote.eastmoney.com/stocklist.html'
        html = urllib.request.urlopen(url, timeout = 10).read()
        html = html.decode('gb2312', 'replace')
        soup = BeautifulSoup(html)
        for item in soup.find_all("a", href=re.compile("^http://quote.eastmoney.com/(sh|sz)\d{6}\.html"), target="_blank"):
            symbol = item.string[-7:-1]
            name = item.string[0:-8]
            prefix = symbol[0:3]
            if prefix not in (ChinaStockSymbol.SS_PREFIX | ChinaStockSymbol.SZ_PREFIX):
                continue
            stocks[symbol] = name
        return stocks

if __name__ == '__main__':
    eastmoney = EastmoneyFinance()
    stocks = eastmoney.getAllStockSymbols()
    print("All china stock symbols:")
    for stock in stocks:
        print("%s - %s" %(stock, stocks[stock]))
