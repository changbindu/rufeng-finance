# coding=utf-8
__author__ = 'Du, Changbin <changbin.du@gmail.com>'

import sys
if sys.version_info < (3, 4):
    raise RuntimeError('at least Python 3.4 is required to run')
sys.path.insert(0, 'tushare')

import logging.config, coloredlogs
from optparse import OptionParser
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
                "\n  list     - list all stocks in local database" + \
                "\n  plot     - plot stock diagram" + \
                "\n  analyze  - analyze our stocks" + \
                "\n  monitor  - monitor realtime status"
        parser = OptionParser(usage=usage)

        parser.add_option("--config",
                          metavar="FILE", dest="config", default="config.yaml",
                          help="specific config file"),

        parser.add_option("-s", "--selector",
                      default="all", dest="selector",
                      help="selectors: all, trend, macd, or hot [default: %default]")

        # for download options
        parser.add_option("-t", "--threads",
                          type="int", dest="threads", default=20,
                          help="threads number to work")
        parser.add_option("-a", "--force_update",
                          action="store_true", dest="force_update", default=False,
                          help="download data ignore local existing data")

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
            'list':     self.cmd_list,
            'plot':     self.cmd_plot,
            'analyze':  self.cmd_analyze,
            'monitor':  self.cmd_monitor
        }

        if command not in cmd_map:
            parser.error('invalid command')
            return -1
        if cmd_map[command] is None:
            logging.error('command \'%s\' is not implemented yet', command)
            return -1

        if options.config:
            print("using config %s" % options.config)
            self._config = yaml.load(open(options.config))

        cmd_map[command](options, cmd_args)
        return 0

    def cmd_download(self, options, cmd_args):
        data_full = self._dm.pick_data(options.threads, options.force_update)
        if not data_full:
            logging.warning('not all data successfully picked')

    def cmd_list(self, options, cmd_args):
        self._dm.load_from_db()
        self._dm.list_availabe_stocks()

    def cmd_plot(self, options, cmd_args):
        if len(cmd_args) != 1:
            logging.error("missing argument stock code")
            return -1
        code = cmd_args[0]

        self._dm.load_from_db()

        if code not in self._dm.stocks:
            logging.error('unknown stock %s', code)
            return

        stock = self._dm.stocks[code]
        print("show diagram for stock %s ...", stock)
        if options.qfq:
            StockPlot().plot_qfq(stock)
        else:
            StockPlot().plot_hist(stock)

    def cmd_analyze(self, options, cmd_args):
        self._dm.load_from_db()

        analyzer = Analyzer()
        analyzer.stocks = self._dm.stocks
        analyzer.indexs = self._dm.indexes
        logging.info('-----------invoking data analyzer module-------------')
        analyzer.analyze()
        logging.info('-------------------analyze done----------------------')

    def cmd_monitor(self, options, cmd_args):
        config = self._config['monitor']
        logging.info('monitor config:\n%s', yaml.dump(config))
        StockMonitor(config).start_and_join()

if __name__ == '__main__':
    # coloredlogs.DEFAULT_LOG_FORMAT = '%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s'
    coloredlogs.DEFAULT_LOG_FORMAT = '%(asctime)s %(message)s'
    coloredlogs.install(level='DEBUG')
    RufengFinance().main(len(sys.argv), sys.argv)
    logging.info("exiting...")