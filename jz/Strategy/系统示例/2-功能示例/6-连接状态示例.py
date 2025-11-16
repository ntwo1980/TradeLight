########################系统示例不支持修改########################
# 连接状态示例
# 用户需要连接状态触发策略时需要在界面上选择连接状态触发或是通过SetTriggerType(6)订阅该触发方式
# 用户可以根据相关服务器的连接状态对策略进行相关的操作，本示例中在收到服务器的连接状态时重新开始实盘交易，收到服务器的断开状态时暂停实盘交易
# 备注：
#   连接状态分为行情服务器和交易服务器的连接状态，当为交易服务器的连接状态触发时，context.triggerData()的"UserNo"字段为空字符串""
#   交易服务器的连接状态仅能收到通过界面或者SetUserNo函数关联的账户的连接状态
##################################################################

import talib as ta
import numpy as np

ContractId = 'ZCE|Z|FG|MAIN'
user = 'ES001'

def initialize(context): 
    if Symbol() == '':
        SetBarInterval(ContractId, Enum_Period_Min(), 15, 500)
    # 策略仅能收到 通过界面或者SetUserNo函数关联的账户的交易数据
    # 交易数据涵盖 委托、成交、持仓、资金、市场状态
    # 委托、成交、持仓仅支持访问本策略相关合约数据（通过界面或者SetBarInterval和SubQuote引用的合约）
    SetUserNo(user)
    SetTriggerType(6)


def handle_data(context):
    # 连接状态触发且为行情服务器的状态触发
    if context.triggerType() == "N" and context.triggerData()["ServerType"] == "Q":
        if context.triggerData()["EventType"] == 1:  # 行情服务器为连接状态
            StartTrade()  # 重新开始实盘交易
        elif context.triggerData()["EventType"] == 2:  # 行情服务器为断开状态
            StopTrade()   # 暂停实盘交易
    
    # 连接状态触发且为交易服务器的状态触发
    if context.triggerType() == "N" and context.triggerData()["ServerType"] == "T":
        triData = context.triggerData()
        if triData["UserNo"] == user and triData["EventType"] == 1:  # user账号为连接状态
            StartTrade()  # 重新开始实盘交易   
        elif triData["UserNo"] == user and triData["EventType"] == 2:  # user账号为未连接状态
            StopTrade()   # 暂停实盘交易
        
        

    

    


