########################系统示例不支持修改########################
# 双均线策略
# 历史阶段用了buy、sell进行测试
# 实盘阶段用了A函数进行更精细的下单控制
##################################################################
import talib
import time

p1 = 5  # 快周期
p2 = 20 # 慢周期
qty = 1
def initialize(context):
    # 设置K线稳定后发单
    SetOrderWay(2)  
    # 设置基准合约，会覆盖界面设置的合约，建议通过界面设置(屏蔽SetBarInterval后则界面添加合约生效)
    SetBarInterval('ZCE|Z|SR|MAIN', 'M', 1, 200, p2) 
    # 设置实盘运行
    SetActual()    
    
# 历史测回执行逻辑
def his_trigger(ma1, ma2):
    if ma1[-1] > ma2[-1] and MarketPosition() <= 0:
        Buy(qty, Close()[-1])
    elif ma1[-1] < ma2[-1] and MarketPosition() >= 0:
        SellShort(qty, Close()[-1])
    
# 实盘阶段执行逻辑
def tim_trigger(ma1, ma2):
    # 判断交易账号是否准备就绪 TODO
    if ma1[-1] > ma2[-1] and A_TotalPosition() <= 0:
        prc = min(Q_AskPrice() + PriceTick(), Q_UpperLimit()) # 对盘超价
        if A_TotalPosition() < 0: 
            A_SendOrder(Enum_Buy(), Enum_ExitToday(), A_SellPosition(), prc) # 平空仓
        A_SendOrder(Enum_Buy(), Enum_Entry(), qty, prc) # 开多仓 
    elif ma1[-1] < ma2[-1] and A_TotalPosition() >= 0:
        prc = max(Q_BidPrice() - PriceTick(), Q_LowLimit())
        if A_TotalPosition() > 0: 
            A_SendOrder(Enum_Sell(), Enum_ExitToday(), A_BuyPosition(), prc) # 平多仓
        A_SendOrder(Enum_Sell(), Enum_Entry(), qty, prc)  # 开空仓 

def handle_data(context):
    if CurrentBar() < p2:
        return;
        
    ma1 = talib.MA(Close(), p1)
    ma2 = talib.MA(Close(), p2)  
    
    his = context.strategyStatus() == 'H'
    if his:
        his_trigger(ma1, ma2) 
    else: 
        tim_trigger(ma1, ma2) 
    
    PlotNumeric("ma1", ma1[-1], 0xFF0000)
    PlotNumeric("ma2", ma2[-1], 0x00aa00) 
    fit = NetProfit() + FloatProfit() - TradeCost() if his else A_CoverProfit() + A_ProfitLoss() - A_Cost()
    PlotNumeric("fit", fit, 0x0000FF, False)
