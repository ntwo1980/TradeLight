########################系统示例不支持修改########################
# 极智量化为用户提供了四个入口函数用于编写策略：
# initialize()、handle_data()、hisover_callback()、exit_callback()，
 
# 每个入口函数都包含一个context参数用于带入策略的上下文信息，
# 上下文信息包括：
# strategyStatus()当前策略状态
# triggerType()当前触发类型
# contractNo()当前触发合约
# kLineType()当前触发的K线类型
# kLineSlice()当前K线触发的K线周期
# tradeDate()当前触发的交易日
# dateTimeStamp()当前触发的时间戳
# triggerData()当前触发类型对应的数据(具体内容参见函数备注)

# 该策略展示如何使用这些方法查看策略当前运行的上下文信息
##################################################################
contractId = "ZCE|Z|SR|MAIN"    #将合约代码定义为变量, 修改合约编号时只需修改该变量值
showCount = 10

# 策略开始运行时执行该函数一次
def initialize(context): 
    # 订阅contractId的一分钟数据10根
    SetBarInterval(contractId, "M", 1, 10)
    # 设置触发方式
    # SetTriggerType(1)   # 即时行情触发(测试时可放开屏蔽)
    SetTriggerType(2)   # 交易数据触发
    SetTriggerType(4, ['090500'])  # 定时触发：9:05触发策略
    SetTriggerType(5)   # K线触发
    SetTriggerType(6)   # 连接状态触发
    #SetUserNo("ES001")  # 替换为自己的资金账号
    SubQuote(contractId)

# 策略触发事件每次触发时都会执行该函数
def handle_data(context):
    # 判断当前的触发方式
    if context.triggerType() == "S":    # 即时行情触发
        if showCount <= 0:            # 打印十笔数据
            return
        else:
            showCount-=1
        LogInfo("触发方式为即时行情触发")
        LogInfo("策略当前状态: ", context.strategyStatus())
        # 打印当前策略的触发合约
        LogInfo("策略当前触发合约: ", context.contractNo())
        # 打印当前触发的K线类型，'T'：分笔， 'M'：分钟，'D'：日线
        LogInfo("策略当前触发的K线类型: ", context.kLineType())
        # 打印当前触发的K线周期
        LogInfo("策略当前触发的K线周期: ", context.kLineSlice())
        # 打印当前触发的交易日
        LogInfo("策略当前触发的交易日: ", context.tradeDate())
        # 打印当前触发的时间戳
        LogInfo("策略当前触发的时间戳: ", context.dateTimeStamp())
        # 打印当前触发类型对应的数据详情
        LogInfo("策略当前触发类型对应的数据: ", context.triggerData()['ContractNo'],context.triggerData()['UpdateTime'])

    elif context.triggerType() == "H":  # 历史阶段K线触发
        LogInfo("触发方式为历史阶段K线触发")
        LogInfo("策略当前状态: ", context.strategyStatus())
        # 打印当前策略的触发合约
        LogInfo("策略当前触发合约: ", context.contractNo())
        # 打印当前触发的K线类型，'T'：分笔， 'M'：分钟，'D'：日线
        LogInfo("策略当前触发的K线类型: ", context.kLineType())
        # 打印当前触发的K线周期
        LogInfo("策略当前触发的K线周期: ", context.kLineSlice())
        # 打印当前触发的交易日
        LogInfo("策略当前触发的交易日: ", context.tradeDate())
        # 打印当前触发的时间戳
        LogInfo("策略当前触发的时间戳: ", context.dateTimeStamp())
        # 打印当前触发类型对应的数据详情
        LogInfo("策略当前触发类型对应的数据: ", context.triggerData())
    
    elif context.triggerType() == "T":  # 定时触发
        LogInfo("触发方式为定时触发")
        LogInfo("策略当前状态: ", context.strategyStatus())
        # 打印当前策略的触发合约
        LogInfo("策略当前触发合约: ", context.contractNo())
        # 打印当前触发的K线类型，'T'：分笔， 'M'：分钟，'D'：日线
        LogInfo("策略当前触发的K线类型: ", context.kLineType())
        # 打印当前触发的K线周期
        LogInfo("策略当前触发的K线周期: ", context.kLineSlice())
        # 打印当前触发的交易日
        LogInfo("策略当前触发的交易日: ", context.tradeDate())
        # 打印当前触发的时间戳
        LogInfo("策略当前触发的时间戳: ", context.dateTimeStamp())
        # 打印当前触发类型对应的数据详情
        LogInfo("策略当前触发类型对应的数据: ", context.triggerData())

    elif context.triggerType() == "O":  # 委托状态变化触发
        LogInfo("触发方式为委托状态变化触发")
        LogInfo("策略当前状态: ", context.strategyStatus())
        # 打印当前策略的触发合约
        LogInfo("策略当前触发合约: ", context.contractNo())
        # 打印当前触发的K线类型，'T'：分笔， 'M'：分钟，'D'：日线
        LogInfo("策略当前触发的K线类型: ", context.kLineType())
        # 打印当前触发的K线周期
        LogInfo("策略当前触发的K线周期: ", context.kLineSlice())
        # 打印当前触发的交易日
        LogInfo("策略当前触发的交易日: ", context.tradeDate())
        # 打印当前触发的时间戳
        LogInfo("策略当前触发的时间戳: ", context.dateTimeStamp())
        # 打印当前触发类型对应的数据详情
        LogInfo("策略当前触发类型对应的数据: ", context.triggerData())

    elif context.triggerType() == "N":  # 连接状态发生变化
        LogInfo("连接状态发生变化触发")
        # 打印连接类型
        LogInfo("连接类型(Q行情 T交易): ", context.triggerData()["ServerType"])
        # 打印状态
        LogInfo("连接状态(1连接 2断开): ", context.triggerData()["EventType"])
        # 打印账号 行情为认证账号 交易为资金账号
        LogInfo("账号信息: ", context.triggerData()["UserNo"])

    elif context.triggerType() == "Z":  # 市场状态发生变化
        LogInfo("市场状态发生变化")
         # 打印当前触发的时间戳
        LogInfo("策略当前触发的时间戳: ", context.dateTimeStamp())
        # 打印当前触发类型对应的数据详情
        LogInfo("策略当前触发类型对应的数据: ", context.triggerData())

# 策略退出前执行该函数一次
def exit_callback(context):
    LogInfo("策略退出")