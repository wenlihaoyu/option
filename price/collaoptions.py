# -*- coding: utf-8 -*-
"""
Created on Tue Aug 30 09:17:50 2016
CollaOption 领式期权计算
@author: lywen
"""


from job import option
from help.help import getNow,getRate,dateTostr
from help.help import getcurrentrate,getcurrentbankrate
from help.help import chooselocalmoney##本金损益
from config.postgres  import  table_collars_option##table name

from database.mongodb import  RateExchange
#from database.mongodb import  BankRate
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
        print '期权类型','ID','货币对','成交日期','交割日','损益'
        self.getDataFromMongo()
        self.updateDataToPostgres()
        
        
    def getDataFromMongo(self):
        """
        from mongo get the currency_pairs and bank_rate
        """
        ## currency_pairs
        currency_pairs = list(set(map(lambda x:x['currency_pair'],self.data)))
        currency_dict = getcurrentrate(currency_pairs)
        
        
        ##bank_rate
        forwarddict= {}
        for lst in self.data:
            
           
            sell_currency = lst['currency_pair'][:3]
            buy_currency  = lst['currency_pair'][3:]
            currency_pair = lst['currency_pair']
            ratetype = getRate((lst['delivery_date'] -lst['trade_date']).days)
            
            
            SellRate,BuyRate = getcurrentbankrate(sell_currency,buy_currency,ratetype)
            
            
            #sell_amount = float64(lst['sell_amount'])
            #buy_amount  = float64(lst['buy_amount'])
            ##获取厘定日的汇率，如果还未到厘定日，那么汇率返回None
            Setdate = dateTostr(lst['determined_date'])##厘定日
            SetRate = RateExchange(currency_pair).getdayMax(Setdate)##厘定日汇率
            
            if SetRate ==[]:
                SetRate = None## 还未到厘定日
     
            ## 执行汇率上下限
            strikeLowerRate = float64(lst['exe_doexrate'])
            strikeUpperRate = float64(lst['exe_upexrate'])
      
            currentRate = currency_dict.get(currency_pair)
            if currentRate is None:
                print "{ } not Fund!\n".format(currency_pair)
                continue
            
            deliverydate = dateTostr(lst['delivery_date'])
            
            print 'CollaOptions',lst['id'],currency_pair,dateTostr(lst['trade_date']),deliverydate,
            forwarddict[lst['id']] = self.cumputeLost(Setdate,SetRate,deliverydate,strikeLowerRate,strikeUpperRate,currentRate,SellRate,BuyRate,self.delta)
            
            
            if forwarddict[lst['id']] is not  None:
                
                
                 ## 计算本金损益
                  forwarddict[lst['id']] = chooselocalmoney(lst,forwarddict[lst['id']])  
            print forwarddict[lst['id']]
            print '\n'
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
                    'buy_amount',
                    'trade_date',
                    'determined_date',
                    'delivery_date',
                    'exe_doexrate',
                    'exe_upexrate',
                    'type'
                    ]
        wherestring = """ delivery_date>='{}' and trade_date<='{}'""".format(Now,Now)
       
        self.data = post.select(self.table,colname,wherestring)
        
    def  cumputeLost(self,Setdate,SetRate,deliverydate,strikeLowerRate,strikeUpperRate,currentRate,SellRate,BuyRate,delta):
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