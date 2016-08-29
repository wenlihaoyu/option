# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 13:29:50 2016
main
@author: lywen
"""


class option(object):
    """
    产品定价
    """
    def __init__(self):
        pass
    
    def getDataFromMongo(self):
        """
        从mongo获取拆借利率及实时汇率
        """
        pass
    
    def getDataFromPostgres(self):
        """
        从postgres获取结构产品数据
        """
        pass

    def cumputeLost(self):
        """
        计算结果行产品数据的损益
        """
        pass
    
    def updateDataToPostgres(self):
        """
        将计算的损益更新到数据库
        """
        pass
    


