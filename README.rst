# rufeng-finance for python, expermental.
(Use modified Tushare as data download backend.)
.. code::
   $ source autocompletion.sh 
   $ rufeng_finance 
   A finance ayalyzer of python.
   Copyright (C) 2016 Changbin Du <changbin.du@gmail.com>. All rights reserved.
   (Analyzer) 
   analyze   download  edit      list      monitor   quit      
   check     drop      help      load      plot      
   (Analyzer) download
   using config config.yaml
   2017-05-07 10:44:06 try to load stock data from local database
   100%|██████████████████████████████████████████████████████████████████| 820/820 [00:24<00:00, 33.76it/s]
   2017-05-07 10:44:30 loaded 820 stocks
   2017-05-07 10:44:31 loaded 6 indexes
   2017-05-07 10:44:31 getting basics from tushare
   2017-05-07 10:44:31 getting stock list from tushare
   2017-05-07 10:47:23 tushare listed 3189 stocks
   2017-05-07 10:47:23 totally there are 3189 listed companies
   2017-05-07 10:47:23 get indexes from tushare
   2017-05-07 10:47:23 get all hist data of indexes
   2017-05-07 10:47:23 getting history data of 6 stocks/indexes using 1 threads
   2017-05-07 10:47:23 [1/6] picking hist data (2016-12-23-2017-05-06) of {"code": "000016", "name": "上证50"}
   2017-05-07 10:47:24 {"code": "000016", "name": "上证50"}: 826 days trading data, appended 87 days
   2017-05-07 10:47:24 [2/6] picking hist data (2016-12-23-2017-05-06) of {"code": "000001", "name": "上证指数"}
   2017-05-07 10:47:24 {"code": "000001", "name": "上证指数"}: 826 days trading data, appended 87 days
   2017-05-07 10:47:24 [3/6] picking hist data (2016-12-23-2017-05-06) of {"code": "000300", "name": "沪深300指数"}
   2017-05-07 10:47:25 {"code": "000300", "name": "沪深300指数"}: 825 days trading data, appended 88 days
   2017-05-07 10:47:25 [4/6] picking hist data (2016-12-23-2017-05-06) of {"code": "399005", "name": "创业板"}
   ...
.. image:: https://github.com/changbindu/rufeng-finance/blob/master/report.png
