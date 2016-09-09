# -*- coding: utf-8 -*-
"""
Created on Fri Sep  9 13:59:07 2016
Target Redemption Forward
例：公司预计1-6月每月有100万美元收汇，拟操作目标赎回式远期提交收益
目标收益：0.5，每月交割1，每次100万美元，锁定汇率为6.75
情景分析：
IF SUM(100*(锁定汇率-市场汇率)<0.5)，则可按照锁定汇率卖出美元买入人民币；
 SUM(100*(锁定汇率-市场汇率)>0.5), 则交易自动敲出（取消）。
@author: lywen
"""

def TargetRedemptionForward(datalist,deliverydates):
    """
    datalist:历史汇率时间序列
             = [{'date':'2015-01-01','Close':6.7},...]
    deliverydates:各期交割日期
    
    
    """
