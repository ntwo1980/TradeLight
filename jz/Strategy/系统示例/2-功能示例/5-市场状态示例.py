########################系统示例不支持修改########################
# 市场状态示例
# 提示：该策略仅仅为了演示市场状态触发功能，请勿使用实盘交易账号运行该策略！！

# 用户可以根据市场状态触发的相关信息去控制抢单、数据统计、发送通知等相关的操作；
# 该策略演示了简单的利用市场状态数据控制策略交易的例子，当用户订阅的合约的交易所状态为竞价撮合或连续交易阶段时，买入一手合约，
# 当用户订阅的合约的交易所状态为交易暂停或闭市时，输出日志信息。
# 用户可以根据市场状态去实现自己期望的策略行为。

# 市场状态的推送数据需要订阅交易数据触发类型
# 市场状态数据属于交易数据，需要登录交易账号才能获取交易数据，用户在使用该策略时需要将策略中的user修改为自己登录的账号
# 市场状态数据中包含服务器标识、交易所代码、交易所时间、本地时间、交易状态和品种代码的信息，可以通过context.triggerData函数获取
# context.triggerData()中交易状态的含义可以查看ExchangeStatus()函数的说明
##################################################################
import talib as ta
import numpy as np

ContractId = 'ZCE|Z|FG|MAIN'
user = 'ES001'

# 交易所状态
exhStateDict = {
      'N':  "未知状态",
      'I':  "正初始化",
      'R':  "准备就绪",
      '0':  "交易日切换",
      '1':  "竞价申报",
      '2':  "竞价撮合",
      '3':  "连续交易",
      '4':  "交易暂停",
      '5':  "交易闭市",
      '6':  "竞价暂停",
      '7':  "报盘未连",
      '8':  "交易未连",
      '9':  "闭市处理"
}

def initialize(context): 
    if Symbol() == '':
        SetBarInterval(ContractId, Enum_Period_Min(), 1, 500)

    SetTriggerType(2)
    SetUserNo(user)


def handle_data(context):
    if context.triggerType() == 'Z':   # 触发类型为交易数据中的市场状态触发
        exhData = context.triggerData()
        if exhData["ExchangeNo"] == ExchangeName(ContractId):
            # 输出市场状态数据的部分信息
            LogInfo(f"{ContractId}的交易所状态为: {exhStateDict[exhData['TradeState']]}")
            LogInfo(f"{exhData['ExchangeNo']}交易所当前时间为: {exhData['ExchangeDateTime']}")
            LogInfo(f"当前的本地时间为: {exhData['LocalDateTime']}")
        
        if exhData["TradeState"] == '2' or exhData["TradeState"] == '3':  # 当前交易所状态为竞价撮合阶段或连续交易
            retCode, retMsg = A_SendOrder(Enum_Buy(), Enum_Entry(), 1, Q_SettlePrice())  # 用结算价买入一手合约
            if retCode == 0:
                LogInfo("定单发送成功")
            else:
                LogInfo("定单发送失败")

        elif exhData["TradeState"] == '4' or exhData["TradeState"] == '5':  # 当前交易所状态为交易暂停或交易闭市
            LogInfo("当前交易所状态为交易暂停或交易闭市")

    

    

    


