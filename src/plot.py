# coding=utf-8
__author__ = 'Du, Changbin <changbin.du@gmail.com>'

import matplotlib.pyplot as plt
from matplotlib.finance import candlestick2_ochl
import matplotlib.ticker as mticker
import matplotlib.dates as mdates


class StockPlot(object):
    def __init__(self):
        pass

    def plot_hist(self, stock):
        fig = plt.figure()
        ax1 = plt.subplot2grid((6, 4), (1, 0), rowspan=4, colspan=4, axisbg='w')
        candlestick2_ochl(ax1,
                          stock.hist_data['open'], stock.hist_data['high'], stock.hist_data['low'], stock.hist_data['close'],
                          width=.75, colorup='g', colordown='r', alpha=0.75)

        plt.ylabel('Stock Price')
        ax1.grid(True)
        for label in ax1.xaxis.get_ticklabels():
            label.set_rotation(90)

        plt.subplots_adjust(left=.10, bottom=.19, right=.93, top=.95, wspace=.20, hspace=0)

        plt.title(str(stock))
        plt.suptitle('History Price')

        plt.show()

    def plot_qfq(self, stock):
        qfq_data = stock.qfq_data
        fig = plt.figure()
        ax1 = plt.subplot2grid((6, 4), (1, 0), rowspan=4, colspan=4, axisbg='w')
        candlestick2_ochl(ax1,
                          qfq_data['open'], qfq_data['high'], qfq_data['low'], qfq_data['close'],
                          width=.75, colorup='g', colordown='r', alpha=0.75)

        plt.ylabel('Stock Price')
        ax1.grid(True)
        for label in ax1.xaxis.get_ticklabels():
            label.set_rotation(90)

        plt.subplots_adjust(left=.10, bottom=.19, right=.93, top=.95, wspace=.20, hspace=0)

        plt.title(str(stock))
        plt.suptitle('Forward Adjusted History Price')

        plt.show()