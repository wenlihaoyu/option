# -*- coding: utf-8 -*-
"""
Created on Tue Aug 30 13:32:45 2016
swap option 
@author: lywen
"""
from help.help import getNow,strTodate
from forward import OrdinaryForward
import numpy as np 
import datetime as dt
from scipy import stats

def SwapOption(Setdate,SetRate,valuedate,deliverydate,currentRate,SellRate,BuyRate,LockedRate,rateway,delta,capped_exrate,trade_type):
    """
    货币掉期
    公司将某个币种互换成另一个币种的资产或者负债
    例：公司有一笔美元负债1000万，利率3mlibor+0.5%,期限12个月，
       通过货币掉期将其互换成人民币负债，执行汇率6.800，公司支付人民币固定利率3%，
       收取美元浮动利率3mlibor+0.5%，则公司在交割日以执行汇率卖出人民币买入美元，
       同时按季支付固定利率，收取浮动利率。
    Setdate:厘定日期
    SetRate：厘定日汇率
    valuedate:起息日
    deliverydate:交割日期
    currentRate:实时汇率
    SellRate:本币固定汇率
    BuyRate:外币拆借浮动利息
    LockedRate：锁定成交汇率
    rateway:计息方式：按季支付、按月支付、操作时付息、到期一次性付息
    delta:波动率
    capped_exrate：封顶汇率
    trade_type:2,3,4分别表示:区间式货币掉期(利率进行互换+固定补贴)、货币掉期（利率互换）、封顶式期权(固定补贴)
    
    """
    Now = strTodate(getNow(),'%Y-%m-%d %H:%M:%S')
    #value = OrdinaryForward(SellRate,BuyRate,deliverydate,LockedRate,currentRate)##当前时刻普通外汇的定价
    Setdate  = strTodate(Setdate+' 16:30:00','%Y-%m-%d %H:%M:%S')##厘定日时间
    
    deliverydate = strTodate(deliverydate+' 16:30:00','%Y-%m-%d %H:%M:%S')
    valuedate = strTodate(valuedate)##起息日
    T = (deliverydate - Now).total_seconds() ##交割剩余时间
    T = T/1.0/60/60/24##换算到多少天
    #yeardays = 365
    SellRate_update = SellRate/360.0##调整利率
    BuyRate_update =  BuyRate/360.0##调整利率       
    times = (deliverydate - valuedate).days##交割日与起息日直接间隔天数
    if T<0:
        T=0
    ##  判断是否已过厘定日，是否获取汇率波动补贴
    if Now>=Setdate:
        if SetRate>capped_exrate:##厘定日汇率大于封顶汇率，公司获得补贴
            Lost = (capped_exrate - LockedRate)/LockedRate*np.exp(-(SellRate_update-BuyRate_update)*T)##补贴比例
        else:
            Lost=0
    else:##还未到厘定日，那么判断厘定日的汇率大于封顶式期权的概率，看做是以capped_exrate为交割价格的看涨欧式期权
        Lost = SwapOptionLost(currentRate,Now,deliverydate,SellRate_update,BuyRate_update,delta,capped_exrate)
        Lost = Lost*(capped_exrate - LockedRate)/LockedRate
    
    ##利率互换    
    if rateway=='按月支付':
        ##截止当前时间已支付的利息和收到的浮动利息
        ## 利息支付日期
        days = 30
    elif rateway=='按季支付':
        days = 90
    elif rateway=='到期一次性付息':
         None
    
        
    if rateway in ['按季支付','按月支付']:
        interval = int(np.ceil(times/days))##支付利息的次数
        
        dates = []
        for i in range(interval):
            if dates==[]:
                
                dates.append(valuedate+dt.timedelta(days))
            else:
                dates.append(dates[-1]+dt.timedelta(days))
        if dates[-1]>deliverydate:
            dates[-1]=deliverydate
        ##判断已付息的次数：
        ##判断当前时间是否已过厘定日期
        
        #那么将未来付息贴现到现在
        dayseconds = 60*60*24
        ts = np.array(map(lambda x:(x - (Now if Now<=deliverydate else deliverydate)).total_seconds()/dayseconds,dates ))
        ## 支付本币利息贴现
        checkout = SellRate_update*(np.exp(-SellRate_update*ts).sum())    
        checkin = BuyRate_update*(np.exp(-BuyRate_update*ts).sum())
                      
        
        
    
    else:##一次性付息
        checkin = T*BuyRate_update*np.exp(-T*BuyRate_update) 
        checkout =T*SellRate_update*np.exp(-T*SellRate_update)
    #print Lost
    #print trade_type, checkout,checkin,Lost
    if trade_type=='2':
        #区间式货币掉期(利率进行互换+固定补贴)
        return  (checkin - checkout)  +Lost
    elif trade_type=='3':
         #货币掉期（利率互换）
         return (checkin - checkout)
    elif trade_type=='4':
         #封顶式期权(固定补贴)
         return Lost
         
    
        
    
def SwapOptionLost(currentRate,Now,deliverydate,SellRate_update,BuyRate_update,delta,capped_exrate):
    """
    区间货币掉期补贴收益
    可以理解为欧式看涨期权
    """
    S = currentRate##当前汇率
    #K = strikeRate##执行汇率
    T = (deliverydate - Now).total_seconds() ##交割剩余时间
    T = T/1.0/60/60/24##换算到多少天
    if T<0:
        T=0
    
    #SellRate_update = SellRate/360.0*yeardays##调整利率
    #BuyRate_update =  BuyRate/360.0*yeardays##调整利率
    r = (SellRate_update-BuyRate_update)
    t = T/1.0
    K = capped_exrate
    d1 = np.log(S/1.0/K/np.exp(-r*t))/delta/np.sqrt(t)+delta*np.sqrt(t)/2
    d2= d1- delta*np.sqrt(t)
    
    
    ##看涨期权的价值
    #c  = S*stats.norm.cdf(d1) - K*np.exp(-r*t)*stats.norm.cdf(d2)##stats.norm.cdf正太分布累计概率
    return  np.exp(-r*t)*stats.norm.cdf(d2)
    
    
    