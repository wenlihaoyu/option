# -*- coding: utf-8 -*-
"""
Created on Tue Aug 30 13:49:09 2016
swapoption 定价
@author: lywen
"""

from job import option
from help.help import getNow,dateTostr,getcurrency,getbankrate
from config.postgres   import  table_swaps_option##table name
from database.mongodb  import  RateExchange
from database.mongodb  import  BankRate
from database.database import postgersql
from numpy import float64,array
from help.help import interestway ##利息支付方式

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
        print '期权类型','ID','货币对','计息方式', '交易类型','起息日','交割日','支付固定利率比例','收取浮动利率比例','获得固定补贴比例','损益'
        self.getDataFromMongo()
        self.updateDataToPostgres()
        
        
    def getDataFromMongo(self):
        """
        from mongo get the currency_pairs and bank_rate
        """
        ## currency_pairs
        currency_pairs = list(set(map(lambda x:x['currency_pair'],self.data)))
        currency_dict = {}
        ## 获取最新的实时汇率
        for currency_pair in currency_pairs:
            RE = RateExchange(currency_pair).getMax()
            if RE is not None and RE !=[]:
               currency_dict[currency_pair] = RE[0]['Close']
        self.currency_dict = currency_dict
        
        ##bank_rate
        forwarddict= {}
        for lst in self.data:
            
            ##交易本币与外币
            ##支付固定利率
            #print '计算订单{}\n'.format(lst)
            payFixRate = None if lst['pay_fix_rate'] is None else float64(lst['pay_fix_rate']) ##支付固定利率
            chargeFixRate  =  None if lst['charge_fix_rate'] is None else  float64(lst['charge_fix_rate'])##收取浮动利息固定部分
            value_date = dateTostr(lst['value_date'])
            delivery_date = dateTostr(lst['delivery_date'])
            if lst['interest_pay_way'] == '到期一次付息':
                br = BankRate(lst['buy_currency'],interestway(lst['interest_pay_way'],lst['charge_float_libor']))
                
                date = {dateTostr(lst['delivery_date']):br.getday(delivery_date)}
            elif lst['interest_pay_way']== '提前支付' or lst['trade_type']=='4':
                br = BankRate(lst['buy_currency'],interestway(lst['interest_pay_way'],lst['charge_float_libor']))
                
                date = {dateTostr(lst['delivery_date']):br.getday(value_date)}
            else:
                date = getbankrate(lst['buy_currency'],value_date,delivery_date,lst['interest_pay_way'],lst['charge_float_libor'])
            #payFixRateDict = {}              
            if  chargeFixRate is not None:
                for t in date:
                    date[t] = date[t]/100.0+chargeFixRate##货币浮动利率及支付利息时间
                   
            Fix = array(sorted(date.items(),key=lambda x:x[0]))
            FixDate = Fix[:,0]
            FixRate =  Fix[:,1][:]
            FixRate = FixRate.astype(float64)
            Rate = (FixDate,payFixRate,FixRate)##利息支付日期，支付卖出货币利息，收取浮动利率利息
            
            
       
            currency_pair = lst['currency_pair']
            
            ##货币对之间本币与外币
            sellCurrency  = currency_pair[:3]
            buyCurrency  = currency_pair[3:]
            buyIndex = getcurrency(buyCurrency)##拆借利率类型
            sellIndex = getcurrency(sellCurrency)##拆借利率类型
            SellRate = BankRate(sellIndex, '12月').getMax()##卖出本币的利率
            if SellRate!=[]:
                SellRate = SellRate[0]['rate']/100.0
            else:
                SellRate=0.0
            
                
            BuyRate  = BankRate(buyIndex, '12月').getMax()##买入货币的利率
            if BuyRate!=[]:
                BuyRate = BuyRate[0]['rate']/100.0
            else:
                BuyRate=0.0
                
            LockedRate = float64(lst['exe_exrate'])##执行汇率
            capped_exrate  = None if lst['capped_exrate'] is None else float64(lst['capped_exrate']) ##封顶汇率
            ##获取厘定日汇率
            ##获取厘定日的汇率，如果还未到厘定日，那么汇率返回None
            Setdate = dateTostr(lst['determined_date'])##厘定日
            SetRate = RateExchange(currency_pair).getdayMax(Setdate)##厘定日汇率
            
            if SetRate ==[]:
                SetRate = None## 还未到厘定日
            
            currentRate = currency_dict[currency_pair] ## 实时汇率
            #deliverydate = dateTostr(lst['delivery_date'])## 交割日期
            trade_type = lst['trade_type']##交易类型
            rateway = lst['interest_pay_way']##利息支付方式
            sell_amount  = float64(lst['sell_amount'])
            buy_amount  = float64(lst['buy_amount'])
            print 'SwapOptions', lst['id'],currency_pair,rateway,trade_type,value_date,delivery_date,
            forwarddict[lst['id']] = self.cumputeLost(Setdate,SetRate,value_date,delivery_date,currentRate,SellRate,BuyRate,LockedRate,rateway,self.delta,capped_exrate,trade_type,Rate)
            #if sell_currency+buy_currency !=currency_pair:
            #    forwarddict[lst['id']] = forwarddict[lst['id']]/currentRate
            print forwarddict[lst['id']]
            print '\n'
            if forwarddict[lst['id']] is not  None:
                
             
                if lst['sell_currency']=='CNY' or lst['sell_currency']=='CNH':
                    
                    forwarddict[lst['id']] =forwarddict[lst['id']]*buy_amount     
                else:
                    forwarddict[lst['id']] =forwarddict[lst['id']]*sell_amount
                
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
                   'buy_amount',
                   'exe_exrate',
                   'capped_exrate',
                   'pay_fix_rate',##支付固定利率
                   'charge_fix_rate',##收取固定利率固定部分
                   'interest_pay_way',##付息方式
                   'charge_float_libor',##收取固定利率浮动部分
                   'trade_type'##交易类型
                   ]
        wherestring = """ delivery_date>='%s'"""%Now
       
        self.data = post.select(self.table,colname,wherestring)
        
    def  cumputeLost(self,Setdate,SetRate,valuedate,deliverydate,currentRate,SellRate,BuyRate,LockedRate,rateway,delta,capped_exrate,trade_type,FixRate):
       if SellRate in [None,[]] or BuyRate in [None,[]]:
           return None
       else:
           return SwapOption(Setdate,SetRate,valuedate,deliverydate,currentRate,SellRate,BuyRate,LockedRate,rateway,delta,capped_exrate,trade_type,FixRate)
      
        
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

