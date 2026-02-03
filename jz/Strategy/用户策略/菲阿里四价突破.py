######################## 菲阿里四价突破策略 ########################
# 使用昨日最高价、最低价作为突破信号
# 今日开盘价作为动态止损基准
# 尾盘 cover_min 分钟强制平仓
##################################################################
import math

contractNo = "ZCE|Z|AP|MAIN"  # 订阅的合约编号
cover_min = 10                # 当日闭市前10分钟开始清仓
qty = 1                       # 单笔开仓量

curr_date = -1                # 当前交易日缓存
today_open = 0                # 今日开盘价

def initialize(context): 
    SetBarInterval(contractNo, "M", 1, 200)  
    SetOrderWay(2)            # K线稳定后发单
    SetTriggerType(3, 1000)   # 每秒触发一次（用于尾盘追价）

def min2float(val):
    return (math.ceil(val / 60) * 40 + val) * 0.0001  

def handle_data(context):    
    global curr_date, today_open
    
    trade_date = TradeDate()
    
    # 换日初始化
    if curr_date != trade_date:
        curr_date = trade_date
        today_open = Open()[-1]  # 今日第一根K线的开盘价即为今日开盘价

    # 获取当前时间与交易时段
    tim = Time()
    count = GetSessionCount()
    if count <= 0:
        LogError('时间节点获取错误', context.contractNo())
        return 
        
    op_tim = GetSessionStartTime(index=0)
    cl_tim = GetSessionEndTime(index=count - 1)
    
    # 处理跨日时间（如夜盘）
    if op_tim > cl_tim:
        if tim <= cl_tim:
            tim += 0.24
        cl_tim += 0.24  

    # === 尾盘清仓逻辑（保留原机制）===
    if cl_tim - min2float(cover_min) <= tim <= cl_tim:       
        b_qty = BuyPosition()
        s_qty = SellPosition()
        if b_qty > 0:
            Sell(b_qty, Close()[-1])
        if s_qty > 0:
            BuyToCover(s_qty, Close()[-1])

        # 实盘追价：每秒撤单重发
        if context.triggerType() == 'C':
            DeleteAllOrders()
            b_qty = A_BuyPosition()
            s_qty = A_SellPosition()
            if b_qty > 0:
                A_SendOrder(Enum_Sell(), Enum_ExitToday(), b_qty, Q_BidPrice())
            if s_qty > 0:
                A_SendOrder(Enum_Buy(), Enum_ExitToday(), s_qty, Q_AskPrice())
        return  # 清仓时段不执行其他逻辑

    # 定时器触发但非主逻辑时段，跳过
    if context.triggerType() == 'C':
        return

    # === 确保至少有两根K线（含昨日）===
    if len(High()) < 2:
        return

    # 获取昨日高、低
    yesterday_high = High()[-2]
    yesterday_low = Low()[-2]

    # === 开仓逻辑：突破昨日高低点 ===
    current_price = Close()[-1]

    # 做多：突破昨日高
    if current_price > yesterday_high and BuyPosition() == 0 and SellPosition() == 0:
        Buy(qty, Open()[-1], contractNo, False)

    # 做空：跌破昨日低
    elif current_price < yesterday_low and BuyPosition() == 0 and SellPosition() == 0:
        SellShort(qty, Open()[-1], contractNo, False)

    # === 动态止损：反向穿过今日开盘价则平仓 ===
    long_pos = BuyPosition()
    short_pos = SellPosition()

    if long_pos > 0 and current_price <= today_open:
        Sell(long_pos, Close()[-1])  # 平多

    if short_pos > 0 and current_price >= today_open:
        BuyToCover(short_pos, Close()[-1])  # 平空

    # === 绘图 ===
    PlotNumeric('yesterday_high', yesterday_high, RGB_Red())
    PlotNumeric('yesterday_low', yesterday_low, RGB_Blue())
    PlotNumeric('today_open', today_open, RGB_Green())
    PlotNumeric("profit", NetProfit() + FloatProfit() - TradeCost(), 0xFF00FF, False)