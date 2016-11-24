# coding=utf-8
__author__ = 'Du, Changbin <changbin.du@gmail.com>'

import os
import math
import shutil
import logging
import datetime
from threadpool import ThreadPool, makeRequests
from jinja2 import Template, Environment, FileSystemLoader
from tqdm import tqdm
from stock import Stock
from plot import StockPlot


class Result(object):
    def __init__(self, stock):
        self.stock = stock
        self.log = ''
        self.status = 'NAN'
        self.exception = None


class Analyzer(object):
    def __init__(self, stocks, indexes, config):
        self.stocks = stocks
        self.indexs = indexes

        self.global_status = 'NAN'
        self.good_stocks = []
        self.bad_stocks = []

        self._config = config
        self.config_min_hist_data = max(config['min_hist_data'], 10)
        self.config_max_price = config['max_price']
        self.config_max_nmc = config['max_nmc']
        self.config_max_mktcap = config['max_mktcap']
        self.config_max_pe = config['max_pe']
        self.config_exclude_gem = config['exclude_gem']
        self.config_exclude_suspension = config['exclude_suspension']
        self.config_exclude_st = config['exclude_st']
        self.config_min_d5_turnover_avg = config['min_d5_turnover_avg']
        self.config_min_d30_turnover_avg = config['min_d30_turnover_avg']
        self.config_min_d90_amp = config['min_d90_amp']
        self.config_position = config['position']
        self.config_min_d90_change_count = config['min_d90_change_count']
        self.config_ma = config['ma']

    def analyze(self, threads=1):
        self.global_status = 'GOOD' if self._analyze_index() else 'BAD'

        pool = ThreadPool(threads)
        requests = makeRequests(self._analyze_single_stock, [s for _, s in self.stocks.items()])
        [pool.putRequest(req) for req in requests]
        pool.wait()

        self.good_stocks = sorted(self.good_stocks, key=lambda result: result.stock.industry)
        self.bad_stocks = sorted(self.bad_stocks, key=lambda result: result.stock.industry)

    def _analyze_index(self):
        sz_index = self.indexs['000001']
        return sz_index.hist_data.ma10[0] > sz_index.hist_data.ma20[0]

    def _analyze_single_stock(self, stock):
        """return if this stock is good"""
        hist_data = stock.hist_data
        result = Result(stock)

        class BadStockException(Exception):
            pass

        try:
            # 创业板
            if self.config_exclude_gem and stock.code.startswith('300'):
                raise BadStockException('in Growth Enterprise Market')

            # 停牌
            if self.config_exclude_suspension and (math.isnan(stock.price) or stock.price == 0.0):
                raise BadStockException('suspending')

            # ST
            if self.config_exclude_st:
                for p in Stock.st_prefix:
                    if stock.name.startswith(p):
                        raise BadStockException('Special Treatment (ST)')

            if stock.hist_len < self.config_min_hist_data:
                raise BadStockException('only %d days history data' % (stock.hist_len))

            # 最新价格
            if hist_data.close[0] > self.config_max_price:
                raise BadStockException('price is too high, %d RMB' % (hist_data.close[0]))

            # 流通市值
            if stock.nmc is not None and stock.nmc/10000 > self.config_max_nmc:
                raise BadStockException('circulated market value is too high, %dY RMB' % (stock.nmc/10000))

            # 总市值
            if stock.mktcap is not None and stock.mktcap/10000 > self.config_max_mktcap:
                raise BadStockException('total market cap value is too high, %dY RMB' % (stock.mktcap/10000))

            # 市盈率
            if stock.pe is not None and stock.pe > self.config_max_pe:
                raise BadStockException('PE is too high, %d' % (stock.pe))

            # 5日平均换手率
            d5_avg = stock.get_turnover_avg(5)
            if d5_avg < self.config_min_d5_turnover_avg:
                raise BadStockException('5 days average turnover is too low, %.2f%%' % (d5_avg))

            # 30日平均换手率
            d30_avg = stock.get_turnover_avg(30)
            if d30_avg < self.config_min_d30_turnover_avg:
                raise BadStockException('30 days average turnover is too low, %.2f%%' % (d30_avg))

            # delay this until we really need
            qfq_data = stock.qfq_data

            # 当前走势位置
            if stock.hist_len >= 60:
                min_close = qfq_data.close[:60].min()
                hratio = (qfq_data.close[0]-min_close)/min_close
                if hratio > self.config_position[0]:
                    raise BadStockException('current price is higher than 60 days min %.2f %.2f%%' % (min_close, hratio*100))

                max_close = qfq_data.close[:min(420, stock.hist_len)].max()
                hratio = (max_close - qfq_data.close[0]) / qfq_data.close[0]
                if hratio < self.config_position[1]:
                    raise BadStockException('420 days max %.2f is only higher than current %.2f%%' % (max_close, hratio*100))

            # 90天振幅
            if stock.hist_len >= 90:
                min_close = qfq_data.close[:90].min()
                max_close = qfq_data.close[:90].max()
                amp = (max_close - min_close)/min_close
                if amp < self.config_min_d90_amp:
                    raise BadStockException('90 day amplitude is only %.2f%%' % (amp*100))

            # 大涨跌幅交易天数
            if stock.hist_len >= 90:
                min_change = self.config_min_d90_change_count[0]
                count = hist_data[abs(hist_data['p_change']) > min_change].index.size
                if count < self.config_min_d90_change_count[1]:
                    raise BadStockException('90 days data only have %d day change percent larger than %.2f%%'
                                            % (count, self.config_min_d90_change_count[1]))

            if stock.hist_len >= self.config_ma[2]:
                ma_map = {5: hist_data.ma5, 10:hist_data.ma10, 20:hist_data.ma20,
                          30:stock.ma30.close, 60:stock.ma60.close, 120:stock.ma120.close
                         }
                ma_a = self.config_ma[0]
                ma_b = self.config_ma[1]
                if ma_a not in ma_map or ma_b not in ma_map:
                    raise ValueError('not a valid ma')
                for i in range(self.config_ma[2]):
                    if ma_map[ma_a][i] < ma_map[ma_b][i]:
                        raise BadStockException('ma%d only larger than ma%d for %d days from now' % (ma_a, ma_b, i))

            logging.debug('%s: good' % stock)
            result.status = 'GOOD'
            self.good_stocks.append(result)
        except BadStockException as e:
            logging.debug('%s: %s' % (stock, str(e)))
            result.status = 'BAD'
            result.log = str(e)
            self.bad_stocks.append(result)
        except Exception as e:
            msg = 'exception occurred: %s' % e
            logging.warning('%s: %s' % (stock, msg))
            result.status = 'BAD'
            result.log = msg
            result.exception = e
            self.bad_stocks.append(result)
        finally:
            pass

    def generate_report(self, out_dir, only_plot_good=True):
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('report.jinja2')
        output = template.render({
                    'config': self._config,
                    'good_stocks': self.good_stocks,
                    'bad_stocks': self.bad_stocks,
                    'global_status': self.global_status,
                    'date': datetime.date.today()})
        with open(os.path.join(out_dir, 'index.html'), "w+") as f:
            f.write(output)

        # copy resources
        def _copy_res(src):
            dest = os.path.join(out_dir, os.path.basename(src))
            if not os.path.exists(dest):
                os.makedirs(dest, exist_ok=True)
            src_files = os.listdir(src)
            for file_name in src_files:
                full_file_name = os.path.join(src, file_name)
                if (os.path.isfile(full_file_name)):
                    shutil.copy(full_file_name, dest)
        _copy_res('templates/css')
        _copy_res('templates/js')
        _copy_res('templates/images')

        # plot history
        img_dir = os.path.join(out_dir, 'images')
        os.makedirs(img_dir, exist_ok=True)

        plot = StockPlot()
        pbar = tqdm(self.good_stocks + (self.bad_stocks if not only_plot_good else []))
        for result in pbar:
            stock = result.stock
            pbar.set_description("Plotting %s" % (stock.code))
            path = os.path.join(img_dir, '%s.png' % stock.code)
            if os.path.exists(path):
                continue  # skip existed plots
            plot.plot_hist(stock, self.indexs['000001'], path=os.path.join(img_dir, '%s.png' % stock.code))
        pbar.close()
