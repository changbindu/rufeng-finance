__author__ = 'changbi'

from optparse import OptionParser
from dataManager import DataManager
from selectEngine import SelectEngine

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

        (options, args) = parser.parse_args()
        if len(args) < 0:
            parser.error("incorrect number of arguments")
            return -1
        if options.download:
            print("download data ...")
        if options.config:
            print("using config %s" % options.config)

        return 0

if __name__ == '__main__':
    exit(RufengFinance().main())
