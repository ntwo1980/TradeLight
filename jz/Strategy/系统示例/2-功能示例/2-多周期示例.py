########################系统示例不支持修改########################
# 多周期示例
# 备注：订阅多个周期的K线数据时，仅基准合约的数据会触发handle_data,其他周期
# K线数据仅更新本地数据，不触发
##################################################################
import talib as ta
import numpy as np

ContractId = 'SHFE|Z|CU|MAIN'
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
    global ContractId
    # 订阅15分钟
    SetBarInterval(ContractId, Enum_Period_Min(), 15, 100)
    # 订阅日线
    SetBarInterval(ContractId, Enum_Period_Day(), 1, 100)

def handle_data(context):
    global ContractId

    # 取15分钟收盘价
    arr1 = HisData(Enum_Data_Close(), Enum_Period_Min(), 15, ContractId)
    # 取日线的上周期开盘价
    arr2 = HisData(Enum_Data_Open(), Enum_Period_Day(), 1, ContractId)

    if len(arr1) == 0:
        LogInfo("%s:暂未获取到15分钟数据\n" % ContractId)
    else:
        ret, ma1 = iMA(arr1)
        LogInfo("%s:的15分钟线当前MA值为:%f\n" %(ContractId, ma1))

    if len(arr2) == 0:
        LogInfo("%s:暂未获取到日线数据\n" % ContractId)
    else:
        ret, ma2 = iMA(arr2, 20, 1)
        LogInfo("%s:的日线前一周期MA值为:%f\n" %(ContractId, ma2))


