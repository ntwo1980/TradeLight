import talib
import types
from Strategy import PairLevelGridStrategy


# 策略参数字典
g_params['threshold'] = 0.02

my_g_params = {
    #'合约': 'DCE|Z|M|MAIN',
    'name': '豆粕',
    #'codes': ['DCE|F|M|2601', 'DCE|F|M|2605', 'ZCE|F|RM|601', 'ZCE|F|RM|605'],
    #'codes': ['ZCE|F|RM|601', 'ZCE|F|RM|601', 'ZCE|F|RM|601', 'ZCE|F|RM|601'],
    'codes': ['DCE|F|JD|2601', 'DCE|F|JD|2602'],
    'orderQty': 1,
    'threshold': g_params['threshold'],
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
        params = my_g_params,
        api = api()
    )

# 策略触发事件每次触发时都会执行该函数
def handle_data(context):
    global strategy
    strategy.handle_data(context)


# 历史回测阶段结束时执行该函数一次
def hisover_callback(context):
    global strategy
    strategy.hisover_callback(context)


# 策略退出前执行该函数一次
def exit_callback(context):
    pass

def api():
    api = types.SimpleNamespace(
        A_Available=A_Available,
        A_BuyPosition=A_BuyPosition,
        A_SellPosition=A_SellPosition,
        A_TotalPosition=A_TotalPosition,
        Buy=Buy,
        BuyPosition=BuyPosition,
        Close=Close,
        CurrentBar=CurrentBar,
        CurrentTime=CurrentTime,
        Enum_Buy=Enum_Buy,
        Enum_ExitToday=Enum_ExitToday,
        ExchangeName=ExchangeName,
        ExchangeStatus=ExchangeStatus,
        High=High,
        IsInSession=IsInSession,
        LogDebug=LogDebug,
        LogError=LogError,
        LogInfo=LogInfo,
        LogWarn=LogWarn,
        Low=Low,
        MarketPosition=MarketPosition,
        Open=Open,
        PriceTick=PriceTick,
        Q_AskPrice=Q_AskPrice,
        Q_BidPrice=Q_BidPrice,
        Q_Close=Q_Close,
        Q_Last=Q_Last,
        Q_LastDate=Q_LastDate,
        Q_LowLimit=Q_LowLimit,
        Q_UpperLimit=Q_UpperLimit,
        Sell=Sell,
        SellPosition=SellPosition,
        SetActual=SetActual,
        SetBarInterval=SetBarInterval,
        SetOrderWay=SetOrderWay,
        SetTriggerType=SetTriggerType,
        StartTrade=StartTrade,
        StopTrade=StopTrade,
        Time=Time,
        TradeDate=TradeDate,
        Vol=Vol,
    )

    return api
