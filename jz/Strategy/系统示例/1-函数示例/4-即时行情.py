########################系统示例不支持修改########################
# 获取即时行情数据，需要先订阅即时行情
# 即时行情正常切片郑州一秒钟最多四笔（但是还有深度和分包的关系，会收到更多的触发）
# 大连、上期、中金等一秒钟最多两笔切片（上期深度关系会更多）
# 外盘切片无固定限制，行情量波动大时会更多
##################################################################
contractId1 = 'ZCE|Z|SR|MAIN'
contractId2 = 'ZCE|Z|CF|MAIN'
kType = "M" 
kSlice = 1 
qty = 1                          

def initialize(context):
    # 设置触发方式为即时行情触发
    SetTriggerType(1)
    # 订阅历史K线 订阅即时行情
    SetBarInterval(contractId1, kType, kSlice, qty)
    # 订阅即时行情
    SubQuote(contractId2)

def handle_data(context):
    # 即时行情触发时打印信息
    if context.triggerType() == "S" and context.contractNo() == contractId1:
        LogInfo("合约: ", contractId1)
        LogInfo("即时行情更新时间: ", Q_UpdateTime())
        
        LogInfo("最新价: ", Q_Last())
        LogInfo("现手: ", Q_LastVol())
        
        LogInfo("最新买价: ", Q_BidPrice())
        LogInfo("最新买量: ", Q_BidVol())
        LogInfo("最新卖价: ", Q_AskPrice())
        LogInfo("最新卖量: ", Q_AskVol())
           
        LogInfo("当日成交量: ", Q_TotalVol())
        LogInfo("当日涨跌: ", Q_PriceChg())
        LogInfo("当日涨跌幅: ", Q_PriceChgRadio())
        LogInfo("持仓量: ", Q_OpenInt())
        LogInfo("当日开盘价: ", Q_Open())
        LogInfo("当日收盘价: ", Q_Close())
        LogInfo("当日最高价: ", Q_High())
        LogInfo("当日最低价: ", Q_Low())
        
        LogInfo("昨收盘价: ", Q_PreClose())
        LogInfo("昨结算: ", Q_PreSettlePrice())       
        LogInfo("最新成交日期: ", Q_LastDate())    
        LogInfo("最新成交时间: ", Q_LastTime())        
        LogInfo("历史最高价: ", Q_HisHigh())
        LogInfo("历史最低价: ", Q_HisLow())
        
        LogInfo("当日成交额: ", Q_TurnOver())
        LogInfo("实时均价: ", Q_AvgPrice())
        LogInfo("当日最低价: ", Q_Low())
        LogInfo("当日跌停板价: ", Q_LowLimit())       
        LogInfo("当日涨停板价: ", Q_UpperLimit())
        LogInfo("当日期权波动率: ", Q_Sigma())

    if context.triggerType() == "S" and context.contractNo() == contractId2:
        LogInfo("合约: ", contractId2)
        LogInfo("即时行情更新时间: ", Q_UpdateTime(contractId2))
        LogInfo("最新卖价: ", Q_AskPrice(contractId2))
        LogInfo("最新卖量: ", Q_AskVol(contractId2))
       
        LogInfo("最新买价: ", Q_BidPrice(contractId2))
        LogInfo("最新买量: ", Q_BidVol(contractId2))