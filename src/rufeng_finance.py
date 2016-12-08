# coding=utf-8
__author__ = 'Du, Changbin <changbin.du@gmail.com>'
__version__ = '1.1.0'

import sys
if sys.version_info < (3, 0):
    raise RuntimeError('Python3 is required')
sys.path.insert(0, 'tushare')

import os
import logging.config, coloredlogs
import argparse
import multiprocessing
from pandas import DataFrame
from tqdm import tqdm
import yaml
import cmd

from analyzer import Analyzer
from dm import DataManager
from monitor import StockMonitor
from plot import StockPlot
import util


class RufengFinanceCommandLine(cmd.Cmd):
    prompt = '(Analyzer) '
    intro = 'A finance ayalyzer of python.\n' \
            'Copyright © 2016 Changbin Du <changbin.du@gmail.com>. All rights reserved.'

    def __init__(self, *args, **kwargs):
        self._dm = DataManager()
        self._config = None
        self.loaded = False
        super(RufengFinanceCommandLine, self).__init__(*args, **kwargs)

    @staticmethod
    def _get_arg_parser():
        class MyArgumentParser(argparse.ArgumentParser):
            def exit(self, status=0, message=None):
                self._print_message(message)
                self.fail = True

            def has_err(self):
                return hasattr(self, 'fail')

        parser = MyArgumentParser(prog=sys._getframe().f_back.f_code.co_name.replace('do_', ''))
        parser.add_argument("--config",
                            metavar="FILE", dest="config", default="config.yaml",
                            help="specific config file")

        return parser

    def _parse_arg(self, parser, args_str):
        options = parser.parse_args(args_str.split())
        if parser.has_err():
            return None
        if options.config:
            print("using config %s" % options.config)
            self._config = yaml.load(open(options.config))
        return options

    def do_load(self, args_str=None):
        if self.loaded and len(self._dm.stocks):
            print('already loaded')
        else:
            self._dm.load_from_db()
            self.loaded = True

    def help_load(self):
        print('\n'.join(['load data from local database to memory',]))

    def do_download(self, args_str):
        parser = self._get_arg_parser()
        parser.add_argument("-t", "--threads",
                            type=int, dest="threads", default=multiprocessing.cpu_count(),
                            help="threads number to work [default equal cpu count]")
        parser.add_argument("-f", "--force_update",
                            action="store_true", dest="force_update", default=False,
                            help="download data ignore local existing data")
        options = self._parse_arg(parser, args_str)
        if not options:
            return

        self._dm.data_period_y = self._config['core']['data_period']
        if options.force_update and self.loaded:
            self._dm.invalid_loaded_stocks()
            self.loaded = False
        elif not self.loaded:
            self.do_load()
        try:
            data_full = self._dm.pick_data(options.threads)
        except IOError as e:
            print(e)
        else:
            if not data_full:
                logging.warning('not all data successfully picked')

    def help_download(self):
        print('\n'.join(['download stock data from internet (years)',]))

    def complete_download(self, text, line, begidx, endidx):
        candidate = ['-f', '--force_update']

        if not text:
            completions = candidate[:]
        else:
            completions = [f for f in candidate if f.startswith(text)]
        return completions

    def do_check(self, args_str):
        parser = self._get_arg_parser()
        parser.add_argument('codes', nargs='*')
        options = self._parse_arg(parser, args_str)
        if not options:
            return

        if not len(options.codes):
            if not self.loaded:
                self.do_load()
            stocks = self._dm.stocks
        else:
            stocks = {}
            for code in options.codes:
                stock = self._dm.find_one_stock_from_db(code)
                if stock is None:
                    logging.error('unknown stock %s', code)
                else:
                    stocks[code] = stock

        good = bad = 0
        for code, stock in stocks.items():
            logging.info('checking %s' % stock)
            if stock.check():
                logging.info('Good, no error found')
                good += 1
            else:
                logging.warning('Bad, error found')
                bad += 1
        logging.info('checked %d, good %d, bad %d' % (good + bad, good, bad))

    def help_check(self):
        print('\n'.join(['check data in local database',]))

    def do_drop(self, args_str):
        parser = self._get_arg_parser()
        parser.add_argument('codes', nargs='*')
        options = self._parse_arg(parser, args_str)
        if not options:
            return

        if len(options.codes) < 1:
            if util.confirm('drop all data?'):
                logging.info('all local data will be dropped')
                self._dm.drop_local_data(None)
        else:
            for code in options.codes:
                logging.info('drop stock/index %s' % code)
                self._dm.drop_local_data(code)

    def help_drop(self):
        print('\n'.join(['drop data in local database',]))

    def do_list(self, args_str):
        parser = self._get_arg_parser()
        parser.add_argument("-o", "--output",
                            metavar="FILE", dest="output",
                            help="specific output dir or file"),
        parser.add_argument('codes', nargs='*')
        options = self._parse_arg(parser, args_str)
        if not options:
            return

        if not len(options.codes):
            if not self.loaded:
                self.do_load()
            stocks = self._dm.stocks
        else:
            stocks = {}
            for code in options.codes:
                stock = self._dm.find_one_stock_from_db(code)
                if stock is None:
                    logging.error('unknown stock %s', code)
                else:
                    stocks[code] = stock

        if not len(stocks):
            logging.info('no stocks found')
            return

        list = []
        for code, stock in self._dm.stocks.items():
            list.append({'code': code, 'name': stock.name, 'price': stock.price,
                         'hist_data': '%4d[%s - %s]' % (
                         stock.hist_data.index.size, stock.hist_data.tail(1).index[0], stock.hist_data.index[0]),
                         'update': stock.last_update.strftime("%Y-%m-%d %H:%M:%S")
                         })
        df = DataFrame(list)

        logging.info('all %d available stocks can be analyzed' % len(self._dm.stocks))
        print(df.to_string(columns=('code', 'name', 'price', 'hist_data', 'update')))

        if options.output:
            # df['code'] = df['code'].apply(lambda x: '<a href="https://touzi.sina.com.cn/public/stock/sz{0}">{0}</a>'.format(x))
            with open(options.output, "w+", encoding="utf-8") as f:
                df.to_html(f, escape=False, columns=('code', 'name', 'price', 'hist_data', 'update'))

    def help_list(self):
        print('\n'.join(['list all stocks in local database',]))

    def do_plot(self, args_str):
        parser = self._get_arg_parser()
        parser.add_argument("-o", "--output",
                            metavar="FILE", dest="output",
                            help="specific output dir or file"),
        parser.add_argument("--qfq",
                         action="store_true", dest="qfq", default=False,
                         help="show forward adjusted history price")
        parser.add_argument("-i", "--index-overlay",
                         action="store_true", dest="index_overlay", default=False,
                         help="overlay index history on price")
        parser.add_argument('codes', nargs='*')
        options = self._parse_arg(parser, args_str)
        if not options:
            return

        if len(options.codes) < 1:
            logging.error("missing argument stock code")
            return -1

        index = self._dm.find_one_index_from_db('000001')

        for code in options.codes:
            stock = self._dm.find_one_stock_from_db(code)
            if stock is None:
                logging.error('unknown stock %s', code)
                return

            path = options.output
            if path:
                if not os.path.exists(path):
                    os.makedirs(path)
                if os.path.isdir(path):
                    path = os.path.join(options.output, '%s.png' % stock.code)
                print('draw diagram for stock %s to %s' % (stock, path))
            else:
                print('show diagram for stock %s ...' % stock)
            if options.qfq:
                StockPlot().plot_qfq(stock, index, options.index_overlay, path)
            else:
                StockPlot().plot_hist(stock, index, options.index_overlay, path)

    def help_plot(self):
        print('\n'.join(['plot stock diagram',]))

    def do_analyze(self, args_str):
        parser = self._get_arg_parser()
        parser.add_argument("-o", "--output",
                            metavar="FILE", dest="output",
                            help="specific output dir or file"),
        parser.add_argument("-t", "--threads",
                            type=int, dest="threads", default=multiprocessing.cpu_count(),
                            help="threads number to work [default equal cpu count]")
        parser.add_argument("--plot-all",
                         action="store_true", dest="plot_all", default=False,
                         help="plot all stocks, not only good ones")
        parser.add_argument('codes', nargs='*')
        options = self._parse_arg(parser, args_str)
        if not options:
            return

        config = self._config['analyzer']
        logging.info('analyzer config:\n%s' % yaml.dump(config))

        if not self.loaded:
            self.do_load()

        stocks = {}
        if len(options.codes):
            for code in options.codes:
                if code in self._dm.stocks:
                    stocks[code] = self._dm.stocks[code]
                else:
                    logging.error('unknown stock %s', code)
        else:
            stocks = self._dm.stocks

        if not len(stocks):
            logging.error('no stocks found in local database, please run \'load\' command first')
            return

        analyzer = Analyzer(stocks, self._dm.indexes, config)
        logging.info('all %d available stocks will be analyzed' % len(analyzer.stocks))
        logging.info('-----------invoking data analyzer module-------------')
        analyzer.analyze(threads=options.threads)
        logging.info('-------------------analyze done----------------------')

        list = []
        for result in analyzer.good_stocks:
            stock = result.stock
            list.append({'code': stock.code, 'name': stock.name, 'price': stock.price,
                         'pe': stock.pe, 'nmc': stock.nmc / 10000, 'mktcap': stock.mktcap / 10000,
                         'toavgd5': '%.2f%%' % stock.get_turnover_avg(5),
                         'toavgd30': '%.2f%%' % stock.get_turnover_avg(30),
                         'area': stock.area, 'industry': stock.industry
                         })
        df = DataFrame(list)
        if df.empty:
            logging.info('no good stocks found')
            return

        logging.info('list of good %d stocks%s:' % (len(analyzer.good_stocks),
                                                    options.output and ' and save plots to %s' % options.output or ''))
        print(df.to_string(
            columns=('code', 'name', 'price', 'pe', 'nmc', 'mktcap', 'toavgd5', 'toavgd30', 'area', 'industry')))
        logging.info('global market status: %s' % analyzer.global_status)

        if options.output:
            logging.info('generating html report...')
            os.makedirs(options.output, exist_ok=True)
            analyzer.generate_report(options.output, only_plot_good=not options.plot_all)
            logging.info('done')

    def help_analyze(self):
        print('\n'.join(['analyze our stocks using local data',]))

    def do_edit(self, args_str=None):
        os.system('vim ' + (args_str if args_str else 'config.yaml'))

    def help_edit(self):
        print('\n'.join(['edit config file using vim', ]))

    def do_monitor(self, args_str):
        parser = self._get_arg_parser()
        parser.add_argument("-f", "--force_update",
                            action="store_true", dest="force_update", default=False,
                            help="download data ignore local existing data")
        options = self._parse_arg(parser, args_str)
        if not options:
            return

        config = self._config['monitor']
        logging.info('monitor config:\n%s' % yaml.dump(config))
        StockMonitor(config).start_and_join()

    def help_monitor(self):
        print('\n'.join(['monitor realtime market status',]))

    def do_quit(self, line):
        return True

    def help_quit(self):
        print('\n'.join(['quit cmd', ]))

    def do_EOF(self, line):
        return True


if __name__ == '__main__':
    # coloredlogs.DEFAULT_LOG_FORMAT = '%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s'
    coloredlogs.DEFAULT_LOG_FORMAT = '%(asctime)s %(message)s'
    coloredlogs.install(level='DEBUG')
    if len(sys.argv) > 1:
        RufengFinanceCommandLine().onecmd(' '.join(sys.argv[1:]))
    else:
        RufengFinanceCommandLine().cmdloop()
