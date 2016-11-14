# coding=utf-8
__author__ = 'Du, Changbin <changbin.du@gmail.com>'

import sys
if sys.version_info < (3, 0):
    raise RuntimeError('Python3 is required')
sys.path.insert(0, 'tushare')

import os
import logging.config, coloredlogs
from optparse import OptionParser
from tqdm import tqdm
import yaml

from analyzer import Analyzer
from dm import DataManager
from monitor import StockMonitor
from plot import StockPlot

class RufengFinance(object):
    def __init__(self):
        self._dm = DataManager()
        self._config = None

    def main(self, argc, argv):
        usage = "usage: %prog [options] <cmd> arg1 arg2\n" + \
                "\n<cmd> should be one of download/list/plot/select:" + \
                "\n  download - download stock data from internet (1 year)" + \
                "\n  drop     - drop all data in local database" + \
                "\n  list     - list all stocks in local database" + \
                "\n  plot     - plot stock diagram" + \
                "\n  analyze  - analyze our stocks" + \
                "\n  monitor  - monitor realtime status"
        parser = OptionParser(usage=usage)

        parser.add_option("--config",
                          metavar="FILE", dest="config", default="config.yaml",
                          help="specific config file"),

        parser.add_option("-o", "--output",
                          metavar="FILE", dest="output",
                          help="specific output dir or file"),

        parser.add_option("-s", "--selector",
                      default="all", dest="selector",
                      help="selectors: all, trend, macd, or hot [default: %default]")

        # for download options
        parser.add_option("-t", "--threads",
                          type="int", dest="threads", default=20,
                          help="download: threads number to work")
        parser.add_option("-a", "--force_update",
                          action="store_true", dest="force_update", default=False,
                          help="download: download data ignore local existing data")

        # for plot options
        parser.add_option("--qfq",
                          action="store_true", dest="qfq", default=False,
                          help="plot: show forward adjusted history price")

        (options, args) = parser.parse_args()
        if len(args) < 1:
            parser.error("incorrect number of arguments, missing cmd")
            return -1

        command = args[0]
        cmd_args = args[1:] if len(args) > 1 else ()
        cmd_map = {
            'download': self.cmd_download,
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
        self._dm.load_from_db()
        logging.info('all %d available stocks can be analyzed' % len(self._dm.stocks))
        logging.info('%-6s %-8s %6s %-30s %-18s' % ('code', 'name', 'price', 'hist_data', 'update'))
        for code, stock in self._dm.stocks.items():
            logging.info('%-6s %-4s %5.2f %-30s %-18s' % (
                         stock.code, stock.name, stock.price,
                         '%4d[%s - %s]' % (stock.hist_data.index.size, stock.hist_data.tail(1).index[0], stock.hist_data.index[0]),
                         stock.last_update.strftime("%Y-%m-%d %H:%M:%S")))

    def cmd_plot(self, options, cmd_args):
        if len(cmd_args) < 1:
            logging.error("missing argument stock code")
            return -1

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
                StockPlot().plot_qfq(stock, path)
            else:
                StockPlot().plot_hist(stock, path)

    def cmd_drop(self, options, cmd_args):
        logging.info('all local data will be dropped')
        self._dm.drop_local_db()

    def cmd_analyze(self, options, cmd_args):
        config = self._config['analyzer']
        logging.info('analyzer config:\n%s' % yaml.dump(config))
        self._dm.load_from_db()

        if not len(self._dm.stocks):
            logging.error('no stocks found in local database, please run \'download\' command first')
            return

        analyzer = Analyzer(self._dm.stocks, self._dm.indexes, config)
        logging.info('all %d available stocks will be analyzed' % len(analyzer.stocks))
        logging.info('-----------invoking data analyzer module-------------')
        selected_stocks, global_status = analyzer.analyze()
        logging.info('-------------------analyze done----------------------')
        logging.info('list of good %d stocks%s:' % (len(selected_stocks),
                     options.output and ' and save plots to %s' % options.output or ''))

        for stock in selected_stocks:
            logging.info('%s', stock)
        logging.info('global market status: %s', 'Good!' if global_status else 'Bad!')

        if options.output:
            if not os.path.exists(options.output):
                os.makedirs(options.output)
            plot = StockPlot()
            pbar = tqdm(selected_stocks)
            for stock in pbar:
                pbar.set_description("Ploting %s[%s]" % (stock.code, stock.name))
                plot.plot_hist(stock, os.path.join(options.output, '%s[%s].png' % (stock.code, stock.name)))

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
