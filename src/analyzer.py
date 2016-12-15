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

        def get_config(name):
            return self._config[name] if name in self._config else None

        class BadStockException(Exception):
            pass

        try:
            # 创业板
            config_exclude_gem = get_config('exclude_gem')
            if config_exclude_gem is not None:
                if config_exclude_gem and stock.code.startswith('300'):
                    raise BadStockException('in Growth Enterprise Market')

            # 停牌
            config_exclude_suspension = get_config('exclude_suspension')
            if config_exclude_suspension is not None:
                if config_exclude_suspension and (math.isnan(stock.price) or stock.price == 0.0):
                    raise BadStockException('suspending')

            # ST
            config_exclude_st = get_config('exclude_st')
            if config_exclude_st is not None:
                for p in Stock.st_prefix:
                    if stock.name.startswith(p):
                        raise BadStockException('Special Treatment (ST)')

            config_min_hist_data = get_config('min_hist_data')
            if config_min_hist_data is not None:
                config_min_hist_data = max(config_min_hist_data, 10)
                if stock.hist_len < config_min_hist_data:
                    raise BadStockException('only %d days history data' % (stock.hist_len))

            # 最新价格
            config_max_price = get_config('max_price')
            if config_max_price is not None:
                if hist_data.close[0] > config_max_price:
                    raise BadStockException('price is too high, %d RMB' % (hist_data.close[0]))

            # 流通市值
            config_max_nmc = get_config('max_nmc')
            if config_max_nmc is not None:
                if stock.nmc is not None and stock.nmc/10000 > config_max_nmc:
                    raise BadStockException('circulated market value is too high, %dY RMB' % (stock.nmc/10000))

            # 总市值
            config_max_mktcap = get_config('max_mktcap')
            if config_max_mktcap is not None:
                if stock.mktcap is not None and stock.mktcap/10000 > config_max_mktcap:
                    raise BadStockException('total market cap value is too high, %dY RMB' % (stock.mktcap/10000))

            # 市盈率
            config_max_pe = get_config('max_pe')
            if config_max_pe is not None:
                if stock.pe is not None and stock.pe > config_max_pe:
                    raise BadStockException('PE is too high, %d' % (stock.pe))

            # 平均换手率
            config_min_turnover_avg = get_config('min_turnover_avg')
            if config_min_turnover_avg is not None:
                for item in config_min_turnover_avg:
                    days = item[0]
                    min_avg = item[1]
                    if days > stock.hist_len:
                        continue
                    avg = stock.get_turnover_avg(days)
                    if avg < min_avg:
                        raise BadStockException('%d days average turnover is too low, %.2f%% < %.2f%%' % (days, avg, min_avg))

            # delay this until we really need
            qfq_data = stock.qfq_data

            # 当前走势位置
            config_position = get_config('position')
            if config_position is not None:
                days = config_position[0][0]
                ratio = config_position[0][1]
                if stock.hist_len >= days:
                    min_close = qfq_data.close[:days].min()
                    hratio = (qfq_data.close[0]-min_close)/min_close
                    if hratio > ratio:
                        raise BadStockException('current price is higher than %d days min %.2f %.2f%%' % (days, min_close, hratio*100))
                days = config_position[1][0]
                ratio = config_position[1][1]
                if stock.hist_len >= days:
                    max_close = qfq_data.close[:min(days, stock.hist_len)].max()
                    hratio = (max_close - qfq_data.close[0]) / qfq_data.close[0]
                    if hratio < ratio:
                        raise BadStockException('%d days max %.2f is only higher than current %.2f%%' % (days, max_close, hratio*100))

            # 周期振幅
            config_amp_scope = get_config('amp_scope')
            if config_amp_scope is not None:
                for item in config_amp_scope:
                    days = item[0]
                    low = item[1]
                    high = item[2]
                    if days > stock.hist_len:
                        continue
                    min_close = qfq_data.close[:days].min()
                    max_close = qfq_data.close[:days].max()
                    amp = (max_close - min_close)/min_close
                    if amp < low or amp > high:
                        raise BadStockException('%d day amplitude %.2f%% is not in range [%.2f%%, %.2f%%]' %
                                                (days, amp*100, low*100, high*100))

            # 周期振幅
            config_raise_drop_scope = get_config('raise_drop_scope')
            if config_raise_drop_scope is not None:
                for item in config_raise_drop_scope:
                    days = item[0]
                    low = item[1]
                    high = item[2]
                    if days > stock.hist_len:
                        continue
                    change = (qfq_data.close[0] - qfq_data.close[days]) / qfq_data.close[days]
                    if change < low or change > high:
                        raise BadStockException('%d day change percent %.2f%% is not in range [%.2f%%, %.2f%%]' %
                                                (days, change * 100, low * 100, high * 100))
            # 大涨跌幅交易天数
            config_min_change_count = get_config('min_change_count')
            if config_min_change_count is not None:
                for item in config_min_change_count:
                    days = item[0]
                    change = item[1]
                    min_count = item[2]
                    if days > stock.hist_len:
                        continue

                    count = hist_data[:days][abs(hist_data['p_change']) > change].index.size
                    if count < min_count:
                        raise BadStockException('%d days data only have %d days change percent larger than %.2f%%'
                                                % (days, count, change))

            config_ma = get_config('ma')
            if config_ma is not None:
                for item in config_ma:
                    ma_a = item[0]
                    ma_b = item[1]
                    min_count = item[2]
                    if max(ma_a, ma_b) > stock.hist_len:
                        continue

                    ma_map = {5: hist_data.ma5, 10:hist_data.ma10, 20:hist_data.ma20,
                              30:stock.ma30.close, 60:stock.ma60.close, 120:stock.ma120.close
                             }
                    if ma_a not in ma_map or ma_b not in ma_map:
                        raise ValueError('not a valid ma')
                    for i in range(min_count):
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
