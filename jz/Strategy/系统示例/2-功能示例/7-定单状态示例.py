########################系统示例不支持修改########################
# 定单状态示例
# 该策略用于演示通过定单状态记录订单信息的功能，如果手工单下单成功，就用策略下平仓单
# 该策略的开仓单通过手动下单，平仓单通过策略平仓
# 通过订阅交易数据触发可以获取定单数据，根据定单的方向，记录策略单和手挂单的信息
# 该策略仅用于演示定单状态的功能，请勿用于实盘交易
# 用户在测试时，可以将策略中的user信息改为自己的模拟账号
##################################################################
import talib as ta
import numpy as np
import time
from collections import OrderedDict
from copy import deepcopy

contractId = 'ZCE|Z|FG|MAIN'
user = 'ES001'

OrdPrice = {}  # 挂单价格

BPrice = 0   # 现价
BuyQty = 0   # 现买量
SPrice = 0   # 现卖价
SellQty = 0   # 现卖量
x = 2        
y = 100

StOrderDict = OrderedDict()  # 策略下单列表
MaOrderDict = OrderedDict()  # 手挂单列表


def initialize(context):
    if Symbol() == '':
        SetBarInterval(contractId, 'M', 1, 'N')  # 订阅合约

    SetActual()                              # 实盘运行
    SetUserNo(user)
    SetTriggerType(2)                        # 交易数据触发


def handle_data(context):
    global OrdPrice, BPrice, BuyQty, SPrice, SellQty, MaOrderDict, StOrderDict
    # 获取账户中所有合约列表
    BuyQty = Q_BidVol(contractId)     # 最新买量
    SellQty = Q_AskVol(contractId)     # 最新卖量
    BPrice = Q_BidPrice(contractId)   # 现买价
    SPrice = Q_AskPrice(contractId)   # 现卖价

    if context.triggerType() == "O":   # 触发类型为交易数据触发
        LogInfo("交易数据触发")
        triData = context.triggerData()

        idd = triData["OrderId"]
        if A_OrderStatus(idd) == Enum_FillPart() or A_OrderStatus(idd) == Enum_Filled():      # 部分成交或者完全成交

            if triData["Direct"] == "B" and triData["Offset"] == "O":  # 买开仓单
                LogInfo(f"买开成交: iid: {iid}")
                if idd in MaOrderDict:
                    MaOrderDict[idd] = triData
                    return

                MaOrderDict[idd] = triData
                price = A_OrderFilledPrice(idd) + x   # 挂单价 = 当前定单成交价 + x
                qty = A_OrderFilledLot(idd)           # 当前定单成交量
                retEnter, EnterOrderID = A_SendOrder(Enum_Sell(), Enum_Exit(), qty, price)
                if retEnter == 0:  # 定单发送成功
                    StOrderDict[EnterOrderID] = {"Direct": Enum_Sell(), "Offset": Enum_Exit(), 
                                                 "OrderPrice": price, "OrderQty": qty}
                    OrdPrice[EnterOrderID] = price         # 更新挂单价字典
            
            elif triData["Direct"] == "S" and triData["Offset"] == "O":  # 卖开仓单
                LogInfo(f"卖开成交: iid: {iid}")
                if idd in MaOrderDict:
                    MaOrderDict[idd] = triData
                    return
                
                MaOrderDict[idd] = triData
                price = A_OrderFilledPrice(idd) - x   # 挂单价 = 当前定单成交价 - x
                qty = A_OrderFilledLot(idd)           # 当前定单成交量
                retEnter, EnterOrderID = A_SendOrder(Enum_Buy(), Enum_Exit(), qty, price)
                if retEnter == 0:  # 定单发送成功
                    StOrderDict[EnterOrderID] = {"Direct": Enum_Buy(), "Offset": Enum_Exit(), 
                                                 "OrderPrice": price, "OrderQty": qty}
                    OrdPrice[EnterOrderID] = price         # 更新挂单价字典