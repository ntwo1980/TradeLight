########################系统示例不支持修改########################
# 属性函数可以帮助我们有效控制策略的执行
# 合约信息之最小变动价，可以辅助我们进行价格超价（限价单要求委托价是最小变动价的整数倍）
# 交易时段之IsInSession()，可以帮助我们判断客户端本地时间是否在交易时段中
# 交易所状态之ExchangeTime()，返回的是交易所当前时间(由于传输延时会有细微出入，不同后台差异会比较大，请使用前先进行测试)
# 策略属性配置之Config函数，可以获取用户通过界面和initialize函数中设置的策略属性
##################################################################

contractId = 'ZCE|Z|SR|MAIN'
# 策略开始运行时执行该函数一次
def initialize(context):
	# 订阅历史K线 订阅即时行情
    SetBarInterval(contractId, "M", 1, 10)
    # 设置触发方式为即时行情触发
    SetTriggerType(1)
    # 通过Config()函数获取用户在界面上和策略中设置的合约信息，注意：在Config之后设置的属性无法正确获取
    LogInfo(Config()["ContDetail"])

# 策略触发事件每次触发时都会执行该函数
def handle_data(context):
    # 以下函数参数不填的情况均默认使用订阅的基准合约信息：即第一次使用SetBarInterval()函数订阅的合约信息
    # 或者是在界面上选择的第一个合约的信息
 
    # 合约信息
    LogInfo("界面合约图表K线周期数值: ", BarInterval())
    LogInfo("界面合约图表K线周期类型: ", BarType())
    LogInfo("合约对应交易所名称: ", ExchangeName(ExchangeName()))
    LogInfo("合约对应品种编号: ", SymbolType())
    LogInfo("合约编号: ", Symbol())
    LogInfo("商品主连/近月对应的合约: ", GetTrendContract())
    LogInfo("合约名称: ", SymbolName())
    LogInfo("买卖盘个数: ", BidAskSize())
    LogInfo("合约的每手乘数: ", ContractUnit())
    LogInfo("合约最小变动价: ", PriceTick())
    LogInfo("合约价格精度: ", PriceScale())
    LogInfo("合约保证金比率: ", MarginRatio())
    LogInfo("可用于回测的历史数据根数: ", MaxBarsBack())
    LogInfo("单笔交易限量: ", MaxSingleTradeSize())
    
	# 交易时间段
    LogInfo("交易时间段的个数: ", GetSessionCount())
    # 循环
    LogInfo("交易时间段的开始时间: ", GetSessionStartTime(), GetSessionEndTime())#0.2100
    # IsInSession用于判断操作系统的当前时间是否在指定合约的交易时段内(适用于实时阶段)
    LogInfo("当前时间是否为交易时间: ", IsInSession()) 

    # 需要交易登录
    # 注意: ExchangeTime返回的是交易所当前时间
    LogInfo("合约对应交易所时间: ", ExchangeTime(ExchangeName()))
    # ExchangeStatus返回交易所的状态，返回值含义可查看该函数说明
    LogInfo("合约对应交易所状态: ", ExchangeStatus(ExchangeName()))
    # 返回品种交易状态，返回值含义可查看该函数说明
    LogInfo("品种或合约交易状态: ", CommodityStatus(contractId))
    
    # 策略属性配置信息的用户列表
    LogInfo("策略配置账户信息：", Config()["UserNo"])