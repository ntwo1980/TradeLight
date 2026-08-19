import types

from Strategy import AdxTrendMomentumStrategy


strategy = None
strategis = []


def initialize(context):
    strategy = AdxTrendMomentumStrategy()
    strategy.initialize(context,
        params={
            'name': 'ADX趋势动量_淀粉',
            'code': 'DCE|F|C|2609',
            'orderQty': 2,
            'direction': 'both',
        },
        api=api()
    )
    strategis.append(strategy)


def handle_data(context):
    for strategy in strategis:
        strategy.handle_data(context)


def hisover_callback(context):
    for strategy in strategis:
        strategy.hisover_callback(context)


def exit_callback(context):
    for strategy in strategis:
        strategy.exit_callback(context)


def api():
    return types.SimpleNamespace(
        A_Available=A_Available,
        A_BuyPosition=A_BuyPosition,
        A_BuyPositionCanCover=A_BuyPositionCanCover,
        A_DeleteOrder=A_DeleteOrder,
        A_SellPosition=A_SellPosition,
        A_SellPositionCanCover=A_SellPositionCanCover,
        A_SendOrder=A_SendOrder,
        A_OrderBuyOrSell=A_OrderBuyOrSell,
        A_OrderEntryOrExit=A_OrderEntryOrExit,
        A_OrderFilledLot=A_OrderFilledLot,
        A_OrderFilledPrice=A_OrderFilledPrice,
        A_OrderStatus=A_OrderStatus,
        A_TotalPosition=A_TotalPosition,
        Buy=Buy,
        BuyToCover=BuyToCover,
        BuyPosition=BuyPosition,
        Close=Close,
        CurrentBar=CurrentBar,
        CurrentTime=CurrentTime,
        DeleteAllOrders=DeleteAllOrders,
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
        GetTrendContract=GetTrendContract,
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
        TimeDiff=TimeDiff,
        TradeDate=TradeDate,
        Vol=Vol,
    )
