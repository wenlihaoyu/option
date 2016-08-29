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
     
