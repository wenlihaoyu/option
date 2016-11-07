# -*- coding: utf-8 -*-
"""
Created on Tue Aug 23 15:19:44 2016
help file
@author: lywen
"""
import datetime as dt

def getNow(format='%Y-%m-%d %H:%M:%S'):
    now = dt.datetime.now()
    try:
       return now.strftime(format)
    except:
        return None
       
       
       
def strTodate(s,formats='%Y-%m-%d'):
    try:
        return dt.datetime.strptime(s,formats)
    except:
        return None
       
def dateTostr(s,formats='%Y-%m-%d'):
    try:
        return dt.datetime.strftime(s,formats)
    except:
        return None
        
def strTostr(s,format1='%Y-%m-%d',format2='%Y-%m-%d %H:%M:%S'):
    try:
        return dt.datetime.strptime(s,format1).strftime(format2)
    except:
        return None
        
def timedelta(s,day,format='%Y-%m-%d'):
   try:
      return (dt.datetime.strptime(s,format)+dt.timedelta(day)).strftime(format)
   except:
       return None
        
        
def getColname(tablename):
            """
            获取表的字段
            """
            sql = """SELECT attname
                 FROM
                       pg_attribute
                       INNER JOIN pg_class  ON pg_attribute.attrelid = pg_class.oid
                       INNER JOIN pg_type   ON pg_attribute.atttypid = pg_type.oid
                       LEFT OUTER JOIN pg_attrdef ON pg_attrdef.adrelid = pg_class.oid AND pg_attrdef.adnum = pg_attribute.attnum
                       LEFT OUTER JOIN pg_description ON pg_description.objoid = pg_class.oid AND pg_description.objsubid = pg_attribute.attnum
                 WHERE
                       pg_attribute.attnum > 0
                      AND attisdropped <> 't'
                       AND pg_class.relname= '%s'  
                 ORDER BY pg_attribute.attnum ;"""%tablename
            return sql
     
def dictTostr(D):
    """
    example:
    D=[{'a':1,'b':3},{'c':1,'d':3}]
    
    return:
       ['a =1 and b=3','c =1 and b=3']
    """
    tmp=[]
    for item in D.items():
            s = u"""%s="""%item[0]
            if type(item[1]) is  str or type(item[1]) is  unicode:
                s+=u"""'%s'"""%item[1]
            else:
                s+=u"""%s"""%item[1]
            tmp.append(s)
             
    return  ' and '.join(tmp)
    
    
def getRate(days):
    """
    输入剩余天数，返回合适的拆借利率
    """
    if days<7:
        return '隔夜'
    elif days<14:
        return '1周'
    elif days < 30:
        return '2周'
    elif days<60:
        return '1月'
    elif days<90:
        return '2月'
    elif days<120:
        return '3月'   
    elif days<150:
        return '4月'    
        
    elif days<180:
        return '5月'
        
    elif days<210:
        return '6月'
    elif days<240:
        return '7月'
    elif days<270:
        return '8月'
    elif days<300:
        return '9月'
    elif days<330:
        return '10月'
    elif days<360:
        return '11月'
    elif days>=360:
        return '1年'
    else:
        return '隔夜(O/N)'
        
    
def getcurrency(code):
    """
    根据货币代码回去对应的拆借利率名称
    """        
    if code=='CNY' or code=='CNH':
        return "Shibor人民币"

    elif code=='USD':
        return "Libor美元"
        
    elif code=='GBP':
        return "Libor英镑"
        
    elif code=='JPY':
        return "Libor日元"
        
    elif code=='EUR':
        return "Euribor欧元"
            
    elif code=='AUD':
        return '澳大利亚元'
    
    elif code=='CAD':
        return '加拿大元'
        
    elif code=='JPY':
        return 'Libor日元'
    
def interestway(interest_pay_way,charge_float_libor):
    """
    interest_pay_way:利息支付方式
    charge_float_libor:支付浮动利率方式
    """       
    if interest_pay_way is None:
        return None
    
    elif interest_pay_way=='按月支付':
        return '1月'
    elif interest_pay_way=='按季支付':
        return '3月'
    elif interest_pay_way=='到期一次付息' or interest_pay_way=='提前支付'  :
        if charge_float_libor is None:
            return None
        elif charge_float_libor.lower()=='1mlibor':
            return '1月'
        elif charge_float_libor.lower()=='3mlibor':
            return '3月'
    
    return None
    
from database.mongodb import BankRate
def getbankrate(currency,valuedate,deliverdate,interest_pay_way,charge_float_libor):
    """
    currency:货币代码
    valuedate:起息日期
    deliverdate:成交日期
    interest_pay_way:利息支付方式
    """
    currencyIndex =getcurrency(currency)
    if interest_pay_way=='按月支付':
        days = 30
    elif interest_pay_way=='按季支付':
        days = 90
        
    Now = getNow('%Y-%m-%d')
    t = valuedate
    ratetype = interestway(interest_pay_way, charge_float_libor)
    ##确定付息时间
    dateDict = {}
    while t<=deliverdate:
          t = timedelta(t,days)
          if timedelta(t,-days)> Now:##未来拆借利率取当前时间最新的拆借利率
             r = dateDict.get(timedelta(t,-days))
          else:
              
              br =  BankRate(code = currencyIndex, ratetype=ratetype)
              if t>deliverdate:
                  r  = br.getday(deliverdate)
                  #dateDict[deliverdate] = br.getday(deliverdate)
             
              else:
                  r  = br.getday(t)
                  #dateDict[t] = br.getday(t)
          dateDict[deliverdate if t>deliverdate else t] = r 
    return dateDict
          
          
             
##获取汇率对应的汇率
from database.mongodb import  RateExchange             
def getcurrentrate(currencyPairs):
        currency_dict = {}
        for currency_pair in currencyPairs:
            RE = RateExchange(currency_pair).getMax()
            if RE is not None and RE !=[]:
               currency_dict[currency_pair] = RE[0]['Close']
        return currency_dict
        
##获取银行拆借利率
def getcurrentbankrate(sell_currency,buy_currency,ratetype):
   
    sell_currency_index = getcurrency(sell_currency)
            
           
    
    buy_currency_index = getcurrency(buy_currency)
            
            
            
    SellRate = BankRate(sell_currency_index,ratetype).getMax()##卖出本币的利率
    BuyRate  = BankRate(buy_currency_index,ratetype).getMax()##买入货币的利率
    if BuyRate is not  None and BuyRate !=[]:
                BuyRate=float(BuyRate[0]['rate'])/100.0
    else:
        BuyRate=0.0
                
    if SellRate is not  None and SellRate !=[]:
                SellRate=float(SellRate[0]['rate'])/100.0 
    else:
        SellRate=0.0
    return SellRate,BuyRate
    
from numpy import float64         
def chooselocalmoney(lst,lost):
    """
    判断本金货币及本金损益
    lost:损益
    """
    ##计算损益比例
    if lst['sell_currency']+lst['buy_currency']==lst['currency_pair']:
        lost = -lost
            
    ##判断本金                
    ##如果是购汇交易，那么本金就是买入金额；如果是结汇交易，那么本金就是卖出金额；如果是互换交易，那么本金就是非美元币种；
    ## localmoney 本金
    ##    type =1,2,3-> 购汇, 结汇,互换 
    if lst['type']==u'1':
                 localmoney = float64(lst.get('buy_amout')) 
    elif     lst['type']==u'2':
                localmoney = float64(lst.get('sell_amount'))
    elif lst['type']==u'3':
          if lst['sell_currency']=='USD':
                    localmoney = float64(lst.get('buy_amout'))
                    
          else:
                    localmoney = float64(lst.get('sell_amount'))
    else:
        localmoney = None ##其他交易类型，暂时无法计算
    if localmoney and localmoney.__str__() !='nan' :
        return lost * localmoney ##本金损益
    else:
        return None
        
     