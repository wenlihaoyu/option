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
from help.help import strTodate
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
    ## 计算当前时间到未来各厘定日及交割日的时间
    orderlist['delivery_date'] = orderlist['delivery_date'].map(lambda  x:strTodate(x.strftime('%Y-%m-%d %H:%M:%S'),'%Y-%m-%d %H:%M:%S'))
    orderlist['determined_date'] = orderlist['determined_date'].map(lambda  x:strTodate(x.strftime('%Y-%m-%d %H:%M:%S'),'%Y-%m-%d %H:%M:%S'))

    orderlist['delivery_time'] =  (orderlist['delivery_date'] -Now).dt.total_seconds()/24.0/60/60
    determined_time = ((orderlist['determined_date'] -Now).dt.total_seconds()/24.0/60/60)

    orderlist['determined_time'] =  determined_time
    orderlist['determined_time'] = orderlist['determined_time'].diff()
    orderlist['determined_time'] = orderlist['determined_time'].fillna(determined_time[0])
    
    #MIC = 0
    ##判断历史累计收益是否已达到目标收益
    CumMIC = orderlist['determined_date_rate'].map(lambda x:0 if x.__str__()=='nan' else max([K-x,0])).sum()
    R = (SellRate - BuyRate)/360.0/100.0   ##两国货币拆解利率差
    #TIV = 0.5
    if orderlist['delivery_time'].max()<0:## 最后一次交割是否已经完成
        
        return None#orderlist.to_dict('records')
    elif CumMIC>=TIV :##累计收益是否达到目标收益:
        print '当前收益为:%f, 超过目标累计收益%f'%(CumMIC,TIV)
        orderlist_ = simulationSpot(S, K,orderlist, spotList,R,  TIV,times=1)
        
    else:
       
       orderlist_ = simulationSpot(S, K,orderlist, spotList,R,  TIV,times=1000)
    return orderlist_.to_dict('records')
    #MIC = map(lambda x:0 if x<0 else x,orderlist['K'] - K)
    
    
    
    
    
def simulationSpot(S, K,orderlist, Rdistribute,R,  TIV = 0.05,times=1000):
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
    temp = orderlist.to_dict('records')
    orderlist_ = orderlist.copy()
    #price = []
    global MIC
    MIC = 0
    orderlist_['price'] = 0.0
    #print S, K,R
    for i in range(times):
        spot = simulation(temp,S,Rdistribute)##模拟未来厘定日的价格走势
        
        spot = np.array(map(lambda x:addMic(max(K-x,0),TIV),spot))##判断是否已达到目标收益
        MIC = 0
        
        orderlist_['price'] += (S - K*np.exp(-R*orderlist_['delivery_time']))*spot
        #print orderlist_['price'].values/(i+1.0)
    sell_currency=orderlist_['sell_currency'].values[0]
    buy_currency =orderlist_['buy_currency'].values[0]
    code = orderlist_['currency_pair'].values[0]
    if sell_currency+buy_currency==code:
        
        orderlist_['price'] =orderlist_['price']/1.0/times/K
    else:
        orderlist_['price'] =orderlist_['price']/1.0/times/K/K
    return orderlist_

def addMic(x,TIV):
    
     global MIC
     MIC +=x
     if MIC - x>TIV:
         return 0##敲除
     else:
         return 1

     
    
def simulation(orderlist,S,Rdistribute):
    X = []
    for lst in orderlist:
        r = np.random.choice(Rdistribute,1)[0]
        
        date = lst['determined_time']
        if X ==[]:   
            tempS = S
        else:
            tempS = X[-1]
            
        if lst['determined_date_rate'].__str__()=='nan':
            ##未到厘定日，那么模拟厘定日汇率
            
               x = tempS*(1+date*r)
               
        else:
               x = lst['determined_date_rate']
        
        X.append(x)
  
    return X