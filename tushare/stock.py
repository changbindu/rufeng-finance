# coding=utf-8
__author__ = 'Du, Changbin <changbin.du@gmail.com>'

import json


class Fundamental(object):
    ''' fundamental class '''
    def __init__(self):
        self.sector = None
        self.industry = None
        self.summary = None
        self.totalShare = 0
        self.tradableShare = 0
        self.priceEarning = 0
        self.netAsset = 0
        self.income = 0
        self.netIncome = 0


class Stock(object):
    ''' stock class'''
    def __init__(self):
        # Basics
        self.code = None # 代码
        self.name = None # 名称
        self.industry = None # 所属行业
        self.area = None # 地区
        self.pe = None # 市盈率
        self.outstanding = None # 流通股本
        self.totals = None # 总股本(万)
        self.totalAssets = None # 总资产(万)
        self.liquidAssets = None # 流动资产
        self.fixedAssets = None # 固定资产
        self.reserved = None # 公积金
        self.reservedPerShare = None # 每股公积金
        self.esp = None # 每股收益 (FIXME: should be 'eps')
        self.eps_yoy = None # 每股收益同比( %)
        self.bvps = None # 每股净资
        self.pb = None # 市净率
        self.timeToMarket = None # 上市日期
        self.roe = None # 净资产收益率( %)
        self.epcf = None # 每股现金流量(元)
        self.net_profits = None # 净利润(万元)
        self.profits_yoy = None # 净利润同比( %)
        self.net_profit_ratio = None # 净利率( %)
        self.gross_profit_rate = None # 毛利率( %)
        self.business_income = None # 营业收入(百万元)
        self.bips = None # 每股主营业务收入(元)
        self.distrib = None # 分配方案
        self.report_date = None # 发布日期
        self.arturnover = None # 应收账款周转率(次)
        self.arturndays = None # 应收账款周转天数(天)
        self.inventory_turnover = None # 存货周转率(次)
        self.inventory_days = None # 存货周转天数(天)
        self.currentasset_turnover = None # 流动资产周转率(次)
        self.currentasset_days = None # 流动资产周转天数(天)
        self.mbrg = None # 主营业务收入增长率( %)
        self.nprg = None # 净利润增长率( %)
        self.nav = None # 净资产增长率
        self.targ = None # 总资产增长率
        self.epsg = None # 每股收益增长率
        self.seg = None # 股东权益增长率
        self.currentratio = None # 流动比率
        self.quickratio = None # 速动比率
        self.cashratio = None # 现金比率
        self.icratio = None # 利息支付倍数
        self.sheqratio = None # 股东权益比率
        self.adratio = None # 股东权益增长率
        self.cf_sales = None # 经营现金净流量对销售收入比率
        self.rateofreturn = None # 资产的经营现金流量回报率
        self.cf_nm = None # 经营现金净流量与净利润的比率
        self.cf_liabilities = None # 经营现金净流量对负债比率
        self.cashflowratio = None # 现金流量比率

        self.price = 0
        self.hist_data = None
        self.hist_qfq = None

    def __str__(self):
        ''' convert to string '''
        return json.dumps({"code": self.code,
                           "name": self.name,
                          }, ensure_ascii = False)