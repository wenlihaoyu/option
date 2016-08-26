# -*- coding: utf-8 -*-
"""
Created on Tue Aug 23 15:11:57 2016

@author: lywen
"""

def getmongo():
    """获取mongo配置"""
    user = 'mongo'
    password ='mongo'
    host='127.0.0.1'
    port=27017
    db='fes'
    return user,password,host,port,db
    