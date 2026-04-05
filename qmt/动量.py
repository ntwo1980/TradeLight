#encoding:gbk
import datetime
import time
import pandas as pd
import numpy as np
import talib
import json
import os

"""
Strategy Description: 全天候动量A
"""

class a():
    pass

universe = a()
with open('Strategy.py', "r", encoding="utf-8") as f:
    exec(f.read(), globals())  # 注入全局

a = MomentumRotationStrategy(
    universe = universe,
    stocks=['518880.SH', '513100.SH', '159915.SZ', "513120.SH", "513020.SH"],
    stockNames=['黄金ETF', '纳指100', '创业板', '港股创新药', '港股科技'],
    #days = 26,  # 95023
    #days = 27,  # 118554
    days = 28,  # 133602
    #days = 29,  # 129755
    #days = 30,  # 95153
    #days = 31,  # 109607
    #days = 32,  # 100259
    #days = 33,  # 90677
    rank = 1,
    get_trade_detail_data_func = get_trade_detail_data,
    pass_order_func = passorder,
    cancel_func = cancel,
    timetag_to_datetime_func = timetag_to_datetime,
    download_history_data_func = download_history_data)

def init(C):
    if not C.do_back_test:
        a.SetAccount(account, accountType)

    a.init(C)

    if not a.IsBacktest:
        C.run_time("f","1nDay","2019-10-14 09:31:00")
        C.run_time("f","1nDay","2019-10-14 09:32:00")

def handlebar(C):
    if a.IsBacktest:
        a.f(C)

def f(C):
    a.f(C)

def g(C):
    a.g(C)
