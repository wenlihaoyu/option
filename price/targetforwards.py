# -*- coding: utf-8 -*-
"""
Created on Fri Sep  9 14:32:34 2016
Target Redemption Forward
@author: lywen

"""
from job import option
from help.help import getNow,getRate,getcurrency
from config.postgres  import  table_frs_option
from database.mongodb import  RateExchange
from database.mongodb import  BankRate
from database.database import postgersql,mongodb
#from numpy import float64
from main.targetforward import  TargetRedemptionForward
import pandas as pd
import numpy as np

from help.help import timedelta

class TargetRedemptionForwards(option):
    """
    目标可赎回式远期
    """

    def __init__(self,Now):
        option.__init__(self)
       # self.delta  =delta
        self.table = table_frs_option
        self.Now = Now
        self.mongo = mongodb()
        self.getDataFromPostgres()##从post提取数据
        self.getDataFromMongo()##从mongo提取数据并更新损益
       # self.updateDataToPostgres()##更新数据到post
        
    def getDataFromMongo(self):
        """
        from mongo get the currency_pairs and bank_rate
        """
        if self.data !=[]:
           
           S = {}##货币对最新汇率
           spot  = {}
           #mongo = mongodb()
           trfdata = {}
           for lst in self.data:
               ##获取厘定日汇率，未到立定日，以None填充
               code = lst.get('currency_pair')
               date = lst.get('determined_date').strftime('%Y-%m-%d')
               determined_date_rate = getkline(code,date,self.mongo)##获取厘定日汇率
               lst.update({'determined_date_rate':determined_date_rate})
               
               sell_currency = lst['sell_currency']
               sell_currency_index = getcurrency(sell_currency)
            
               buy_currency  = lst['buy_currency']
               buy_currency_index = getcurrency(buy_currency)
               ratetype = getRate((lst['delivery_date'] -lst['trade_date']).days)
               SellRate = BankRate(sell_currency_index,ratetype).getMax()##卖出本币的利率
               BuyRate  = BankRate(buy_currency_index,ratetype).getMax()##买入货币的利率
               if SellRate is None or SellRate==[]:
                   SellRate = 0
               else:
                   SellRate = float(SellRate[0].get('rate'))
               if BuyRate is None or BuyRate==[]:
                   BuyRate = 0
               else:
                   BuyRate = float(BuyRate[0].get('rate'))   
                   
               if S.get(code) is None:
                   RE = RateExchange(code).getMax()
                   if RE is not None and RE !=[]:
                      S[code] =  RE[0].get('Close')##获取实时汇率
               
               if spot.get(code) is None:
                   dayspot = getdayspot(code,self.mongo)
                   dayspot = datafill(dayspot)
                   spot[code] = dayspot
                
               if trfdata.get(lst['trade_id']) is None:
                   lags = (lst['delivery_date'] -lst['trade_date']).days
                   trfdata[lst['trade_id']] = {'orderlist':[],
                                                'spotList':lagdata(spot[code],lags),##lags时间段收益时间序列
                                                 'S':S[code],##实时汇率
                                                 'SellRate':SellRate,##卖出货币拆解利率
                                                 'BuyRate':BuyRate,##买入货币拆解利率
                                                 'K':float(lst.get('rate')),##锁定汇率
                                                 'TIV':float(lst.get('trp')),##目标收益
                                                 'lags':lags,##每期时间间隔
                                                 'Now':self.Now,##损益计算时间
                                                 }
               trfdata[lst['trade_id']]['orderlist'].append(lst)
        self.trfdata = trfdata
                
    
    def getDataFromPostgres(self):
        """
        获取结构性产品的订单数据
        """
        post = postgersql()
        colname = [
              'id',                 
             'trade_id',
             'currency_pair',
             'sell_currency',
             'buy_currency',
             'sell_amount',
             'trade_date',
             'determined_date',
             'delivery_date',
             'trp',
             'rate'
                ]
        wherestring = None
       
        self.data = post.select(self.table,colname,wherestring)
        
    def  cumputeLost(self):
        """
        
        """
        Lost =[]
        for trade_id in self.trfdata:
            spotList  = self.trfdata[trade_id]['spotList']
            orderlist = self.trfdata[trade_id]['orderlist']
            S         = self.trfdata[trade_id]['S']
            K         = self.trfdata[trade_id]['K']
            SellRate  = self.trfdata[trade_id]['SellRate']
            BuyRate   = self.trfdata[trade_id]['BuyRate']
            Now       = self.trfdata[trade_id]['Now']
            
            lags      = self.trfdata[trade_id]['lags']
            TIV       = self.trfdata[trade_id]['TIV']
            TRF = TargetRedemptionForward(spotList,orderlist,S,K,SellRate,BuyRate,lags,Now,TIV)##计算损益值
            Lost.extend(TRF)
        
        
               
           
           
       
        
    def updateDataToPostgres(self):
        """
        将计算的损益更新到数据库
        """
        from database.database import postgersql
        post = postgersql()
        updatelist=[]
        wherelist =[]
        for key in self.forwarddict:
            if self.forwarddict[key] is not None:
               updatelist.append({'ex_pl':self.forwarddict[key]})
               wherelist.append({'trade_id':key})
          
        post.update(self.table,updatelist,wherelist)
        post.close()


def getkline(code,date,mongo):
    """
    code：汇率对
    date：日期
    获取指定日期指定汇率对的汇率
    """
   
    date = date+" 00:00:00"
    reslut =  mongo.select('kline',{'type':'5','code':code,'Time':date})
    
    if reslut!=[]:
        
        return reslut[0].get('High') /1.0 / reslut[0].get('PriceWeight')
    else:
        return None
        
        
        

def getdayspot(code,mongo):
    """
    获取汇率对历史记录时间序列
    code:汇率对
    mongo:数据库连接实例
    
    """
    spot = mongo.select('kline',{'type':'5','code':code})
    
    spot = pd.DataFrame(spot)
    spot = spot[['Time','Close','PriceWeight']]
    spot['Close'] = spot['Close']/spot['PriceWeight']
    spot['Time'] = spot['Time'].astype(np.datetime64).dt.strftime('%Y-%m-%d')
    return spot[['Time','Close']]
    
    
    
def datafill(spot):
    """填充无交易日期的汇率
        以上一个交易日的的收盘价进行填充
    """
    def dateseris(mindate,maxdate):
        
        date = timedelta(mindate,1)
        series = []
        while maxdate>=date:
            series.append(date)

            date = timedelta(date,1)

        return series

    spot = pd.merge(pd.DataFrame(dateseris(spot['Time'].min(),spot['Time'].max()),columns=['Time']),spot[['Time','Close']],on=['Time'],how='left' )
    spot = spot.sort_values('Time')
    for i in range(spot.shape[0]):
        if spot['Close'].values[i].__str__()=='nan':
            spot['Close'].values[i] = spot['Close'].values[i-1]
    return spot

def lagdata(spot,lags=30):
    """
    spot：每天外汇收益率时间序列
    lags：时间长度
    序列指定时间长度的收益率
    """
    spot = datafill(spot)
    
    spot['Close_%d'%lags] = np.repeat(None,lags).tolist() + spot['Close'].values[:-lags].tolist()
    spot =  spot.dropna()
    
    
    spot['Close_%d_rate'%lags] = (spot['Close'] - spot['Close_%d'%lags])/spot['Close_%d'%lags]
    
    return spot['Close_%d_rate'%lags].values
    
    

    
#for i in range(len(trf.data)):trf.data[i]['trade_id'] = i   
#trf.data = filter(lambda x:x['currency_pair']!='EUREUR',trf.data)