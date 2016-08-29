# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 13:29:50 2016
main
@author: lywen
"""
from help.help import getNow,strTodate,getRate,getcurrency,dateTostr
from config.postgres  import  forward_option
from database.mongodb import  RateExchange
from database.mongodb import  BankRate
from database.database import postgersql

from main.forward     import OrdinaryForward

class option(object):
    """
    产品定价
    """
    def __init__(self):
        pass
    
    def getDataFromMongo(self):
        """
        从mongo获取拆借利率及实时汇率
        """
        pass
    
    def getDataFromPostgres(self):
        """
        从postgres获取结构产品数据
        """
        pass

    def cumputeLost(self):
        """
        计算结果行产品数据的损益
        """
        pass
    
    def updateDataToPostgres(self):
        """
        将计算的损益更新到数据库
        """
        pass
    


class forwards(option):
    """
    普通外汇远期定价
    """

    def __init__(self):
        option.__init__(self)
        self.getDataFromPostgres()
        self.getDataFromMongo()
        
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
            sell_amount = float(lst['sell_amount'])
            if BuyRate is not  None and BuyRate !=[]:
                BuyRate=float(BuyRate[0]['rate'])/100.0
                
            if SellRate is not  None and SellRate !=[]:
                SellRate=float(SellRate[0]['rate'])/100.0
                
            LockedRate = float(lst['rate'])
            currentRate = currency_dict[currency_pair]
            deliverydate = dateTostr(lst['delivery_date'])
            if buy_currency+buy_currency==currency_pair:
               LockedRate = 1.0/LockedRate
               currentRate = 1.0/currentRate
            forwarddict[lst['id']] = self.cumputeLost(SellRate,BuyRate,deliverydate,LockedRate,currentRate,sell_amount)
        self.forwarddict = forwarddict
            
                
    
    def getDataFromPostgres(self):
        
        
        Now = getNow('%Y-%m-%d')
  
        post = postgersql()
        colname = ['id','currency_pair','trade_date','delivery_date','rate','sell_currency','sell_amount','buy_currency','buy_currency']
        wherestring = """ delivery_date>='%s'"""%Now
       
        self.data = post.select(forward_option,colname,wherestring)
        
    def  cumputeLost(self,SellRate,BuyRate,deliverydate,LockedRate,currentRate,sell_amount):
       if SellRate in [None,[]] or BuyRate in [None,[]]:
           return None
       else:
           return sell_amount*OrdinaryForward(SellRate,BuyRate,deliverydate,LockedRate,currentRate)
      
        
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
        
        post.update(forward_option,updatelist,wherelist)
        post.close()