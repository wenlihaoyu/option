# -*- coding: utf-8 -*-
"""
Created on Fri Sep  9 14:32:34 2016
Target Redemption Forward
@author: lywen

"""
#from job import option
from help.help import getNow,getRate,getcurrency,dateTostr
from config.postgres  import  table_frs_option
from database.mongodb import  RateExchange
from database.mongodb import  BankRate
from database.database import postgersql,mongodb
from numpy import float64
from main.targetforward import  TargetRedemptionForward
import pandas as pd
import numpy as np

from help.help import timedelta

class TargetRedemptionForwards(option):
    """
    目标可赎回式远期
    """

    def __init__(self):
        option.__init__(self)
       # self.delta  =delta
        self.table = table_frs_option
        self.mongo = mongodb()
        self.getDataFromPostgres()##从post提取数据
       # self.getDataFromMongo()##从mongo提取数据并更新损益
       # self.updateDataToPostgres()##更新数据到post
        
    def getDataFromMongo(self):
        """
        from mongo get the currency_pairs and bank_rate
        """
        ## currency_pairs
        currency_pairs = list(set(map(lambda x:x['currency_pair'],self.data)))
        currency_dict = {}
        for currency_pair in currency_pairs:
            RE = RateExchange(currency_pair).getMax()
            if RE is not None and RE !=[]:
               currency_dict[currency_pair] = RE[0]['Close']
        self.currency_dict = currency_dict
        
        ##bank_rate
        forwarddict= {}
        for lst in self.data:
            sell_currency = lst['sell_currency']
            sell_currency_index = getcurrency(sell_currency)
            
            buy_currency  = lst['buy_currency']
            buy_currency_index = getcurrency(buy_currency)
            
            currency_pair = lst['currency_pair']
            ratetype = getRate((lst['delivery_date'] -lst['trade_date']).days)
            SellRate = BankRate(sell_currency_index,ratetype).getMax()##卖出本币的利率
            BuyRate  = BankRate(buy_currency_index,ratetype).getMax()##买入货币的利率
            sell_amount = float64(lst['sell_amount'])
            Setdate = dateTostr(lst['determined_date'])
            SetRate = RateExchange(currency_pair).getdayMax(Setdate)##厘定日汇率
            
            if BuyRate is not  None and BuyRate !=[]:
                BuyRate=float(BuyRate[0]['rate'])/100.0
                
            if SellRate is not  None and SellRate !=[]:
                SellRate=float(SellRate[0]['rate'])/100.0
                
            LockedRate = float(lst['rate'])
            currentRate = currency_dict[currency_pair]
            deliverydate = dateTostr(lst['delivery_date'])
            
            if sell_currency+buy_currency!=currency_pair:
               LockedRate = 1.0/LockedRate
               currentRate = 1.0/currentRate
            forwarddict[lst['trade_id']] = self.cumputeLost(Setdate,SetRate,deliverydate,currentRate,LockedRate,SellRate,BuyRate,self.delta,sell_amount)
        self.forwarddict = forwarddict
        
          
                
    
    def getDataFromPostgres(self):
        
        
        #Now = getNow('%Y-%m-%d')
  
        post = postgersql()
        colname = [
                 
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
       
        data = post.select(self.table,colname,wherestring)
        
        if data !=[]:
           self.data ={}
           #mongo = mongodb()
           for lst in data:
               ##获取厘定日汇率，未到立定日，以None填充
               code = lst.get('currency_pair')
               date = lst.get('determined_date').strftime('%Y-%m-%d')
               determined_date_rate = getkline(code,date,self.mongo)
               #spot = getdayspot(code,self.mongo)##外汇时间序列
               #spot = datafill(spot) 
               #lagdata(spot,lags=30)
               
               lst.update({'determined_date_rate':determined_date_rate})
               if self.data.get(lst['trade_id']) is None:
                   self.data[lst['trade_id']] = []
               self.data[lst['trade_id']].append(lst)
           #mongo.close()
           for trade_id in self.data:
               pass
           self.data = data   
               
        
        
    def  cumputeLost(self,Setdate,SetRate,deliverydate,currentRate,LockedRate,SellRate,BuyRate,delta,sell_amount  ):
       if SellRate in [None,[]] or BuyRate in [None,[]]:
           return None
       else:
           return sell_amount*TargetRedemptionForward(Setdate,SetRate,deliverydate,currentRate,LockedRate,SellRate,BuyRate,delta)
      
        
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