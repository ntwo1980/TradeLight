########################系统示例不支持修改########################
# 穿越价位报警
##################################################################
import talib
import winsound
import numpy as np

contractNo = "ZCE|Z|AP|MAIN"  # 订阅的合约编号
arr = np.array([])
# 修改p1和price变量定义MA参数和穿越价位
p1 = 30                      # MA周期
price = 4850                 # 穿越价位


def initialize(context): 
    SetBarInterval(contractNo, "M", 1, 200)  # 订阅200根1分钟苹果历史行情
    SetTriggerType(1)                        # 即时行情触发
    SetTriggerType(5)                        # K线触发
    SetActual()                              # 实盘运行

def handle_data(context):
    global p1, price, arr
    
    if len(Close()) < p1:
        return

    p_arr = np.concatenate((arr,[p1]))
    arr = np.append(p_arr,p1)
    
    MA1 = talib.MA(Close(), 30)     # 30周期收盘价均值
    # 画线
    if MA1[-1] > REF(MA1, 1):
        PlotNumeric("Up", MA1[-1], RGB_Red(), False)
    else:
        PlotNumeric("Down", MA1[-1], RGB_Green(), False)
    
    if CrossOver(MA1, arr) or CrossUnder(MA1, arr):
        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
        

    