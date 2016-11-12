# coding=utf-8
__author__ = 'Du, Changbin <changbin.du@gmail.com>'

import matplotlib.pyplot as plt
from matplotlib.finance import candlestick2_ochl
import matplotlib.ticker as mticker
import matplotlib.dates as mdates


class StockPlot(object):
    def __init__(self):
        pass

    def _plot(self, stock, qfq=False):
        data = stock.qfq_data if qfq else stock.hist_data
        data = data.sort_index(ascending=True, inplace=False)
        fig = plt.figure()
        ax1 = plt.subplot2grid((6, 4), (1, 0), rowspan=4, colspan=4, axisbg='w')
        candlestick2_ochl(ax1, data['open'], data['high'], data['low'], data['close'],
                          width=.75, colorup='g', colordown='r', alpha=0.75)

        plt.xlabel('Date')
        plt.ylabel('Price')
        plt.ylim(ymin=stock.hist_min-stock.hist_min/30, ymax=stock.hist_max+stock.hist_max/30)
        ax1.grid(True)
        xrange = range(0, data.index.size, int(data.index.size / 5))
        plt.xticks(xrange, [data.index[loc] for loc in xrange])
        for label in ax1.xaxis.get_ticklabels():
            label.set_rotation(90)

        plt.subplots_adjust(left=.10, bottom=.19, right=.93, top=.95, wspace=.20, hspace=0)


    def plot_hist(self, stock):
        self._plot(stock)
        plt.title(str(stock))
        plt.suptitle('History Price')

        plt.show()

    def plot_qfq(self, stock):
        self._plot(stock, qfq=True)
        plt.title(str(stock))
        plt.suptitle('Forward Adjusted History Price')

        plt.show()