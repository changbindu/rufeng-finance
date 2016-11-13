# coding=utf-8
__author__ = 'Du, Changbin <changbin.du@gmail.com>'

from  pylab import mpl
import time
from matplotlib.font_manager import FontProperties
from matplotlib import pyplot as plt
from matplotlib.dates import DateFormatter, DayLocator
from matplotlib import gridspec
from matplotlib.dates import num2date, IndexDateFormatter
from matplotlib.ticker import  IndexLocator, FuncFormatter
from matplotlib.finance import candlestick2_ochl, volume_overlay
import matplotlib.ticker as mticker
import matplotlib.dates as mdates

# mpl.rcParams['font.sans-serif'] = ['FangSong']
mpl.rcParams['axes.unicode_minus'] = False

class StockPlot(object):
    """ref: https://gist.github.com/ithurricane/240b4aa954e09915b24697ca5f2aa1db"""
    def __init__(self):
        self.display_size = (5, 5)
        self.save_size = (40, 20)

    def __plot(self, stock, figsize, qfq):
        data = stock.qfq_data if qfq else stock.hist_data
        data = data.sort_index(ascending=True, inplace=False)

        fp = FontProperties(fname='simsun.ttc')
        fig = plt.figure(figsize=figsize, dpi=100)
        fig.subplots_adjust(left=.10, bottom=.09, right=.93, top=.95, wspace=.20, hspace=0)
        gs = gridspec.GridSpec(3, 1, height_ratios=[4, 1, 1])

        # draw hist price diagram
        ax0 = plt.subplot(gs[0])
        candlestick2_ochl(ax0, data.open, data.high, data.low, data.close,
                          width=.75, colorup='g', colordown='r', alpha=0.75)

        for i, factor in enumerate(data.factor):
            if i != 0 and factor != data.factor[i-1]:
                plt.annotate(r'Q(f=%.3f)' % factor,
                     xy=(i, data.open[i]), xycoords='data',
                     xytext=(0, data.open[i]), textcoords='offset pixels', fontsize=10,                     arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2"))

        left, height, top = 0.025, 0.05, 0.9
        t1 = ax0.text(left, top, '%s-%s' % (stock.code, stock.name), fontproperties=fp, fontsize=8, transform=ax0.transAxes)
        if not qfq:
            t2 = ax0.text(left, top - height, 'EMA(5)', color='b', fontsize=8, transform=ax0.transAxes)
            t3 = ax0.text(left, top - 2 * height, 'EMA(10)', color='y', fontsize=8, transform=ax0.transAxes)
            t4 = ax0.text(left, top - 3 * height, 'EMA(20)', color='r', fontsize=8, transform=ax0.transAxes)
            ax0.plot(data.ma5.values, color='b', lw=1)
            ax0.plot(data.ma10.values, color='y', lw=1)
            ax0.plot(data.ma20.values, color='r', lw=1)

        s = '%s O:%1.2f H:%1.2f L:%1.2f C:%1.2f, V:%1.1fM Chg:%+1.2f' % (
            data.index[-1],
            data.open[-1], data.high[-1], data.low[-1], data.close[-1],
            data.volume[-1] * 1e-6,
            data.close[-1] - data.open[-1])
        t5 = ax0.text(0.5, top, s, fontsize=8, transform=ax0.transAxes)

        plt.ylabel('Price')
        plt.ylim(ymin=stock.hist_min-stock.hist_min/30, ymax=stock.hist_max+stock.hist_max/30)
        ax0.grid(True)

        if qfq:
            plt.title('Forward Adjusted History Price')
        else:
            plt.title('History Price')

        xrange = range(0, data.index.size, max(int(data.index.size / 5), 5))
        plt.xticks(xrange, [data.index[loc] for loc in xrange])
        plt.setp(ax0.get_xticklabels(), visible=False)

        # draw hist volume diagram
        ax1 = plt.subplot(gs[1], sharex=ax0)
        volume_overlay(ax1, data.open, data.close, data.volume,
                       width=.75, colorup='g', colordown='r', alpha=0.75)
        ax1.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%1.1fM' % (x*1e-6)
                       if data.volume.max()>1e6 else '%1.1fK' % (x*1e-3)))

        if not qfq:
            ax1.plot(data.v_ma5.values, color='b', lw=1)
            ax1.plot(data.v_ma10.values, color='y', lw=1)
            ax1.plot(data.v_ma20.values, color='r', lw=1)
        plt.setp(ax1.get_xticklabels(), visible=False)
        ax1.yaxis.set_ticks_position('both')
        ax1.set_ylabel('Volume')
        ax1.grid(True)

        # draw hist turnover diagram
        ax2 = plt.subplot(gs[2], sharex=ax0)
        volume_overlay(ax2, data.open, data.close, data.turnover,
                       width=.75, colorup='g', colordown='r', alpha=0.75)
        ax2.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%s' % (data.index[x])))
        ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%.2f%%' % (x)))
        for label in ax2.xaxis.get_ticklabels():
            label.set_rotation(0)
        ax2.set_xlabel('Date')
        ax2.yaxis.set_ticks_position('both')
        ax2.set_ylabel('Turnover')
        ax2.grid(True)

        # plt.legend(prop=fp)

    def _plot(self, stock, qfq, path=None):
        if path is None:
            self.__plot(stock, self.display_size, qfq)
            plt.show()
        else:
            self.__plot(stock, self.save_size, qfq)
            plt.savefig(path)
        plt.close()

    def plot_hist(self, stock, path=None):
        self._plot(stock, False, path)

    def plot_qfq(self, stock, path=None):
        self._plot(stock, True, path)
