# coding=utf-8
__author__ = 'Du, Changbin <changbin.du@gmail.com>'
__version__ = '1.1.0'

import sys
if sys.version_info < (3, 0):
    raise RuntimeError('Python3 is required')
sys.path.insert(0, 'tushare')

import os
import logging.config, coloredlogs
from optparse import OptionParser, OptionGroup
import multiprocessing
from pandas import DataFrame
from tqdm import tqdm
import yaml

from analyzer import Analyzer
from dm import DataManager
from monitor import StockMonitor
from plot import StockPlot
import util


class RufengFinance(object):
    def __init__(self):
        self._dm = DataManager()
        self._config = None

    def main(self, argc, argv):
        usage = "usage: %prog [options] <cmd> arg1 arg2\n" + \
                "\n<cmd> should be one of download/list/plot/select:" + \
                "\n  download - download stock data from internet (years)" + \
                "\n  check    - check data in local database" + \
                "\n  drop     - drop data in local database" + \
                "\n  list     - list all stocks in local database" + \
                "\n  plot     - plot stock diagram" + \
                "\n  analyze  - analyze our stocks using local data" + \
                "\n  monitor  - monitor realtime market status"
        parser = OptionParser(usage=usage)

        parser.add_option("--config",
                          metavar="FILE", dest="config", default="config.yaml",
                          help="specific config file"),
        parser.add_option("-o", "--output",
                          metavar="FILE", dest="output",
                          help="specific output dir or file"),
        parser.add_option("-t", "--threads",
                          type="int", dest="threads", default=multiprocessing.cpu_count(),
                          help="threads number to work [default equal cpu count]")

        # for download options
        group = OptionGroup(parser, 'Download Options', description='')
        group.add_option("-f", "--force_update",
                         action="store_true", dest="force_update", default=False,
                         help="download data ignore local existing data")
        parser.add_option_group(group)

        # for plot options
        group = OptionGroup(parser, 'Plot Options', description='')
        group.add_option("--qfq",
                         action="store_true", dest="qfq", default=False,
                         help="show forward adjusted history price")
        group.add_option("-i", "--index-overlay",
                         action="store_true", dest="index_overlay", default=False,
                         help="overlay index history on price")
        parser.add_option_group(group)

        # for analyze options
        group = OptionGroup(parser, 'Analyze Options', description='')
        group.add_option("--plot-all",
                         action="store_true", dest="plot_all", default=False,
                         help="plot all stocks, not only good ones")
        parser.add_option_group(group)

        (options, args) = parser.parse_args()
        if len(args) < 1:
            parser.error("incorrect number of arguments, missing cmd")
            return -1

        command = args[0]
        cmd_args = args[1:] if len(args) > 1 else ()
        cmd_map = {
            'download': self.cmd_download,
            'check':    self.cmd_check,
            'drop':     self.cmd_drop,
            'list':     self.cmd_list,
            'plot':     self.cmd_plot,
            'analyze':  self.cmd_analyze,
            'monitor':  self.cmd_monitor
        }

        if command not in cmd_map:
            parser.error('invalid command')
            return -1
        if cmd_map[command] is None:
            logging.error('command \'%s\' is not implemented yet' % command)
            return -1

        if options.config:
            print("using config %s" % options.config)
            self._config = yaml.load(open(options.config))

        cmd_map[command](options, cmd_args)
        return 0

    def cmd_download(self, options, cmd_args):
        self._dm.data_period_y = self._config['core']['data_period']
        data_full = self._dm.pick_data(options.threads, options.force_update)
        if not data_full:
            logging.warning('not all data successfully picked')

    def cmd_list(self, options, cmd_args):
        self._dm.load_from_db(cmd_args if len(cmd_args) else None)

        list = []
        for code, stock in self._dm.stocks.items():
            list.append({'code': code, 'name': stock.name, 'price': stock.price,
                       'hist_data':'%4d[%s - %s]' % (stock.hist_data.index.size, stock.hist_data.tail(1).index[0], stock.hist_data.index[0]),
                       'update': stock.last_update.strftime("%Y-%m-%d %H:%M:%S")
                    })
        df = DataFrame(list)

        logging.info('all %d available stocks can be analyzed' % len(self._dm.stocks))
        print(df.to_string(columns=('code', 'name', 'price', 'hist_data', 'update')))

        if options.output:
            #df['code'] = df['code'].apply(lambda x: '<a href="https://touzi.sina.com.cn/public/stock/sz{0}">{0}</a>'.format(x))
            with open(options.output, "w+", encoding="utf-8") as f:
                df.to_html(f, escape=False, columns=('code', 'name', 'price', 'hist_data', 'update'))

    def cmd_plot(self, options, cmd_args):
        if len(cmd_args) < 1:
            logging.error("missing argument stock code")
            return -1

        index = self._dm.find_one_index_from_db('000001')

        for code in cmd_args:
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

    def cmd_check(self, options, cmd_args):
        self._dm.load_from_db(cmd_args if len(cmd_args) else None)

        good = bad = 0
        for code, stock in self._dm.stocks.items():
            logging.info('checking %s' % stock)
            if stock.check():
                logging.info('Good, no error found')
                good += 1
            else:
                logging.warning('Bad, error found')
                bad += 1
        logging.info('checked %d, good %d, bad %d' % (good+bad, good, bad))

    def cmd_drop(self, options, cmd_args):
        if len(cmd_args) < 1:
            if util.confirm('drop all data?'):
                logging.info('all local data will be dropped')
                self._dm.drop_local_data(None)
        else:
            for code in cmd_args:
                logging.info('drop stock/index %s' % code)
                self._dm.drop_local_data(code)

    def cmd_analyze(self, options, cmd_args):
        config = self._config['analyzer']
        logging.info('analyzer config:\n%s' % yaml.dump(config))

        self._dm.load_from_db(cmd_args if len(cmd_args) else None)
        if not len(self._dm.stocks):
            logging.error('no stocks found in local database, please run \'download\' command first')
            return

        analyzer = Analyzer(self._dm.stocks, self._dm.indexes, config)
        logging.info('all %d available stocks will be analyzed' % len(analyzer.stocks))
        logging.info('-----------invoking data analyzer module-------------')
        analyzer.analyze(threads=options.threads)
        logging.info('-------------------analyze done----------------------')

        list = []
        for result in analyzer.good_stocks:
            stock = result.stock
            list.append({'code': stock.code, 'name': stock.name, 'price': stock.price,
                         'pe': stock.pe, 'nmc': stock.nmc/10000, 'mktcap': stock.mktcap/10000,
                         'area': stock.area, 'industry': stock.industry
                        })
        df = DataFrame(list)
        if df.empty:
            logging.info('no good stocks found')
            return

        logging.info('list of good %d stocks%s:' % (len(analyzer.good_stocks),
                     options.output and ' and save plots to %s' % options.output or ''))
        print(df.to_string(columns=('code', 'name', 'price', 'pe', 'nmc', 'mktcap', 'area', 'industry')))
        logging.info('global market status: %s' % analyzer.global_status)

        if options.output:
            logging.info('generating html report...')
            os.makedirs(options.output, exist_ok=True)
            analyzer.generate_report(options.output, only_plot_good=not options.plot_all)
            logging.info('done')

    def cmd_monitor(self, options, cmd_args):
        config = self._config['monitor']
        logging.info('monitor config:\n%s' % yaml.dump(config))
        StockMonitor(config).start_and_join()

if __name__ == '__main__':
    # coloredlogs.DEFAULT_LOG_FORMAT = '%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s'
    coloredlogs.DEFAULT_LOG_FORMAT = '%(asctime)s %(message)s'
    coloredlogs.install(level='DEBUG')
    RufengFinance().main(len(sys.argv), sys.argv)
    logging.info("exiting...")
