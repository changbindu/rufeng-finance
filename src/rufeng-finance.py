#coding=utf-8
__author__ = 'changbi'

from optparse import OptionParser
from dataManager import DataManager
from selectEngine import SelectEngine
from lib.util import logger
from lib.stockPlot import StockPlot

class RufengFinance(object):
    def __init__(self):
        self.dataManager = DataManager()
        self.selectEngine = SelectEngine()
        self.config = None

    def main(self):
        usage = "usage: %prog [options] arg1 arg2"
        parser = OptionParser(usage=usage)
        parser.add_option("-d", "--download",
                  action="store_true", dest="download", default=False,
                  help="download stock data from finance service")
        parser.add_option("-a", "--append",
                  action="store_false", dest="append",
                  help="download data by append [default]")
        parser.add_option("-c", "--config",
                  metavar="FILE", help="specific config file"),
        parser.add_option("-s", "--selector",
                  default="all", dest = "selector",
                  help="selectors: all, trend, macd, or hot [default: %default]")
        parser.add_option("-p", "--plot",
                  action="store_true", dest="plot", default=False,
                  help="plot stock diagram")

        (options, args) = parser.parse_args()
        if len(args) < 0:
            parser.error("incorrect number of arguments")
            return -1
        if options.config:
            logger.info("using config %s" % options.config)
        if options.download:
            logger.info("download data ...")
            self.dataManager.downloadAll(options.append)
        if options.plot:
            logger.info("show diagram for stock %s ..." % args[0])
            stock = self.dataManager.loadStock(args[0])
            plot = StockPlot(stock)
            plot.plot(False)

        return 0

if __name__ == '__main__':
    ret = RufengFinance().main()
    logger.info("exiting...")
    exit(ret)
