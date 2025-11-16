########################系统示例不支持修改########################
# 设置函数使用注意事项
# 1、设置函数需要在初始化函数initialize中进行调用（除止损止盈外）
# 2、未设置的参数，将以界面设置为准；当界面和代码中均有设置的时候，代码设置的参数会覆盖界面设置(SetTriggerType除外)
# 3、建议用户在界面中设置，保存为默认值
##################################################################
import talib

contractId1 = "ZCE|Z|SR|MAIN"

def initialize(context): 
    # 订阅历史K线数据（自动订阅即时行情）
    # 版本新增barDataLen，代表高开低收函数返回值可取到的最大数量（可提升策略性能）
    # 先订阅的合约会被作为基准合约用于展示K线和下单信号
    SetBarInterval(contractId1, "M", 1, 500, 200) 

    # 设置触发方式
    #SetTriggerType(1)                         # 即时行情触发
    #SetTriggerType(2)                         # 交易数据触发
    #SetTriggerType(3, 1000)                   # 每隔固定时间触发：时间间隔为1000毫秒
    #SetTriggerType(4, ['223000', '223030'])   # 指定两个时刻触发
    SetTriggerType(5)                          # K线触发
    #SetTriggerType(6)                         # 连接状态触发

    # 设置发单方式 仅对当SetTriggerType 为5（K线触发）时才有意义
    #SetOrderWay(1)                             # 实时发单
    SetOrderWay(2)                              # K线稳定后发单

    #SetActual()                                # 设置实盘运行
    #SetUserNo("Test1")                         # 设置默认交易账号(已登录)，【策略只接收界面和函数指定交易账号的交易数据】
   
    #SetInitCapital(200*10000)
    #SetMargin(0, 0.08)                         # 第一个参数 0：按比例收取保证金， 1：按定额收取保证金
    #SetTradeFee('O', 2, 5)
    #SetTradeDirection(0)                       # 双向交易
    #SetMinTradeQuantity(1)
    #SetHedge('T')                              # 默认使用投机类型
    #SetSlippage(1)                             # 设置滑点

def handle_data(context):
    # 判断策略是由哪种触发方式触发
    if context.triggerType() == "T":  # 定时触发
        LogInfo("定时触发")
    elif context.triggerType() == "C":  # 时间周期触发
        LogInfo("时间周期触发")
    elif context.triggerType() == "H":  # 回测阶段K线触发
        LogInfo("回测阶段K线触发")
    elif context.triggerType() == "K":  # 实时阶段K线触发
        LogInfo("实时阶段K线触发")
    elif context.triggerType() == "S":  # 即时行情触发
        LogInfo("即时行情触发")
    elif context.triggerType() == "O":  # 委托状态变化触发
        LogInfo("委托状态变化触发")
    elif context.triggerType() == "Z":  # 市场状态变化触发
        LogInfo("市场状态变化触发")
    elif context.triggerType() == "N":  # 连接状态触发
        LogInfo("连接状态触发")


