# -*- coding: utf-8 -*-
"""
Created on Thu Sep  1 15:49:35 2016
敲出式期权
@author: lywen
"""


from job import option
from help.help import getNow,getRate,getcurrency,dateTostr
from config.postgres  import  table_knock_option
from database.mongodb import  RateExchange
from database.mongodb import  BankRate
from database.database import postgersql
from numpy import float64
from main.knockoption import  knockoption

class knockoptions(option):
    """
    敲出式期权
    """

    def __init__(self,delta=0.1):
        option.__init__(self)
        self.table = table_knock_option
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
               currency_dict[currency_pair] = RE[0]['Close']
        self.currency_dict = currency_dict
        
        ##bank_rate
        forwarddict= {}
        for lst in self.data:
            
            sell_currency = lst['currency_pair'][:3]##卖出货币代码
            sell_currency_index = getcurrency(sell_currency)
            
            
            buy_currency = lst['currency_pair'][3:]##买入货币代码
            
            buy_currency_index = getcurrency(buy_currency)
            
            currency_pair = lst['currency_pair']
            ratetype = getRate((lst['delivery_date'] -lst['trade_date']).days)
            SellRate = BankRate(sell_currency_index,ratetype).getMax()##卖出本币的利率
            BuyRate  = BankRate(buy_currency_index,ratetype).getMax()##买入货币的利率
            sell_amount = float64(lst['sell_amount'])
            buy_amount = float64(lst['buy_amount'])
            Setdate = dateTostr(lst['determined_date'])
            SetRate = RateExchange(currency_pair).getdayMax(Setdate)##厘定日汇率
            kncockRate = float64(lst['knockout_exrate'] )##敲出汇率
            
            if BuyRate is not  None and BuyRate !=[]:
                BuyRate=float(BuyRate[0]['rate'])/100.0
                
            if SellRate is not  None and SellRate !=[]:
                SellRate=float(SellRate[0]['rate'])/100.0
                
            LockedRate = float(lst['rate'])
            currentRate = currency_dict[currency_pair]
            deliverydate = dateTostr(lst['delivery_date'])
            print 'knockoptions',lst['id'],currency_pair,dateTostr(lst['trade_date']),deliverydate,
            forwarddict[lst['id']] = self.cumputeLost(Setdate,SetRate,deliverydate,currentRate,LockedRate,kncockRate,SellRate,BuyRate,self.delta)
            
            print forwarddict[lst['id']]
            print '\n'
            
           
            if forwarddict[lst['id']] is not None:
                
             
                if lst['sell_currency']=='CNY' or lst['sell_currency']=='CNH':
                    
                    forwarddict[lst['id']] =forwarddict[lst['id']]*buy_amount 
                else:
                    forwarddict[lst['id']] =forwarddict[lst['id']]*sell_amount 
                
            #if sell_currency+buy_currency!=currency_pair:
            #    forwarddict[lst['id']] = forwarddict[lst['id']]/currentRate
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
               'rate',
               'knockout_exrate'
                ]
        wherestring = """ delivery_date>='%s'"""%Now
       
        self.data = post.select(self.table,colname,wherestring)
        
    def  cumputeLost(self,Setdate,SetRate,deliverydate,currentRate,LockedRate,kncockRate,SellRate,BuyRate,delta  ):
       if SellRate in [None,[]] or BuyRate in [None,[]]:
           return None
       else:
           return knockoption(Setdate,SetRate,deliverydate,currentRate,LockedRate,kncockRate,SellRate,BuyRate,delta)
      
        
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