# -*- coding: utf-8 -*-
"""
Created on Thu Sep  1 15:02:50 2016
participateforward 价值计算
@author: lywen
"""

from job import option
from help.help import getNow,getRate,getcurrency,dateTostr
from config.postgres  import  table_participate_forward
from database.mongodb import  RateExchange
from database.mongodb import  BankRate
from database.database import postgersql
from numpy import float64
from main.participateforward import  participateforward

class participateforwards(option):
    """
    参与式远期
    """

    def __init__(self,delta=0.1):
        option.__init__(self)
        self.table = table_participate_forward
        self.delta  =delta
        self.getDataFromPostgres()##从post提取数据
        print '期权类型','ID','货币对','成交日期','交割日','损益'
        self.getDataFromMongo()##从mongo提取数据并更新损益
        self.updateDataToPostgres()##更新数据到post
        
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
               currency_dict[currency_pair] = RE[0]['Close']##获取最新汇率
        self.currency_dict = currency_dict
        
        ##bank_rate
        forwarddict= {}
        for lst in self.data:
            #sell_currency = lst['sell_currency']##卖出货币代码
            sell_currency = lst['currency_pair'][:3]##卖出货币代码
            sell_currency_index = getcurrency(sell_currency)
            
            #buy_currency  = lst['buy_currency']##买入货币代码
            buy_currency = lst['currency_pair'][3:]##买入货币代码
            buy_currency_index = getcurrency(buy_currency)
            
            currency_pair = lst['currency_pair']
            ratetype = getRate((lst['delivery_date'] -lst['trade_date']).days)
            SellRate = BankRate(sell_currency_index,ratetype).getMax()##获取卖出本币的拆借利率
            BuyRate  = BankRate(buy_currency_index,ratetype).getMax()##买入货币的拆借利率
            sell_amount = float64(lst['sell_amount'])
            buy_amount = float64(lst['buy_amount'])
            Setdate = dateTostr(lst['determined_date'])
            SetRate = RateExchange(currency_pair).getdayMax(Setdate)##获取厘定日汇率
            
            if BuyRate is not  None and BuyRate !=[]:
                BuyRate=float(BuyRate[0]['rate'])/100.0
                
            if SellRate is not  None and SellRate !=[]:
                SellRate=float(SellRate[0]['rate'])/100.0
                
            LockedRate = float(lst['rate'])##锁定汇率
            currentRate = currency_dict[currency_pair]##实时汇率
            deliverydate = dateTostr(lst['delivery_date'])##日期转化为字符串
            print 'participateforwards',lst['id'],currency_pair,dateTostr(lst['trade_date']),deliverydate,
            forwarddict[lst['id']] = self.cumputeLost(Setdate,SetRate,deliverydate,currentRate,LockedRate,SellRate,BuyRate,self.delta)
            print forwarddict[lst['id']]
            print '\n'
            if forwarddict[lst['id']] is not None:
                
            
                if lst['sell_currency']=='CNY' or lst['sell_currency']=='CNH':
                    
                    forwarddict[lst['id']] =forwarddict[lst['id']]*buy_amount
                else:
                    forwarddict[lst['id']] =forwarddict[lst['id']]*sell_amount 
                
        self.forwarddict = forwarddict
        
          
                
    
    def getDataFromPostgres(self):
        
        
        Now = getNow('%Y-%m-%d')
  
        post = postgersql()
        colname = [
                'id',
                'trade_id',
               'currency_pair',
               'sell_currency',
               'buy_currency',
               'sell_amount',
               'buy_amount',
               'trade_date',
               'determined_date',
               'delivery_date',
               'rate'
                ]
        wherestring = """ delivery_date>='%s'"""%Now
       
        self.data = post.select(self.table,colname,wherestring)
        
    def  cumputeLost(self,Setdate,SetRate,deliverydate,currentRate,LockedRate,SellRate,BuyRate,delta  ):
       if SellRate in [None,[]] or BuyRate in [None,[]]:
           return None
       else:
           ##return sell_amount*participateforward(Setdate,SetRate,deliverydate,currentRate,LockedRate,SellRate,BuyRate,delta)
           return participateforward(Setdate,SetRate,deliverydate,currentRate,LockedRate,SellRate,BuyRate,delta)
        
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