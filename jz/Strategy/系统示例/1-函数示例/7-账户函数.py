########################系统示例不支持修改########################
# 关于账户函数和交易数据请注意以下 4 点：
# 1、交易数据包括委托、成交、持仓、资金、市场状态等信息
# 2、账户：可访问通过 界面 或者 SetUserNo 函数关联的账户的交易数据
# 3、合约：可访问通过 界面 或者 SetBarInterval和SubQuote 引用的合约的交易数据
# 4、若虚拟合约ZCE|Z|AP|MAIN 的真实合约为 ZCE|F|AP|105 则A函数访问和交易的合约是 ZCE|F|AP|105 相关的数据***
##################################################################
import talib

# 定义全局变量
ShortPeriod = 5
LongPeriod = 20

OrderNum = 1
EnterOrderId = -1
ExitOrderId = -1
retEnter = -1
retExit = -1
ContractId = "ZCE|Z|AP|MAIN"
UserId = "ES001"


# 初始化函数
def initialize(context):  
    SetBarInterval(ContractId, 'M', 1, 100)
    SetTriggerType(5)
    SetTriggerType(2)
    SetOrderWay(2)
    SetActual()
    SetUserNo(UserId) # 设置交易账号
    
# 策略触发执行函数
def handle_data(context):
    # 使用全局变量
    global EnterOrderId, ExitOrderId
    global ShortPeriod, LongPeriod
    global OrderNum
    global ContractId, UserId
    global retEnter, retExit
    
    if CurrentBar() < LongPeriod:
        return
        
    # 定义局部变量
    MovePoint = 10
    MinPoint = PriceTick()
    
    ma1 = talib.MA(Close(), timeperiod=ShortPeriod)
    ma2 = talib.MA(Close(), timeperiod=LongPeriod)
    
    #撤消未成交开仓单
    if retEnter == 0 and A_OrderStatus(EnterOrderId) != '6':
        LogInfo("撤销未成交的开仓单：%s, 订单状态值：%d, 可用资金：%f" %(EnterOrderId, A_DeleteOrder(EnterOrderId), A_Available()))
        retEnter = -1  
    #撤消未成交平仓单
    if retExit == 0 and A_OrderStatus(ExitOrderId) != '6':
        LogInfo("撤销未成交的平仓单：%s, 订单状态值：%d, 可用资金：%f" %(ExitOrderId, A_DeleteOrder(ExitOrderId), A_Available()))
        retExit = -1
    
    #实时K线判断，避免循环触发
    if context.triggerType() == 'K':
        if A_TotalPosition() == 0:
            if ma1[-1] > ma2[-1]:
                retEnter, EnterOrderId = A_SendOrder(Enum_Buy(), Enum_EntryExitIgnore(), OrderNum, Q_AskPrice() + MovePoint * MinPoint, ContractId, UserId, Enum_Order_Limit(), Enum_FOK(), Enum_Speculate())
                if retEnter == 0:
                    LogInfo("定单号：%s, 合约：%s, 买入开仓数量：%d, 价格: %f" %(EnterOrderId, ContractId, OrderNum, Q_AskPrice() + MovePoint * MinPoint))
                else:
                    LogInfo("买入开仓 error: ",retEnter)
            elif ma1[-1] < ma2[-1]:
                retEnter, EnterOrderId = A_SendOrder(Enum_Sell(), Enum_EntryExitIgnore(), OrderNum, Q_BidPrice()  - MovePoint * MinPoint, ContractId, UserId, Enum_Order_Limit(), Enum_FOK(), Enum_Speculate())
                if retEnter == 0:
                    LogInfo("定单号：%s, 合约：%s, 卖出开仓数量：%d, 价格: %f" %(EnterOrderId, ContractId, OrderNum, Q_BidPrice() - MovePoint * MinPoint))
                else:
                    LogInfo("卖出开仓 error: ",retEnter)
        else:
            LogInfo("不操作, 总仓位:%d, 多头仓位:%d, 空头仓位:%d" % (A_TotalPosition(), A_BuyPosition(), A_SellPosition()))

    
    if context.triggerType() == 'O':
        # 定单状态变化   已发送--已受理--已排队--完全成交
        #                已发送--已受理--已排队--部分成交--（撤单）--已撤余单
        #                已发送--已受理--已排队--（撤单）--已撤单
        #                已发送--已受理--指令失败
        #                中间状态 已受理 已排队 完全成交 等可能会收到多次，请根据实际需要过滤重复
        LogInfo("报单状态: ", context.triggerData()['OrderState'])

        # 完全成交
        if context.triggerData()['OrderState'] == '6':

            # 注意：收到完全成交的通知时，由于委托和持仓是异步更新的，持仓量不能保证同步更新

            # 输出指定交易账户的当前商品的买入持仓量、买入持仓均价
            LogInfo("帐户下当前商品的买入持仓均价: ", A_BuyAvgPrice())
            LogInfo("帐户下当前商品的买入持仓量: ", A_BuyPosition())
            # 输出指定交易账户的当前商品的买仓可平数量、买入持仓盈亏
            LogInfo("帐户下买仓可平数量: ", A_BuyPositionCanCover())
            LogInfo("帐户下当前商品的买入持仓盈亏: ", A_BuyProfitLoss())
            # 输出指定交易账户的当前商品的卖出持仓量、卖出持仓均价
            LogInfo("帐户下当前商品的卖出持仓均价: ", A_SellAvgPrice())
            LogInfo("帐户下当前商品的卖出持仓: ", A_SellPosition())
            # 输出指定交易账户的当前商品的卖仓可平数量、卖出持仓盈亏
            LogInfo("帐户下卖仓可平数量: ", A_SellPositionCanCover())
            LogInfo("帐户下当前商品的卖出持仓盈亏: ", A_SellProfitLoss())  
            # 输出当前账户指定商品的持仓均价、总持仓量、总持仓盈亏、当日买入持仓量、当日卖出持仓量
            LogInfo("帐户下当前商品的持仓均价: ", A_TotalAvgPrice())
            LogInfo("帐户下当前商品的总持仓量: ", A_TotalPosition())
            LogInfo("帐户下当前商品的总持仓盈亏: ", A_TotalProfitLoss())
            LogInfo("帐户下当前商品的当日买入持仓量: ", A_TodayBuyPosition())
            LogInfo("帐户下当前商品的当日卖出持仓量: ", A_TodaySellPosition())

            # 计算手续费和保证金
            calcFee = A_CalcParam() # 获取合约的计算参数
            fee = 0
            dat = context.triggerData()
            if context.triggerData()["Offset"] == Enum_Entry():
                fee  = (dat["OrderPrice"] * MinPoint *calcFee["OpenFeeRatio"] + calcFee["OpenFeeAmount"]) * dat["OrderQty"]
            elif context.triggerData()["Offset"] == Enum_Exit():
                fee  = (dat["OrderPrice"] * MinPoint *calcFee["CoverFeeRatio"] + calcFee["CoverFeeAmount"]) * dat["OrderQty"]
            elif context.triggerData()["Offset"] == Enum_ExitToday():
                fee  = (dat["OrderPrice"] * MinPoint *calcFee["CoverTodayFeeRatio"] + calcFee["CoverTodayFeeAmount"]) * dat["OrderQty"]
            LogInfo("定单%s的手续费为: %f" % (dat["StrategyOrderId"], fee))


            # 取与本地订单号相同的orderNo 输出合约持仓信息
            sessionId, orderNo =  A_GetOrderNo(EnterOrderId)
            if context.triggerData()['OrderNo'] == orderNo:
                # 输出某一订单号的信息
                LogInfo("---------------------------------------------------------------")
                orderId = context.triggerData()["OrderId"]
                LogInfo("该订单号为： ", orderNo)
                # A_OrderBuyOrSell()函数返回订单买卖类型，返回值含义如下：
                # 'B' : 买入，'S' : 卖出，'A' : 双边
                LogInfo("帐户下当前商品的某个委托单的买卖类型: ", A_OrderBuyOrSell(orderId))
                # A_OrderEntryOrExit函数返回订单开平仓状态，返回值含义如下
                # 'N' : 无, 'O': 开仓, 'C' : 平仓, 'T' : 平今
                LogInfo("帐户下当前商品的某个委托单的开平仓状态: ", A_OrderEntryOrExit(orderId))

                LogInfo("帐户下当前商品的某个委托单的成交数量: ", A_OrderFilledLot(orderId))
                LogInfo("帐户下当前商品的某个委托单的成交价格: ", A_OrderFilledPrice(orderId))
                LogInfo("帐户下当前商品的某个委托单的委托数量: ", A_OrderLot(orderId))
                LogInfo("帐户下当前商品的某个委托单的委托价格: ", A_OrderPrice(orderId))
                # A_OrderStatus()函数返回委托单的状态，返回值含义可查看函数说明
                LogInfo("帐户下当前商品的某个委托单的状态: ", A_OrderStatus(orderId))
                LogInfo("委托单是否完结: ", A_OrderIsClose(orderId))
                # 输出订单的委托时间
                LogInfo("帐户下当前商品的某个委托单的委托时间: ", A_OrderTime(orderId))
                # 订单所对应的下单合约
                LogInfo("订单的合约号： ", A_OrderContractNo(orderId))
                # 输出orderNo对应的订单的下一个订单号
                LogInfo("当前账户下一个订单号： ", A_NextOrderNo(orderId))
                # 输出orderNo对应的订单的下一个订单号
                LogInfo("当前账户的下一个排队(可撤)订单号： ", A_NextQueueOrderNo(orderId))
                
        
        


