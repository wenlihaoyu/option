# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 16:36:54 2016

@author: lywen
"""

from price.participateforwards import participateforwards##参与式远期
from price.collaoptions import CollaOptions##领式期权
from price.knockoptions import knockoptions##敲出式期权
from price.forwards import forwards##普通外汇远期
from price.swapoption import SwapOptions## 区间式货币掉期or货币互换or封顶式期权
from price.targetforwards import TargetRedemptionForwards##目标可赎回式远期


if '__main__'==__name__:
    #fd = participateforwards(0.1)
    for items in [participateforwards,CollaOptions,knockoptions,forwards,SwapOptions,TargetRedemptionForwards]:
        items()
    