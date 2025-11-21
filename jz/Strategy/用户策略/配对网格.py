import talib
import types
from Strategy import PairLevelGridStrategy

# 策略参数字典
g_params = {
    #'合约': 'DCE|Z|M|MAIN',
    'codes': ['DCE|F|M|2601', 'DCE|F|M|2605', 'ZCE|F|RM|601', 'ZCE|F|RM|605'],
    'orderQty': 1,
    #'codes': ['ZCE|F|RM|601', 'DCE|F|M|2601'],
    #'轴价': 3200,
    #'每格跳数': 5,
    #'K线数量': 2000,
    #'保证金': 1999,
    #'手续费': 10
}
strategy = None

# 策略开始运行时执行该函数一次
def initialize(context): 
    global strategy
    strategy = PairLevelGridStrategy()

    strategy.initialize(context, 
        params = g_params,
        api = api()
    )

# 策略触发事件每次触发时都会执行该函数
def handle_data(context):
    global strategy
    strategy.handle_data(context)
    # 输出当前的K线索引，索引值从1开始
    # LogInfo("当前K线索引: ", CurrentBar())
    # 输出当前Bar的状态值, 0表示第一个Bar,1表示中间普通Bar,2表示最后一个Bar
    # LogInfo("当前Bar的状态值：", BarStatus())
    # LogInfo("当前Bar的时间： ", Time())
    # LogInfo("当前Bar的日期：", Date())
    # LogInfo("当前Bar的交易日: ", TradeDate())


# 历史回测阶段结束时执行该函数一次
def hisover_callback(context):
    pass


# 策略退出前执行该函数一次
def exit_callback(context):
    pass

def api():
    api = types.SimpleNamespace(
        A_Available=A_Available，
        PriceTick=PriceTick,
        LogDebug=LogDebug,
        LogInfo=LogInfo,
        LogWarn=LogWarn,
        LogError=LogError,
        SetBarInterval=SetBarInterval,
        Open=Open,
        Close=Close,
        High=High,
        Low=Low,
        Vol=Vol,
        TradeDate = TradeDate,
        Time=Time,
        CurrentTime=CurrentTime,
        Q_Close=Q_Close,
        Q_Last=Q_Last,
        Q_LastDate=Q_LastDate,
        SetOrderWay=SetOrderWay,
        MarketPosition=MarketPosition,
        A_TotalPosition=A_TotalPosition,
        BuyPosition=BuyPosition,
        SellPosition=SellPosition,
        A_BuyPosition=A_BuyPosition,
        A_SellPosition=A_SellPosition,
        Enum_Buy=Enum_Buy,
        Enum_ExitToday=Enum_ExitToday,
        ExchangeName=ExchangeName,
        ExchangeStatus=ExchangeStatus,
        StartTrade=StartTrade,
        StopTrade=StopTrade,
        IsInSession=IsInSession,
    )

    return api

