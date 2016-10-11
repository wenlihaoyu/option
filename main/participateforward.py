# -*- coding: utf-8 -*-
"""
Created on Thu Sep  1 11:05:10 2016
参与式远期
@author: lywen
"""

from help.help import getNow,strTodate
from scipy import stats
import numpy as np

def participateforward(Setdate,SetRate,deliverydate,currentRate,LockedRate,SellRate,BuyRate,delta):
    """
    参与式远期
    例：公司预计3个月后有笔200万美元收汇，拟操作参与式远期
    锁定汇率6.73，本金为100万美元
    情景分析：
    IF 厘定日即期汇率<=6.73,则本金交割100万美元
    厘定日即期汇率>6.73，则本金交割本金*2,即200万美元
    
        Setdate:厘定日
        SetRate:厘定日汇率
        deliverydate:交割日
        
        currentRate:实时汇率
        LockedRate:锁定汇率
        SellRate:本币利率
        BuyRate:外币利率
        delta:汇率波动率
    """
    Now = strTodate(getNow(),'%Y-%m-%d %H:%M:%S')
    Setdate = strTodate(Setdate+' 16:30:00','%Y-%m-%d %H:%M:%S')##厘定日下午16:30:00
    deliverydate = strTodate(deliverydate+' 16:30:00','%Y-%m-%d %H:%M:%S')##交割日期为当天下午16:30:00
    SellRate = SellRate/360.0*365
    BuyRate  = BuyRate/360.0*365
    T = (deliverydate - Now).total_seconds() ##交割剩余时间
    T = T/1.0/60/60/24##换算到多少天
    if T<0:
        T=0
    p=1
    set_t = (Setdate - Now).total_seconds()/1.0/60/60/24/365##当前时间距离厘定日剩余的时间
    if set_t<0:
        set_t=0
   
    if Now < Setdate or SetRate is None:
        ##判断当前时间是否已过拟定日
        S =   currentRate##实时汇率
        K =   LockedRate##锁定汇率
        t = T/365
        d1 = np.log(S/K /np.exp(-(SellRate -BuyRate)*set_t))/delta/np.sqrt(set_t)+ delta*np.sqrt(set_t)/2
        d2 = d1-delta*np.sqrt(set_t)
        #N1 = stats.norm.cdf(d1)  
        N2 = stats.norm.cdf(d2)##厘定日汇率大于锁定汇率的概率
        
        ##期望成交金额 N2 + 2*(1-N2)
        p = 2 - N2
        
    else:
        if SetRate<=LockedRate:
            p = 1
        else:
            p = 2
            
    ##定价 p*
    S0 = LockedRate* np.exp((BuyRate -SellRate) *t)
    St = currentRate
    return p*(St - S0)/currentRate        
    
    
