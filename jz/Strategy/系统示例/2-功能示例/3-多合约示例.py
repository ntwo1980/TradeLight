########################系统示例不支持修改########################
# 多合约示例
# 备注：订阅多个合约的K线数据时，仅基准合约的数据会触发handle_data,其他合约
# K线数据仅更新本地数据，不触发
##################################################################
import talib as ta
import numpy as np

code1 = 'ZCE|Z|FG|MAIN'
code2 = 'ZCE|Z|SA|MAIN'
arr1 = np.array([])
arr2 = np.array([])

# 移动平均线
def iMA(arr:np.array, length=10, pos=0):
    s = 0.0

    if len(arr) - pos < length:
        return -1, s

    for i in range(pos, pos+length):
        rindex = i+1
        s = s + arr[-rindex]

    return 0, s/length

def initialize(context): 
    global code1
    global code2
    # 订阅玻璃主力
    SetBarInterval(code1, Enum_Period_Day(), 1, 500)
    # 订阅纯碱主力
    SetBarInterval(code2, Enum_Period_Day(), 1, 500)

def handle_data(context):
    #计算MA  
    if len(Close())<10:
        return
    Ma1 = iMA(Close())#talib.MA(Close(), 10)
    PlotNumeric('Ma1', Ma1[-1], RGB_Red())
    
    if len(Close(code2, Enum_Period_Day(), 1))<10:
        return
    Ma2 = iMA(Close(code2, Enum_Period_Day(), 1), 10)#talib.MA(Close(code2, Enum_Period_Day(), 1), 10) 
    PlotNumeric('Ma2', Ma2[-1], RGB_Green())


