import talib
import types
from Strategy import PairLevelGridStrategy
from Strategy import SpreadGridStrategy

strategy = None
strategis = []

# 策略开始运行时执行该函数一次
def initialize(context):
    strategy = SpreadGridStrategy()

    strategy.initialize(context,
        params = {
            'name': '玻璃_纯碱',
            'codes': ['SPD|m|FG-SA|605|605', 'ZCE|M|FG&SA|605', 'ZCE|F|FG|605', 'ZCE|F|SA|605'],
            'orderQty': 1,
            'firstPosition': True,
            'atr': 20
        },
        api = api()
    )

    strategis.append(strategy)


# 策略触发事件每次触发时都会执行该函数
def handle_data(context):
    for s in strategis:
        s.handle_data(context)

# 历史回测阶段结束时执行该函数一次
def hisover_callback(context):
    for s in strategis:
        s.hisover_callback(context)

# 策略退出前执行该函数一次
def exit_callback(context):
    pass

def api():
    api = types.SimpleNamespace(
        A_Available=A_Available,
        A_BuyPosition=A_BuyPosition,
        A_BuyPositionCanCover=A_BuyPositionCanCover,
        A_OrderStatus=A_OrderStatus,
        A_SellPosition=A_SellPosition,
        A_SellPositionCanCover=A_SellPositionCanCover,
        A_SendOrder=A_SendOrder,
        A_TotalPosition=A_TotalPosition,
        Buy=Buy,
        BuyToCover=BuyToCover,
        BuyPosition=BuyPosition,
        Close=Close,
        CurrentBar=CurrentBar,
        CurrentTime=CurrentTime,
        Enum_Buy=Enum_Buy,
        Enum_Canceled=Enum_Canceled,
        Enum_Entry=Enum_Entry,
        Enum_Exit=Enum_Exit,
        Enum_ExitToday=Enum_ExitToday,
        Enum_Filled=Enum_Filled,
        Enum_FillPart=Enum_FillPart,
        Enum_Sell=Enum_Sell,
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
        SellShort=SellShort,
        SellPosition=SellPosition,
        SetActual=SetActual,
        SetBarInterval=SetBarInterval,
        SetOrderWay=SetOrderWay,
        SetTriggerType=SetTriggerType,
        SetUserNo=SetUserNo,
        StartTrade=StartTrade,
        StopTrade=StopTrade,
        Time=Time,
        TradeDate=TradeDate,
        Vol=Vol,
    )

    return api
