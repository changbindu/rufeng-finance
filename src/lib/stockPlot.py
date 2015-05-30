# -*- coding: utf-8 -*-

import datetime

from pylab import mpl
mpl.rcParams['font.sans-serif'] = ['SimHei']
mpl.rcParams['axes.unicode_minus'] = False

import numpy as np
import matplotlib.colors as colors
import matplotlib.finance as finance
import matplotlib.dates as mdates
import matplotlib.ticker as mticker
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager

class StockPlot(object):
    def __init__(self, stock):
        self.stock = stock

    def plot(self):
        stock = self.stock
        date = np.array([q.time for q in stock.history])
        low = np.array([q.low for q in stock.history])
        close = np.array([q.close for q in stock.history])
        high = np.array([q.high for q in stock.history])
        volume = np.array([q.volume for q in stock.history])

        plt.rc('axes', grid=True)
        plt.rc('grid', color='0.75', linestyle='-', linewidth=0.5)

        textsize = 9
        left, width = 0.1, 0.8
        rect1 = [left, 0.8, width, 0.1] #[left, bottom, width, height]
        rect2 = [left, 0.3, width, 0.5]
        rect3 = [left, 0.1, width, 0.2]

        fig = plt.figure(facecolor='white')

        info_ax = fig.add_axes(rect1, axisbg='yellow')  #left, bottom, width, height
        history_ax = fig.add_axes(rect2, axisbg='black', sharex=info_ax)
        volume_ax = fig.add_axes(rect3, axisbg='black', sharex=info_ax)

        plt.xlabel("Time(Day)")

        ### plot the stock information
        fillcolor = 'darkgoldenrod'
        info_ax.text(0.01, 0.9, u'TODO: Here show fundamental information.', va='top', transform=info_ax.transAxes, fontsize=textsize)
        info_ax.set_ylim(0, 100)
        info_ax.set_yticks([30, 70])
        info_ax.set_title("%s(%s)" % (stock.name, stock.symbol))

        ### plot the price and volume data
        history_ax.vlines(date, low, high, color='red', linewidth=1, label='_nolegend_')
        pmax = high.max()
        history_ax.set_ylim(0, pmax + pmax/10)

        last = stock.history[-1]
        s = '%s O:%1.2f H:%1.2f L:%1.2f C:%1.2f, V:%1.1fM Chg:%+1.2f' % (
            last.time.strftime('%d-%b-%Y'),
            last.open, last.high,
            last.low, last.close,
            last.volume*1e-6,
            last.close-last.open )
        history_ax.text(0.3, 0.9, s, transform=history_ax.transAxes, fontsize=textsize)

        volume = volume / 1e6  # dollar volume in millions
        vmax = volume.max()
        poly = volume_ax.fill_between(date, volume, 0, label='Volume', facecolor=fillcolor, edgecolor=fillcolor)
        volume_ax.set_ylim(0, 1.2*vmax)
        volume_ax.set_yticks([])

        # set locator
        for ax in info_ax, history_ax, volume_ax:
            if ax != volume_ax:
                for label in ax.get_xticklabels():
                    label.set_visible(False)
            else:
                for label in ax.get_xticklabels():
                    label.set_rotation(0)
                    label.set_horizontalalignment('center')

            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.YearLocator())
            ax.xaxis.set_minor_locator(mdates.MonthLocator())
            for tick in ax.xaxis.get_major_ticks():
                tick.label1.set_fontsize(12)

        for label in info_ax.get_yticklabels():
            label.set_visible(False)

        plt.show()

    def saveToFile(self, path):
        pass

'''
# StockPlot3D - show several stocks in one  3D diagram
'''
class StockPlot3D(object):
    def __init__(self, stocks):
        self.stocks = stocks
        pass

    def plot(self):
        pass

    def saveToFile(self, path):
        pass
