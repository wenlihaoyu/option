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
import numpy as np
import pandas as pd
def TargetRedemptionForward(spotList,orderlist,S,K,SellRate,BuyRate,logs,Now,TIV):
    """
    spotList:汇率时间序列图
             = [{'date':'2015-01-01','Close':6.7},...]
    orderlist: 赎回远期订单数据
    orderlist= [{'buy_currency': 'EUR',## 买入货币
                 'currency_pair': 'EURCNY',##汇率对
                 'delivery_date': datetime.date(2016, 10, 1),##交易时间
                 'determined_date': datetime.date(2016, 10, 1),##立定日日期
                 'determined_date_rate': None,##厘定日汇率
                 'rate': Decimal('7.5949'),##锁定汇率
                 'sell_amount': Decimal('10930603.84'),##卖出金额
                 'sell_currency': 'CNY',##卖出货币
                 'trade_date': datetime.date(2016, 8, 10),##交易日期
                 'trade_id': None,##交易单号
                 'trp': Decimal('0.09')}##目标收益
                 ,...]
    S:实时汇率,
    R:锁定汇率
    SellRate:卖出货币利率
    
    BuyRate:买入货币利率
    logs:每期交割时间间隔
    Now:损益计算时间
    TIV:目标收益
    """
    orderlist = pd.DataFrame(orderlist)
    orderlist = orderlist.sort_values('delivery_date')
    
    MIC = 0
    orderlist['MIC'] = orderlist['determined_date_rate'].map(lambda x:0 if x.__str__()=='nan' else max([K-x,0]))
    
    for x in orderlist['determined_date_rate'].values:
        if x.__str__()=='nan':
            break
        else:
            MIC += max([K-x,0])
        if  MIC>=TIV:
            pass
        
    #MIC = map(lambda x:0 if x<0 else x,orderlist['K'] - K)
    
    
    
    
    
def simulationSpot(S, K, dateList, Rdistribute, lags = 30, MIC = 0, TIV = 0.05):
    """
    S:当前价格
    R:锁定价格
    Rdistribute:该汇率的历史收益率分布图
    lags:默认收益率的天数，如果date天数小于 lags，那么收益的系数date/lags
    dateList:模拟的时间长度,[15,30,30,30,30]
    MIC: 截至当前时间已获得累计收益
    TIV：目标收益
    以当前价格模拟未来汇率的变得趋势，及收益情况
    
    """
    X = []
    for date in dateList:
        r = np.random.choice(Rdistribute,1)[0]
        
        if X ==[]:
           x = S*(1+date/1.0/lags*r)
            
        else:
            x = X[-1]*(1+date/1.0/lags*r)
        X.append(x)
    return X
    