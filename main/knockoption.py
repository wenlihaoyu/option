# -*- coding: utf-8 -*-
"""
Created on Thu Sep  1 13:42:41 2016
敲出式期权
@author: lywen
结汇的时候就是高于，购汇的时候是低于
"""


from help.help import getNow,strTodate
from scipy import stats
import numpy as np

def knockoption(Setdate,SetRate,deliverydate,currentRate,LockedRate,kncockRate,SellRate,BuyRate,delta,trade_type):
    """
    设定敲出汇率，定价日高于/低于敲出汇率时，则交易自动敲出；
    例：公司预计3个月后有笔欧元收款100万，拟操作敲出式远期，卖欧元买美元
    锁定汇率：1.13，敲出汇率：1.05
    情景分析：IF 厘定日汇率>=1.05,则公司以1.13卖出欧元买入美元
               厘定日汇率<1.05,则交易敲出（取消）。
    
        Setdate:厘定日
        SetRate:厘定日汇率
        deliverydate:交割日
        
        currentRate:实时汇率
        LockedRate:锁定汇率
        kncockRate:敲出汇率
        SellRate:本币利率
        BuyRate:外币利率
        delta:汇率波动率
        trade_type:结汇还是收汇
    """
    Now = strTodate(getNow(),'%Y-%m-%d %H:%M:%S')
    Setdate = strTodate(Setdate+' 16:30:00','%Y-%m-%d %H:%M:%S')
    deliverydate = strTodate(deliverydate+' 16:30:00','%Y-%m-%d %H:%M:%S')
    SellRate = SellRate/360.0*365
    BuyRate  = BuyRate / 360.0*365
    T = (deliverydate - Now).total_seconds() ##交割剩余时间
    T = T/1.0/60/60/24##换算到多少天
    set_t = (Setdate - Now).total_seconds()/1.0/60/60/24/365
    if set_t<0:
        set_t=0
    p=1
    if Now < Setdate or SetRate is None:
        ##判断当前时间是否已过拟定日
        S =   currentRate
        K =   kncockRate
        t = T/365
        d1 = np.log(S/K /np.exp(-(BuyRate - SellRate )*set_t))/delta/np.sqrt(set_t)+ delta*np.sqrt(set_t)/2
        d2 = d1-delta*np.sqrt(set_t)
        #N1 = stats.norm.cdf(d1)  
        N2 = stats.norm.cdf(d2)
        
        if trade_type==u'1':
            ##小于敲出汇率时敲除
            ##期望成交金额 N2 + 0*(1-N2)
            p = N2
                   
        elif trade_type==u'2':
            ##大与敲出汇率时敲除
            ##期望成交金额 0*N2 + (1-N2)
            p = 1 - N2
        else:
            p=0
        
        
    else:
        if SetRate>kncockRate:##判断厘定日汇率大于敲出汇率，那么就敲出
           if   trade_type==u'1':
                p = 1
           elif trade_type==u'2':
                p=0
           else:
               p=0
        else:
            if   trade_type==u'1':
                p = 0
            elif trade_type==u'2':
                p=1
            else:
               p=0
            
    ##定价 p*
    S0 = LockedRate* np.exp(-(BuyRate -SellRate) *t)
    St = currentRate
    return p*(St - S0)/currentRate        
    
    
        
        
