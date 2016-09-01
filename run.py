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
if '__main__'==__name__:
    #fd = participateforwards(0.1)
    for items in [participateforwards,CollaOptions,knockoptions,forwards,SwapOptions]:
        items()