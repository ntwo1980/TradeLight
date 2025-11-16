########################系统示例不支持修改########################
# 【Buy】、【Sell】系列函数主要用于【历史回测】
# 【实盘阶段】也支持发单交易，但是需要配合【策略仓】使用(实盘阶段-可以根据实际需要选择【账户函数】进行持仓判断和下单)
# 在【行情断线】、【交易断线】或者其他情况下，可以调用【UnLoadStrategy】实现【卸载策略】
# 可以配合定时触发，在指定时间调用【ReloadStrategy】重新启动策略（效果等同手动新启动策略），起到【定时任务】作用
##################################################################
import talib

code = 'ZCE|Z|SR|MAIN'

def initialize(context): 
    SetBarInterval(code, 'M', 1, 200)
    SetTriggerType(5) #K线触发
    SetTriggerType(6) #连接状态触发
    SetActual() # 实盘运行

def handle_data(context):
    # 回测阶段K线触发
    if context.triggerType() == 'H':
        if CurrentBar() == 1:
            # 以最新收盘价，买开一手
            # 合约不设置时，以基准合约买入
            # needCover 默认为True 此时如果当前有空仓，先平后开；False时，不平仓，直接开仓
            Buy(1, Close()[-1])
        if CurrentBar() == 2:
            # 与Buy 函数对应，以最新收盘价，卖开一手 
            # 当前默认平仓为True， 会将第一根K线买开全部平完之后，开1手空仓
            # 可参照输出的持仓信息对比用法
            SellShort(1, Close()[-1])
        if CurrentBar() == 3:
            # 以最新收盘价，平一手卖开仓
            # 合约不设置时，以基准合约为准
            BuyToCover(1, Close()[-1])
        if CurrentBar() == 4:
            # 与BuyToCover 对应，该函数产生一个多头平仓操作
            # 如果当前持仓状态为持平，该函数不执行任何操作。
            # 如果当前持仓状态为空仓，该函数不执行任何操作。
            # 如果当前持仓状态为多仓，如果此时orderQty使用默认值，该函数将平掉所有多仓，达到持平的状态，否则只平掉参数orderQty的多仓。
            # 由于前三根操作，当前买卖持仓均为0，此时Sell函数不执行任何操作
            Sell(1, Close()[-1])
        LogInfo("++++++++++++++++++++++++++++++++++")
        LogInfo("CurrentBar: ", CurrentBar())
        LogInfo("BuyPosition: ", BuyPosition())
        LogInfo("SellPosition: ", SellPosition())
        LogInfo("==================================")

    # 连状态触发
    if context.triggerType() == 'N': 
        if context.triggerData()['ServerType'] == 'T':# 交易
            if context.triggerData()['EventType'] == 1:# 交易连接
				# 盘中重新启动实盘交易
                StartTrade()
                LogInfo('StartTrade')
            else: # 交易断开
                # 盘中暂时停止实盘交易
                StopTrade()
                LogInfo('StopTrade')
            LogInfo('IsTradeAllowed', IsTradeAllowed())
           
        


