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
    if code=='CNY':
        return "shibor人民币"
        
    elif code=='EUR':
        return "libor欧元"
        
    elif code=='USD':
        return "libor美元"
        
    elif code=='GBP':
        return "libor英镑"
        
    elif code=='JPY':
        return "libor日元"
        
    elif code=='EUR':
        
        return "euribor欧元"
    
        
    elif code=='AUD':
        return None
    
    elif code=='CAD':
        return None
        
     