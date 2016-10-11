# -*- coding: utf-8 -*-
"""
Created on Tue Aug 30 09:17:50 2016
CollaOption 领式期权计算
@author: lywen
"""


from job import option
from help.help import getNow,getRate,getcurrency,dateTostr
from config.postgres  import  table_collars_option##table name
from database.mongodb import  RateExchange
from database.mongodb import  BankRate
from database.database import postgersql
from numpy import float64

from main.collaoption     import CollaOption
class CollaOptions(option):
    """
    CollaOption 领式期权计算
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
    """

    def __init__(self,delta=0.1):
        option.__init__(self)
        self.table = table_collars_option
        self.delta = delta##波动率
        self.getDataFromPostgres()
        self.getDataFromMongo()
        self.updateDataToPostgres()
        
        
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
               currency_dict[currency_pair] = RE[0]['Close']##实时汇率 
        self.currency_dict = currency_dict
        
        ##bank_rate
        forwarddict= {}
        for lst in self.data:
            sell_currency = lst['sell_currency']
            sell_currency_index = getcurrency(sell_currency)##拆借利率类型
            
            buy_currency  = lst['buy_currency']
            buy_currency_index = getcurrency(buy_currency)##拆借利率类型
            
            currency_pair = lst['currency_pair']
            ratetype = getRate((lst['delivery_date'] -lst['trade_date']).days)##拆借利率期限
            SellRate = BankRate(sell_currency_index,ratetype).getMax()##卖出本币的利率
            BuyRate  = BankRate(buy_currency_index,ratetype).getMax()##买入货币的利率
            sell_amount = float64(lst['sell_amount'])
            ##获取厘定日的汇率，如果还未到厘定日，那么汇率返回None
            Setdate = dateTostr(lst['determined_date'])##厘定日
            SetRate = RateExchange(currency_pair).getdayMax(Setdate)##厘定日汇率
            if SetRate ==[]:
                SetRate = None## 还未到厘定日
            
            
            ##买入货币的拆借 利率修正值
            if BuyRate is not  None and BuyRate !=[]:
                BuyRate=float64(BuyRate[0]['rate'])/100.0
                
            ##买出货币的拆借 利率修正值    
            if SellRate is not  None and SellRate !=[]:
                SellRate = float64(SellRate[0]['rate'])/100.0
                
            ## 执行汇率上下限
            strikeLowerRate = float64(lst['exe_doexrate'])
            strikeUpperRate = float64(lst['exe_upexrate'])
            
                
            
            currentRate = currency_dict[currency_pair]
            deliverydate = dateTostr(lst['delivery_date'])
            
            if sell_currency+buy_currency!=currency_pair:
               #strikeLowerRate = 1.0/strikeLowerRate
               #strikeUpperRate = 1.0/strikeUpperRate
               #currentRate = 1.0/currentRate
               BuyRate,SellRate = SellRate,BuyRate
               
               
            forwarddict[lst['id']] = self.cumputeLost(Setdate,SetRate,deliverydate,strikeLowerRate,strikeUpperRate,currentRate,SellRate,BuyRate,self.delta,sell_amount)
            if sell_currency+buy_currency!=currency_pair:
                forwarddict[lst['id']] =forwarddict[lst['id']]/currentRate
        self.forwarddict = forwarddict
            
                
    
    def getDataFromPostgres(self):
        
        
        Now = getNow('%Y-%m-%d')
  
        post = postgersql()
        colname = ['id',
                    'trade_id',
                    'currency_pair',
                    'sell_currency',
                    'buy_currency',
                    'sell_amount',
                    'trade_date',
                    'determined_date',
                    'delivery_date',
                    'exe_doexrate',
                    'exe_upexrate']
        wherestring = """ delivery_date>='%s'"""%Now
       
        self.data = post.select(self.table,colname,wherestring)
        
    def  cumputeLost(self,Setdate,SetRate,deliverydate,strikeLowerRate,strikeUpperRate,currentRate,SellRate,BuyRate,delta,sell_amount):
       if SellRate in [None,[]] or BuyRate in [None,[]]:
           return None
       else:
           ##return sell_amount*CollaOption(Setdate,SetRate,deliverydate,strikeLowerRate,strikeUpperRate,currentRate,SellRate,BuyRate,delta)
           return CollaOption(Setdate,SetRate,deliverydate,strikeLowerRate,strikeUpperRate,currentRate,SellRate,BuyRate,delta)

        
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