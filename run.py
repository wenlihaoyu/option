# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29 16:36:54 2016

@author: lywen
"""

from price.participateforwards import participateforwards
from price.collaoptions import CollaOptions
from price.knockoptions import knockoptions
from price.forwards import forwards
from price.swapoption import SwapOptions
from price.targetforwards import TargetRedemptionForwards
from help.help import getNow,strTodate
import pandas as pd

if '__main__'==__name__:
    #fd = participateforwards(0.1)
    #for items in [participateforwards,CollaOptions,knockoptions,forwards,SwapOptions]:
    #    items()
    Now = getNow()
    Now = strTodate(Now,'%Y-%m-%d %H:%M:%S')
    trf = TargetRedemptionForwards(Now)
    print pd.DataFrame(trf.cumputeLost())