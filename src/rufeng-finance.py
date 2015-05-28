#coding=utf-8
__author__ = 'changbi'

from optparse import OptionParser
from dataManager import DataManager
from selectEngine import SelectEngine
from lib.util import logger
from lib.stockPlot import StockPlot

import sys
reload(sys)
sys.setdefaultencoding( "utf-8" )

class RufengFinance(object):
    def __init__(self):
        self.dataManager = None
        self.selectEngine = None
        self.config = None

    def main(self):
        usage = "usage: %prog [options] <cmd> arg1 arg2\n" + \
                "\n<cmd> should be one of download/list/plot/select:" + \
                "\n  download - download stock data from finance service" + \
                "\n  list - list all stocks in local database" + \
                "\n  plot - plot stock diagram" + \
                "\n  select - use selectors to filter stocks"
        parser = OptionParser(usage=usage)
        parser.add_option("-l", "--local",
                  action="store_true", dest="local", default=False,
                  help="update local stock only")
        parser.add_option("-t", "--threads",
                  type="int", dest="threads", default=5,
                  help = "threads number to work")
        parser.add_option("-a", "--append",
                  action="store_true", dest="append", default=True,
                  help="download data by append [default]")
        parser.add_option("--config",
                  metavar="FILE", help="specific config file"),
        parser.add_option("--dbfile",
                  metavar="FILE", dest="dbfile", default="data/stock.sqlite",
                  help="specific database file [default: data/stock.sqlite]"),
        parser.add_option("-s", "--selector",
                  default="all", dest = "selector",
                  help="selectors: all, trend, macd, or hot [default: %default]")

        (options, args) = parser.parse_args()
        if len(args) < 1:
            parser.error("incorrect number of arguments, missing cmd")
            return -1
        command = args[0]
        cmd_args = args[1:] if len(args) > 1 else ()

        if options.config:
            logger.info("using config %s" % options.config)
        self.dataManager = DataManager(dbpath=options.dbfile)
        self.selectEngine = SelectEngine()

        if command == "download":
            logger.info("download data ...")
            if len(cmd_args) == 0:
                self.dataManager.downloadAll(localOnly=options.local, append=options.append, threads=options.threads)
            else:
                self.dataManager.downloadStocks(cmd_args, append=options.append, threads=options.threads)
        elif command == "plot":
            if len(cmd_args) != 1:
                parser.error("missing argument stock symbol")
                return -1
            symbol = cmd_args[0]
            logger.info("show diagram for stock %s ..." % symbol)
            stock = self.dataManager.loadStockAndHistory(symbol)
            if stock is None:
                logger.error("stock %s is not found in database" % symbol)
                return -1
            plot = StockPlot(stock)
            plot.plot()
        elif command == "list":
            stocks = self.dataManager.loadAllStocks()
            print("List of stocks (symbol, name, price):")
            for stock in stocks:
                print("%s - %s - %d" % (stock.symbol, stock.name, stock.price))
        elif command == "select":
            pass
        else:
            parser.error("unrecognized command %s" % command)
            return -1

        return 0

if __name__ == '__main__':
    ret = RufengFinance().main()
    logger.info("exiting...")
    exit(ret)
