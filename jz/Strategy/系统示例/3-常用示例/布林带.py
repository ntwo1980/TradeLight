########################系统示例不支持修改########################
# 布林带策略
# 根据布林带计算出高中低三个通道，较好的体现了行情的盘整和突破
# 根据行情时段与特点灵活运用会有不错的效果
##################################################################
import talib

p = 8    # 计算周期
qty = 1  # 下单量

def initialize(context): 
    # 设置K线稳定后发单
    SetOrderWay(2) 
    # 设置基准合约，会覆盖界面设置的合约，建议通过界面设置(屏蔽SetBarInterval后则界面添加合约生效)
    SetBarInterval('ZCE|Z|SR|MAIN', 'M', 1, 200, p) 
    
def handle_data(context):  
    # 等待数据就绪，否则计算果结为异常值
    if CurrentBar() < p:
        return
  
    # 计算布林带高中低点
    upp, mid, low = talib.BBANDS(Close(), p, 2, 2)
    
    # 低买高卖
    if MarketPosition() <= 0 and Close()[-1] < low[-1]: 
        Buy(qty, Close()[-1])
    elif MarketPosition() >= 0 and Close()[-1] > upp[-1]:
        SellShort(qty, Close()[-1])

    # 绘制布林带曲线
    PlotNumeric('upp', upp[-1], RGB_Red())
    PlotNumeric('mid', mid[-1], RGB_Blue())
    PlotNumeric('low', low[-1], RGB_Green())
    # 绘制盈亏曲线
    PlotNumeric("profit", NetProfit() + FloatProfit() - TradeCost(), 0xFF00FF, False) 

