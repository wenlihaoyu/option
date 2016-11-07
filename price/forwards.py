# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 17:56:36 2016
forwards
@author: lywen
修改本金计算逻辑 
"""
from job import option
from help.help import getNow,getRate,dateTostr
from help.help import getcurrentrate,getcurrentbankrate
from help.help import chooselocalmoney ##计算本金损益
from config.postgres  import  table_comlong_term
#from database.mongodb import  RateExchange
from database.database import postgersql
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
        ##--------------------获取汇率对的实时汇率
        currency_pairs = list(set(map(lambda x:x['currency_pair'],self.data)))
       
        currency_dict = getcurrentrate(currency_pairs)
        ##--------------------获取汇率对的实时汇率
        
        
        forwarddict= {}
        for lst in self.data:
            ##
            
            sell_currency = lst['currency_pair'][:3]
            buy_currency  = lst['currency_pair'][3:]
            currency_pair = lst['currency_pair']
            ratetype = getRate((lst['delivery_date'] -lst['trade_date']).days)
            
            
            SellRate,BuyRate = getcurrentbankrate(sell_currency,buy_currency,ratetype)##获取银行拆借利率
              
            LockedRate   = float(lst['rate'])##锁定汇率
            
            currentRate  = currency_dict.get(currency_pair)##即期实时汇率
            if currentRate is None:
                print "{} not fund!\n".format(currency_pair)
                continue
            
            deliverydate = dateTostr(lst['delivery_date'])##交割日期
            
           
            print 'forwards',lst['id'],currency_pair,dateTostr(lst['trade_date']),deliverydate,

            forwarddict[lst['id']] = self.cumputeLost(SellRate,BuyRate,deliverydate,LockedRate,currentRate)
             
            
            ## 计算本金损益
            if forwarddict[lst['id']] is not  None:
                forwarddict[lst['id']] = chooselocalmoney(lst,forwarddict[lst['id']])
            
            print forwarddict[lst['id']]
            print '\n'
            
            
            
        self.forwarddict = forwarddict
            
                
    
    def getDataFromPostgres(self):
        
        
        Now = getNow('%Y-%m-%d')
  
        post = postgersql()
        colname = ['id','trade_id','currency_pair','trade_date','delivery_date','rate','sell_currency','sell_amount','buy_currency','buy_amount','type']
        wherestring = """ delivery_date>='{}' and trade_date<='{}'""".format(Now,Now)
       
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
