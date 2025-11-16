#***********************************************************
#  Copyright © 2019 StarTech. All rights reserved
#  Author: Fanliangde
#  Description: 量化指标计算函数包
#  History: 
#   1. Create Version1.0 on 2019/07/18
#   2. 
#  
#***********************************************************

import numpy as np
from EsSeries import NumericSeries


def U_Summation(data,period):
    '''
    【说明】
          求最近length周期的和

    【参数】
          data 计算参考序列，类型可为[],NumericSeries或者np.array
          period 周期数，整型

    【返回值】
          返回最近length周期的和，浮点型

    【备注】
          无
    '''
    index = len(data) - period if len(data) > period else 0
    return sum(data[index:])

def U_Average(data,period):
    '''
    【说明】
          求最近length周期的均值

    【参数】
          data 计算参考序列，类型可为[],NumericSeries或者np.array
          period 周期数，整型

    【返回值】
          返回最近length周期的均值，浮点型

    【备注】
          无
    '''
    period = 1 if period == 0 else period
    nBars =  min(len(data), period)
    
    return U_Summation(data, period) / nBars
    
def U_AverageFC(X, data, period):
    '''
    【说明】
          快速求最近length周期的均值

    【参数】
          X 所有length周期的均值, NumericSeries类型
          data 计算参考序列，类型可为[],NumericSeries或者np.array
          period 周期数，整型

    【返回值】
          返回最近length周期的均值，浮点型

    【备注】
          X = NumericSeries()
          X[-1] = XAverage(X, Close(), 10)
    '''
    nSum = 0
    nBars = 1
    dLen = len(data)
    
    if dLen <= 1:
        return data[-1]
    
    if dLen <= period:
        nSum = X[-1] * (dLen-1) + data[-1]
        nBars = dLen
    else:
        nSum = X[-1] * period + data[-1] - data[-period-1]
        nBars = period
    
    return nSum / nBars


def U_XAverage(X, data, period):
    '''
    【说明】
          求最近length周期的指数平均

    【参数】
          X 所有length周期的指数平均, NumericSeries类型
          data 计算参考序列，类型可为[],NumericSeries或者np.array
          period 周期数，整型

    【返回值】
          返回最近length周期的指数平均，浮点型

    【备注】
          X = NumericSeries()
          X[-1] = XAverage(X, Close(), 10)
    '''
    sFcactor = 2 / ( period + 1 )
    if len(data) == 1:
        retValue = data[-1]
    else:
        retValue = X[-1] + sFcactor * (data[-1] - X[-1])
    
    return retValue

def U_MA(data, period):
    '''
    【说明】
          求最近length周期的移动平均

    【参数】
          data 计算参考序列，类型可为[],NumericSeries或者np.array
          period 周期数，整型

    【返回值】
          返回最近length周期的移动平均值，浮点型

    【备注】
          无
    '''
    period = 1 if period == 0 else period
    
    return U_Summation(data, period) / period

def U_EMA(X, data, period):
    '''
    【说明】
          求最近length周期的指数平均

    【参数】
          X 所有length周期的指数平均, NumericSeries类型
          data 计算参考序列，类型可为[],NumericSeries或者np.array
          period 周期数，整型

    【返回值】
          返回最近length周期的指数平均值，浮点型

    【备注】
          X = NumericSeries()
          X[-1] = EMA(X, Close(), 10)
    '''
    return U_XAverage(X, data,period)

def U_SMA(X, data, period, weight=1):
    '''
    【说明】
          求最近length周期的移动平均

    【参数】
          X 所有length周期的指数平均, NumericSeries类型
          data 计算参考序列，类型可为[],NumericSeries或者np.array
          period 周期数，整型
          weight 权重

    【返回值】
          返回最近length周期的移动平均，浮点型

    【备注】
          X = NumericSeries()
          X[-1] = SMA(X, Close(), 10, 2)
    '''
    if period==0:
        return None
        
    if len(data) == 1:
        sMaValue = data[-1]
    else: 
        sMaValue = (X[-1]*(period-weight) + data[-1]*weight)/period
    return sMaValue
    
    
def U_Lowest(data, period=5):
    '''
    【说明】
          求最近length周期的最低值

    【参数】
          data 计算参考序列，类型可为[],NumericSeries或者np.array
          period 周期数，整型

    【返回值】
          返回最近length周期的最低值，浮点型

    【备注】
          无
    '''
    period = 1 if period == 0 else period
    index = len(data) - period if len(data) > period else 0
    return min(data[index:])
    
def U_Highest(data, period=5):
    '''
    【说明】
          求最近length周期的最高值

    【参数】
          data 计算参考序列，类型可为[],NumericSeries或者np.array
          period 周期数，整型

    【返回值】
          返回最近length周期的最高值，浮点型

    【备注】
          无
    '''
    period = 1 if period == 0 else period
    index = len(data) - period if len(data) > period else 0
    return max(data[index:])
    

def U_VAR(data,period):
    '''
    【说明】
          求标准方差

    【参数】
          data 计算参考序列，类型可为[],NumericSeries或者np.array
          period 周期数，整型

    【返回值】
          返回求指数平均后的值

    【备注】
          无
    '''
    index = len(data) - period if len(data) > period else 0
    return np.var(np.array(data[index:]))


def U_STD(data,period):
    '''
    【说明】
          求标准差

    【参数】
          data 计算参考序列，类型可为[],NumericSeries或者np.array
          period 周期数，整型

    【返回值】
          返回求指数平均后的值

    【备注】
          无
    '''
    index = len(data) - period if len(data) > period else 0
    return np.std(np.array(data[index:]))
