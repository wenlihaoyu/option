# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 17:56:36 2016
forwards
@author: lywen
"""
from job import option
from help.help import getNow,getRate,getcurrency,dateTostr
from config.postgres  import  table_comlong_term
from database.mongodb import  RateExchange
from database.mongodb import  BankRate
from database.database import postgersql
from numpy import float64
from main.forward     import OrdinaryForward
class forwards(option):
    """
    普通外汇远期定价
    """

    def __init__(self):
        option.__init__(self)
        self.table = table_comlong_term
        self.getDataFromPostgres()##从post提取数据
        print '期权类型','ID','货币对','成交日期','交割日','损益'

        self.getDataFromMongo()##从mongo提取数据并更新损益
        self.updateDataToPostgres()##更新数据到post
        
    def getDataFromMongo(self):
        """
        from mongo get the currency_pairs and bank_rate
         #卖出币种如果是人民币(CNY/CNH)，那么买入币种是本金，否则就是卖出币种
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
            ##跟改
            #sell_currency = lst['sell_currency']
            sell_currency = lst['currency_pair'][:3]
            sell_currency_index = getcurrency(sell_currency)
            
            #buy_currency  = lst['buy_currency']
            buy_currency = lst['currency_pair'][3:]
            buy_currency_index = getcurrency(buy_currency)
            
            currency_pair = lst['currency_pair']
            ratetype = getRate((lst['delivery_date'] -lst['trade_date']).days)
            SellRate = BankRate(sell_currency_index,ratetype).getMax()##卖出本币的利率
            BuyRate  = BankRate(buy_currency_index,ratetype).getMax()##买入货币的利率
            sell_amount = float64(lst['sell_amount'])
            buy_amount = float64(lst['buy_amount'])
            
            if BuyRate is not  None and BuyRate !=[]:
                BuyRate=float(BuyRate[0]['rate'])/100.0
                
            if SellRate is not  None and SellRate !=[]:
                SellRate=float(SellRate[0]['rate'])/100.0
                
            LockedRate = float(lst['rate'])
            currentRate = currency_dict[currency_pair]
            deliverydate = dateTostr(lst['delivery_date'])
            
           
            print 'forwards',lst['id'],currency_pair,dateTostr(lst['trade_date']),deliverydate,
            forwarddict[lst['id']] = self.cumputeLost(SellRate,BuyRate,deliverydate,LockedRate,currentRate)
             #卖出币种如果是人民币，那么买入币种是本金，否则就是卖出币种            
            print forwarddict[lst['id']]
            print '\n'
            if forwarddict[lst['id']] is not None:
                if lst['sell_currency']=='CNY' or lst['sell_currency']=='CNH':
                    
                    forwarddict[lst['id']] =forwarddict[lst['id']]*buy_amount 
                else:
                    forwarddict[lst['id']] =forwarddict[lst['id']]*sell_amount
            
            
            #if sell_currency+buy_currency!=currency_pair:
            #    forwarddict[lst['id']] =forwarddict[lst['id']]/currentRate
        self.forwarddict = forwarddict
            
                
    
    def getDataFromPostgres(self):
        
        
        Now = getNow('%Y-%m-%d')
  
        post = postgersql()
        colname = ['id','trade_id','currency_pair','trade_date','delivery_date','rate','sell_currency','sell_amount','buy_currency','buy_amount']
        wherestring = """ delivery_date>='%s'"""%Now
       
        self.data = post.select(self.table ,colname,wherestring)
        
    def  cumputeLost(self,SellRate,BuyRate,deliverydate,LockedRate,currentRate):
       if SellRate in [None,[]] or BuyRate in [None,[]]:
           return None
       else:
           return OrdinaryForward(SellRate,BuyRate,deliverydate,LockedRate,currentRate)
      
        
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
