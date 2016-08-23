# -*- coding: utf-8 -*-
"""
Created on Tue Aug 23 11:51:41 2016
数据库基本操作，从配置文件中读取基本配置信息
@author: lywen
"""


import traceback
from config.mongoconfig import getmongo
class database(object):
    """
    数据库操作抽象类
    """
    def __init__(self,db,user,password,host,port):
        self.db = db## 数据库实例
        self.user = user ## 用户
        self.password = password ##密码
        self.host = host ##数据库IP
        self.port = port ## 数据库端口
        
    def connect(self):
        """
        数据库连接
        """
        pass
        
    def update(self,sql):
        """
        数据update更新操作
        """
        pass
    
    def insert(self,sql):
        """
        数据插入操作
        """
        pass
        
    def create(self,tablename):
        """
        创建表
        """
        pass
    
    def select(self,sql):
        """
         数据查询
        """
        pass
    
    def run(self):
        """
        运行
        """
        pass
    
    def close(self):
        """
        关闭连接
        """
        pass
    
   
   
class mongodb(database):
    """
    mongo数据库相关操作
    """
    def __init__(self):
        user,password,host,port,db = getmongo()
        database.__init__(self,db,user,password,host,port)##继承父类的__init__方法
        self.connect()
        
    def connect(self):
        """
        连接mongo数据库
        """
        from pymongo import MongoClient
        try:
            self.Client = MongoClient(host=self.host, port=self.port)
            
            db = self.Client[self.db]
            if self.host !='127.0.0.1':
               db.authenticate(name=self.user,password=self.password)
            self.__conn = db
        except:
            traceback.print_exc()
            #logs('database','mongodb','connect',traceback.format_exc())
            self.__conn = None


    def select(self,collectname,where):
        """
        collectname：数据库文档名称
        where:{'a':1}
        """
        collection = self.__conn[collectname]
        return collection.find(where)
        
    def group(self,collectname,key, condition, initial, reduce, finalize=None, **kwargs):
        """
        group function
        """
        collection = self.__conn[collectname]
        try:
            return collection.group(key, condition, initial, reduce)
        except:
            traceback.print_exc()
        
        
                   
    def close(self):
        """
        关闭连接
        """
        self.__conn.client.close()
        
    

   
class postgersql(database):
    """
    postgersql数据库相关操作
    """
    def __init__(self,db,user,password,host,port):
        database.__init__(self,db,user,password,host,port)
        
    def connect(self):
        """
        连接数据库，连接失败返回错误日志
        """
        import psycopg2
        try:
           conn = psycopg2.connect(database=self.database, user=self.user, password=self.password, host=self.host, port=self.port)
           conn.autocommit =True##自动提交
           self.conn = conn
        except:
           #logs('database','postgersql','connect',traceback.format_exc())
           self.conn = None
    

    def select(self,tablename,wherelist):
        self.conn
        
    
        

