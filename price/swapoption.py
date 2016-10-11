# -*- coding: utf-8 -*-
"""
Created on Tue Aug 30 13:49:09 2016
swapoption 定价
@author: lywen
"""

from job import option
from help.help import getNow,dateTostr
from config.postgres   import  table_swaps_option##table name
from database.mongodb  import  RateExchange
#from database.mongodb  import  BankRate
from database.database import postgersql
from numpy import float64


from main.swapoption  import SwapOption
class SwapOptions(option):
    """
    区间式货币掉期or货币互换or封顶式期权:
        Setdate:厘定日
        SetRate:厘定日汇率
        deliverydate:交割日
        strikeLowerRate: 执行汇率下限
        strikeUpperRate:执行汇率上限
        currentRate:实时汇率
        SellRate:本币汇率
        BuyRate:外币汇率
        delta:汇率波动率
    """

    def __init__(self,delta=0.1):
        option.__init__(self)
        self.table = table_swaps_option
        self.delta = delta##波动率
        self.getDataFromPostgres()
        self.getDataFromMongo()
        #self.updateDataToPostgres()
        
        
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
            #sell_currency_index = getcurrency(sell_currency)##拆借利率类型
            
            buy_currency  = lst['buy_currency']
            #buy_currency_index = getcurrency(buy_currency)##拆借利率类型
            
            currency_pair = lst['currency_pair']
            #ratetype = getRate((lst['delivery_date'] -lst['trade_date']).days)##拆借利率期限
            #SellRate = BankRate(sell_currency_index, ratetype).getMax()##卖出本币的利率
            #BuyRate  = BankRate(buy_currency_index, ratetype).getMax()##买入货币的利率
            SellRate = float64(lst['pay_fix_rate']) ##支付固定利率
            BuyRate  = float64(lst['charge_fix_rate'])##收取浮动利息
            sell_amount = float64(lst['sell_amount'])##卖出金额
            LockedRate = float64(lst['exe_exrate'])##执行汇率
            capped_exrate  = None if lst['capped_exrate'] is None else float64(lst['capped_exrate']) ##封顶汇率
            
            rateway = lst['interest_pay_way']##付息方式
            ##获取厘定日的汇率，如果还未到厘定日，那么汇率返回None
            Setdate = dateTostr(lst['determined_date'])##厘定日
            SetRate = RateExchange(currency_pair).getdayMax(Setdate)##厘定日汇率
            
            if SetRate ==[]:
                SetRate = None## 还未到厘定日
                
            valuedate  = dateTostr(lst['value_date'])##起息日
            
            currentRate = currency_dict[currency_pair] ## 实时汇率
            deliverydate = dateTostr(lst['delivery_date'])## 交割日期
            trade_type = lst['trade_type']##交易类型
            if sell_currency+buy_currency !=currency_pair:
               #LockedRate = 1.0/LockedRate
               #capped_exrate = 1.0/capped_exrate
               #if SetRate is not None:
               #   SetRate = 1.0/SetRate
               #currentRate = 1.0/currentRate
               SellRate,BuyRate = BuyRate,SellRate
               
               
            forwarddict[lst['id']] = self.cumputeLost(Setdate,SetRate,valuedate,deliverydate,currentRate,SellRate,BuyRate,LockedRate,rateway,self.delta,sell_amount,capped_exrate,trade_type)
        self.forwarddict = forwarddict
            
                
    
    def getDataFromPostgres(self):
        
        
        Now = getNow('%Y-%m-%d')
  
        post = postgersql()
        colname = ['id',
                   'trade_id',
                   'currency_pair',
                   'sell_currency',
                   'buy_currency',
                   'trade_date',
                   'value_date',
                   'determined_date',
                   'delivery_date',
                   'sell_amount',
                   'exe_exrate',
                   'capped_exrate',
                   'pay_fix_rate',##支付固定利率
                   'charge_fix_rate',##收取固定利率
                   'interest_pay_way',##付息方式
                   'trade_type'##交易类型
                   ]
        wherestring = """ delivery_date>='%s'"""%Now
       
        self.data = post.select(self.table,colname,wherestring)
        
    def  cumputeLost(self,Setdate,SetRate,valuedate,deliverydate,currentRate,SellRate,BuyRate,LockedRate,rateway,delta,sell_amount,capped_exrate,trade_type):
       if SellRate in [None,[]] or BuyRate in [None,[]]:
           return None
       else:
           return SwapOption(Setdate,SetRate,valuedate,deliverydate,currentRate,SellRate,BuyRate,LockedRate,rateway,delta,capped_exrate,trade_type)
      
        
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
               wherelist.append({'id':key})
        
        post.update(self.table,updatelist,wherelist)
        post.close()    

