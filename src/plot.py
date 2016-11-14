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
from pandas import DataFrame

# mpl.rcParams['font.sans-serif'] = ['FangSong']
mpl.rcParams['axes.unicode_minus'] = False

class StockPlot(object):
    """ref: https://gist.github.com/ithurricane/240b4aa954e09915b24697ca5f2aa1db"""
    def __init__(self):
        self.display_size = (5, 5)
        self.save_size = (40, 20)

    def __plot(self, stock, figsize, qfq, index):
        data = stock.qfq_data if qfq else stock.hist_data
        data = data.sort_index(ascending=True, inplace=False)

        fp = FontProperties(fname='simsun.ttc')
        fig = plt.figure(figsize=figsize, dpi=100)
        fig.subplots_adjust(left=.10, bottom=.09, right=.93, top=.95, wspace=.20, hspace=0)
        gs = gridspec.GridSpec(3, 1, height_ratios=[4, 1, 1])

        # draw hist price diagram
        ax_price = plt.subplot(gs[0])
        candlestick2_ochl(ax_price, data.open, data.high, data.low, data.close,
                          width=.75, colorup='g', colordown='r', alpha=0.75)

        for i, factor in enumerate(data.factor):
            if i != 0 and factor != data.factor[i-1]:
                plt.annotate(r'Q(f=%.3f)' % factor,
                     xy=(i, data.open[i]), xycoords='data',
                     xytext=(0, data.open[i]), textcoords='offset pixels', fontsize=10, arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2"))

        left, height, top = 0.025, 0.05, 0.9
        t1 = ax_price.text(left, top, '%s-%s' % (stock.code, stock.name), fontproperties=fp, fontsize=8, transform=ax_price.transAxes)
        if not qfq:
            t2 = ax_price.text(left, top - height, 'EMA(5)', color='b', fontsize=8, transform=ax_price.transAxes)
            t3 = ax_price.text(left, top - 2 * height, 'EMA(10)', color='y', fontsize=8, transform=ax_price.transAxes)
            t4 = ax_price.text(left, top - 3 * height, 'EMA(20)', color='r', fontsize=8, transform=ax_price.transAxes)
            ax_price.plot(data.ma5.values, color='b', lw=1)
            ax_price.plot(data.ma10.values, color='y', lw=1)
            ax_price.plot(data.ma20.values, color='r', lw=1)

        s = '%s O:%1.2f H:%1.2f L:%1.2f C:%1.2f, V:%1.1fM Chg:%+1.2f' % (
            data.index[-1],
            data.open[-1], data.high[-1], data.low[-1], data.close[-1],
            data.volume[-1] * 1e-6,
            data.close[-1] - data.open[-1])
        t5 = ax_price.text(0.5, top, s, fontsize=8, transform=ax_price.transAxes)

        plt.ylabel('Price')
        plt.ylim(ymin=stock.hist_min-stock.hist_min/30, ymax=stock.hist_max+stock.hist_max/30)
        ax_price.grid(True)

        if qfq:
            plt.title('Forward Adjusted History Price')
        else:
            plt.title('History Price')

        xrange = range(0, data.index.size, max(int(data.index.size / 5), 5))
        plt.xticks(xrange, [data.index[loc] for loc in xrange])
        plt.setp(ax_price.get_xticklabels(), visible=False)

        # draw index overlay
        if index:
            index_hist = index.hist_data
            common_index = index_hist.index.intersection(data.index)
            common_data = index_hist.join(DataFrame(index=common_index), how='inner')
            common_data.sort_index(ascending=True, inplace=True)
            ax_index = ax_price.twinx()
            candlestick2_ochl(ax_index, common_data.open, common_data.high, common_data.low, common_data.close,
                              width=.75, colorup='g', colordown='r', alpha=0.35)
            ax_index.set_ylabel('Index(%s)' % index.name, fontproperties=fp)
            ax_index.set_ylim(ymin=common_data.low.min(), ymax=common_data.high.max())

        # draw hist volume diagram
        ax_volume = plt.subplot(gs[1], sharex=ax_price)
        volume_overlay(ax_volume, data.open, data.close, data.volume,
                       width=.75, colorup='g', colordown='r', alpha=0.75)
        ax_volume.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%1.1fM' % (x*1e-6)
                       if data.volume.max()>1e6 else '%1.1fK' % (x*1e-3)))

        if not qfq:
            ax_volume.plot(data.v_ma5.values, color='b', lw=1)
            ax_volume.plot(data.v_ma10.values, color='y', lw=1)
            ax_volume.plot(data.v_ma20.values, color='r', lw=1)
        plt.setp(ax_volume.get_xticklabels(), visible=False)
        ax_volume.yaxis.set_ticks_position('both')
        ax_volume.set_ylabel('Volume')
        ax_volume.grid(True)

        # draw hist turnover diagram
        ax_turnover = plt.subplot(gs[2], sharex=ax_price)
        volume_overlay(ax_turnover, data.open, data.close, data.turnover,
                       width=.75, colorup='g', colordown='r', alpha=0.75)
        ax_turnover.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%s' % (data.index[x])))
        ax_turnover.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: '%.2f%%' % (x)))
        for label in ax_turnover.xaxis.get_ticklabels():
            label.set_rotation(0)
        ax_turnover.set_xlabel('Date')
        ax_turnover.yaxis.set_ticks_position('both')
        ax_turnover.set_ylabel('Turnover')
        ax_turnover.grid(True)

        # plt.legend(prop=fp)

    def _plot(self, stock, qfq, index=None, path=None):
        if path is None:
            self.__plot(stock, self.display_size, qfq, index)
            plt.show()
        else:
            self.__plot(stock, self.save_size, qfq, index)
            plt.savefig(path)
        plt.close()

    def plot_hist(self, stock, index=None, path=None):
        self._plot(stock, False,index, path)

    def plot_qfq(self, stock, index=None, path=None):
        self._plot(stock, True, index, path)
