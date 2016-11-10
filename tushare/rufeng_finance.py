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


class RufengFinance(object):
    def __init__(self):
        self._dm = DataManager()
        self._config = None

    def main(self, argc, argv):
        usage = "usage: %prog [options] <cmd> arg1 arg2\n" + \
                "\n<cmd> should be one of download/list/plot/select:" + \
                "\n  download - download stock data from finance service" + \
                "\n  list     - list all stocks in local database" + \
                "\n  plot     - plot stock diagram" + \
                "\n  analyze  - analyze our stocks" + \
                "\n  monitor  - monitor realtime status"
        parser = OptionParser(usage=usage)
        parser.add_option("-l", "--local",
                          action="store_true", dest="local", default=False,
                          help="update local stock only")
        parser.add_option("-t", "--threads",
                          type="int", dest="threads", default=20,
                          help="threads number to work")
        parser.add_option("-a", "--append",
                          action="store_true", dest="append", default=True,
                          help="download data by append [default]")
        parser.add_option("--config",
                          metavar="FILE", dest="config", default="config.yaml",
                          help="specific config file"),
        parser.add_option("-s", "--selector",
                          default="all", dest="selector",
                          help="selectors: all, trend, macd, or hot [default: %default]")

        (options, args) = parser.parse_args()
        if len(args) < 1:
            parser.error("incorrect number of arguments, missing cmd")
            return -1

        command = args[0]
        cmd_args = args[1:] if len(args) > 1 else ()
        cmd_map = {
            'download': None,
            'list':     None,
            'plog':     None,
            'analyze':  self.cmd_analyze,
            'monitor':  None
        }

        if command not in cmd_map:
            logging.error('invalid command')
            return
        if cmd_map[command] is None:
            logging.error('command \'%s\' is not implemented yet', command)
            return

        if options.config:
            print("using config %s" % options.config)
            self._config = yaml.load(open(options.config))

        cmd_map[command](options, cmd_args)


    def cmd_analyze(self, options, cmd_args):
        if not self._dm.pick_data():
             logging.error('cannot start analyze because data is not full')
        else:
            analyzer = Analyzer()
            analyzer.stocks = self._dm.stocks
            analyzer.indexs = self._dm.indexes
            logging.info('-----------invoking data analyzer module-------------')
            analyzer.analyze()
            logging.info('-------------------analyze done----------------------')


if __name__ == '__main__':
    coloredlogs.DEFAULT_LOG_FORMAT = '%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s'
    coloredlogs.install(level='DEBUG')
    RufengFinance().main(len(sys.argv), sys.argv)
    logging.info("exiting...")