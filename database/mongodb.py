# -*- coding: utf-8 -*-
"""
Created on Tue Aug 23 15:09:26 2016
##从mongo获取相关数据
@author: lywen
"""
from database import mongodb## mongo connect
from help.help import getNow,strTostr,timedelta ##get current datetime


class RateExchange(object):
    """
    获取汇率实时行情数据
    """
    def __init__(self,code):
        
        self.__mongo = mongodb()
        
        self.code = code
        

    def getMax(self):
        """获取最大的实时汇率"""
        '''key={'code':True}
        
        Time = strTostr(getNow('%Y-%m-%d'))
        initial ={'Close':0,'Time':Time}
        reduces = """function(doc,prev){
 
                    if (prev.Time<doc.Time){
                          prev.Close = doc.Close/1.0/doc.PriceWeight;
                          prev.Time = doc.Time
                     }}"""##遍历寻找当前最大汇率值
        condition={'type':'0','code':self.code,'Time':{'$gte':Time}}             
        data =  self.__mongo.group('kline',key,condition,initial,reduces)
        self.__mongo.close()
        return data
        '''
        data = self.__mongo.select('kline_new',{'code':self.code,'type':'0'})
        if data ==[]:
            return []
        else:
           data = data[0]
           return [{'Close':data.get('Close')/1.0/data.get('PriceWeight')}]
        
    def getdayMax(self,Time=None):
        """
        获取某一天汇率最大值
        """
        key={'code':True}
        
        Time_end = strTostr(timedelta(Time,17.0/24))##当天时间下午5点
        Time = strTostr(Time)
        initial ={'Close':0,'Time':Time}
       
        reduces = """function(doc,prev){
 
                     if (prev.Time<doc.Time){
                          prev.Close = doc.Close/1.0/doc.PriceWeight;
                          prev.Time = doc.Time
                     }}"""##遍历寻找当前最大汇率值
        condition={'type':'0','code':self.code,'Time':{'$lt':Time_end,'$gte':Time}}             
        data =  self.__mongo.group('kline',key,condition,initial,reduces)
        self.__mongo.close()
        return data
        
     
        
        
    

class BankRate(object):
    """
    获取银行拆借利率
    """
    def __init__(self,code,ratetype):
        """
        code:货币
        ratetype:拆借利率期限
        """
        
        self.__mongo = mongodb()
        self.code = code
        self.ratetype = ratetype
        
        
        
    def getMax(self):
        """
        获取利率最大的日期对应的日期
        """
        key={'index':True}
        Time = strTostr(getNow('%Y'),'%Y')
        initial ={'rate':0,'datadate':Time}
        reduces = """function(doc,prev){
 
                     if (prev.datadate<doc.datadate){
                          prev.rate = doc.rate;
                          prev.datadate = doc.datadate
                     }}"""##遍历寻找当前最大汇率值
        ratetype ='12月'
        condition={'ratetype':ratetype,'index':self.code}      
        
        data = self.__mongo.group('KPI',key,condition,initial,reduces)
        self.__mongo.close()
        return data
        
