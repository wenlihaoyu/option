# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 10:43:16 2016
普通远期：公司在未来某个时刻（交割日）以锁定汇率卖出币种买入另一个币种
    买入一单位外币的定价
    CurrencySell:卖出货币
    CurrencyBuy:买入货币
    SellRate:卖出货币利率
    BuyRate:买入货币拆借利率
    deliverydate:交割日期
    LockedRate:锁定汇率
    currentRate:实时汇率

@author: lywen
"""
from help.help import getNow,strTodate
import numpy as np
##普通远期
##
def OrdinaryForward(SellRate,BuyRate,deliverydate,LockedRate,currentRate):
    """
    普通远期：公司在未来某个时刻（交割日）以锁定汇率卖出币种买入另一个币种
    买入一单位外币的定价
    CurrencySell:卖出货币
    CurrencyBuy:买入货币
    SellRate:卖出货币利率
    BuyRate:买入货币拆借利率
    deliverydate:交割日期
    LockedRate:锁定汇率
    currentRate:实时汇率
    """
    Now = strTodate(getNow(),'%Y-%m-%d %H:%M:%S')##获取当前时间
    deliverydate = strTodate(deliverydate+' 16:30:00','%Y-%m-%d %H:%M:%S')
    T = (deliverydate - Now).total_seconds() ##交割剩余时间
    T = T/1.0/60/60/24##换算到多少天
    if T<0:
        T=0
    
    SellRate_update = SellRate/360.0##调整利率
    BuyRate_update =  BuyRate/360.0##调整利率
    S0 = LockedRate* np.exp((BuyRate_update -SellRate_update) *T)
    St = currentRate
    return (St - S0)/currentRate