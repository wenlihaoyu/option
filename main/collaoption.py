# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 10:46:04 2016
领式期权
@author: lywen
"""
from help.help import getNow, strTodate
import numpy as np
from scipy import stats

def CollaOption(Setdate,SetRate,deliverydate,strikeLowerRate,strikeUpperRate,currentRate,SellRate,BuyRate,delta):
    """
        领式期权:
        Setdate:厘定日
        SetRate:厘定日汇率
        deliverydate:交割日
        strikeLowerRate: 执行汇率下限
        strikeUpperRate:执行汇率上限
        currentRate:实时汇率
        SellRate:本币汇率
        BuyRate:外币汇率
        delta:汇率波动率
        
        领式期权：公司与银行买入一个美元看涨期权，卖出一个美元看跌期权
        例：公司有一笔美元负债1000万，1个月后到期，叙做领式期权，
         执行汇率下限为6.6845，执行汇率上限为6.6846
    情景分析：
         IF 厘定日汇率<执行汇率下限，则公司在交割日以执行汇率下限卖出人民币买入美元；
            厘定日汇率>执行汇率上线，则公司在交割日以执行汇率上限卖出人民币买入美元
    对于欧式期权：
        1）看涨期权定价：
            S*N(d1) - K*exp(-rt)*N(d2),其中d1 = ln(S/K/exp(-rt))/delta/sqrt(t), d2 = d1 - delta*sqrt(t),delta为波动率
        2) 看跌期权
            S*[N(d1) -1] - K*exp(-rt)*[N[d2]-1]
    美式期权：
        采用二叉树对美式期权进行定价：
          1）将时间分成长度为n个相等的小区间：长度为delta_t;
          2)在每一个节点，初始价格S以概率p上升到u*S或者以1-p的概率下降到dS:
            u = exp(delta*sqrt(delta_t))
            d = 1/u
            p = [exp((r-r_)*delta_t) - d] / (u-d),r,r_分别为国内、国外利率
                               
    """
    ##判断当前日期是否已过厘定日期
    Now = strTodate(getNow('%Y-%m-%d %H:%M:%S'),'%Y-%m-%d %H:%M:%S')
    deliverydate = strTodate(deliverydate+' 16:30:00','%Y-%m-%d %H:%M:%S')
    Setdate = strTodate(Setdate+' 16:30:00','%Y-%m-%d %H:%M:%S')##下午16:30:00的厘定汇率
    if Now<=Setdate or SetRate is None:
        ##看涨期权定价
        strikeRate_U = strikeUpperRate
        strikeRate_L = strikeLowerRate
       
        
    else:
        ##如果已过厘定日，则转为以执行价格执行的看涨和看跌欧式期权
        if  SetRate>=strikeUpperRate:
            #strikeRate = strikeUpperRate
            strikeRate_U = strikeUpperRate
            strikeRate_L = strikeUpperRate
        else:
            #strikeRate = strikeLowerRate
            strikeRate_U = strikeLowerRate
            strikeRate_L = strikeLowerRate

    S = currentRate##当前汇率
    #K = strikeRate##执行汇率
    T = (deliverydate - Now).total_seconds() ##交割剩余时间
    T = T/1.0/60/60/24##换算到多少天
    if T<0:
        T=0
    yeardays = 365
    SellRate_update = SellRate/360.0*yeardays##调整利率
    BuyRate_update =  BuyRate/360.0*yeardays##调整利率
    r = (SellRate_update-BuyRate_update)
    t = T/1.0/yeardays
    K = strikeRate_U
    d1_U = np.log(S/1.0/K/np.exp(-r*t))/delta/np.sqrt(t)+delta*np.sqrt(t)/2
    d2_U = d1_U- delta*np.sqrt(t)
    ##看涨期权的价值
    c  = S*stats.norm.cdf(d1_U) - K*np.exp(-r*t)*stats.norm.cdf(d2_U)##stats.norm.cdf正太分布累计概率
    
    K = strikeRate_L
    d1_L = np.log(S/1.0/K/np.exp(-r*t))/delta/np.sqrt(t)+delta*np.sqrt(t)/2
    d2_L = d1_L- delta*np.sqrt(t)
    ##看跌期权的价值
    p  = S*(stats.norm.cdf(d1_L)-1) - K*np.exp(-r*t)*(stats.norm.cdf(d2_L)-1)##stats.norm.cdf正太分布累计概率
    

    return (c+p)/currentRate
    