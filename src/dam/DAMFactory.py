'''
Created on Nov 9, 2011

@author: ppa
'''

from lib.errors import Errors, UfException

class DAMFactory(object):
    ''' DAM factory '''
    @staticmethod
    def createDAM(damType, settings = None):
        ''' create DAM '''
        if 'yahoo' == damType:
            from dam.yahooDAM import YahooDAM
            dam = YahooDAM()
        elif 'google' == damType:
            from dam.googleDAM import GoogleDAM
            dam = GoogleDAM()
        elif 'excel' == damType:
            from dam.excelDAM import ExcelDAM
            dam = ExcelDAM()
        elif 'hbase' == damType:
            from dam.hbaseDAM import HBaseDAM
            dam = HBaseDAM()
        elif 'sql' == damType:
            from dam.sqlDAM import SqlDAM
            dam = SqlDAM()
        elif 'eastfinance' == damType:
            from dam.eastmoneyDAM import EastmoneyDAM
            dam = EastmoneyDAM()
        else:
            raise UfException(Errors.INVALID_DAM_TYPE,
                              "DAM type is invalid %s" % damType)

        dam.setup(settings)
        return dam

    @staticmethod
    def getAvailableTypes():
        ''' return all available types '''
        return ['yahoo', 'google', 'excel', 'hbase', 'sql', 'eastfinance']
