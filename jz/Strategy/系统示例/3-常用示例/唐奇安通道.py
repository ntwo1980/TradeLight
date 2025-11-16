########################系统示例不支持修改########################
# 唐奇安通道
##################################################################
import talib
import numpy as np

# 全局变量定义
M = 5
N = 5
MaxPositionNum = 3   # 最大开仓数
StopPoint = 5        # 止损点
WinPoint = 10        # 止赢点
FloatStopStart = 50  # 浮动止损开始点
FloatStopPoint = 20  # 浮动止损点

HHV = np.array([])
LLV = np.array([])

def initialize(context): 
    # 设置K线稳定后发单
    SetOrderWay(2) 
    # 设置基准合约，会覆盖界面设置的合约，建议通过界面设置(屏蔽SetBarInterval后则界面添加合约生效)
    SetBarInterval('ZCE|Z|SR|MAIN', 'M', 1, 200, 10)   

def handle_data(context):   
    # 最少获取10根数据
    if CurrentBar() < 10:
        return

    bars = HisBarsInfo()
   
    close  = bars[-1]["LastPrice"]
    pclose = bars[-2]["LastPrice"]
    high   = bars[-1]["HighPrice"]
    phigh  = bars[-2]["HighPrice"]
    low    = bars[-1]["LowPrice"]
    plow   = bars[-2]["LowPrice"]

    # 求M周期最高
    HHV = Highest(High().tolist(), M)
    # 求N周期最低
    LLV = Lowest(Low().tolist(), N)

    PlotNumeric("LAST_HHV", HHV[-2], RGB_Red())
    PlotNumeric("LAST_LLV", LLV[-2], RGB_Green())

    if high > HHV[-2]:
        if (CurrentContracts() < MaxPositionNum) or (MarketPosition() < 0):
            Buy(1, high)
    elif low < LLV[-2]:
        if (abs(CurrentContracts()) < MaxPositionNum) or (MarketPosition() > 0):
            SellShort(1, low)
    
    # 止损
    SetStopPoint(StopPoint)
    # 止赢
    SetWinPoint(WinPoint)
    # 浮动止损, 暂不支持
    #SetFloatStopPoint(FloatStopStart, FloatStopPoint)
