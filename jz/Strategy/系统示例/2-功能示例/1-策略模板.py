########################系统示例不支持修改########################
# EQuant策略的基本结构：模块导入、策略参数、全局变量、四个接口函数
# 基本的python语法：变量使用，变量赋值、全局变量、数组操作、list访问、字典使用、条件语句、循环语句
##################################################################

# 导入功能模块
import talib
import numpy as np

# 策略参数
g_params['p1'] = 20
g_params['p2'] = 40
g_params['qty'] = 5

# 全局变量
ord_bar = 0

# 策略初始化函数，策略开始运行时一次
def initialize(context): 
    # K线完成时触发
    SetOrderWay(2)
    # 订阅历史K线
    SetBarInterval('ZCE|Z|SR|MAIN', 'M', 1, 200)

# 策略执行函数，策略触发事件每次触发时都会调用一次
def handle_data(context):
    # 全局变量, 若要将修改后的变量值保存下来，则需要用global在函数内对变量进行标记
    global ord_bar

    # 周期数判断
    if CurrentBar() < g_params['p2']:
        return

    # 设置多种触发方式分类处理
    if context.triggerType() != "H" and context.triggerType() != "K":  # 非K线触发
        LogInfo("触发事件类型：",context.triggerType())
        return

    # 策略参数的使用
    ma1 = talib.MA(Close(), g_params['p1'])    
    ma2 = talib.MA(Close(), g_params['p2'])

    # 策略交易
    if ma1[-1] > ma2[-1] and MarketPosition() <= 0:
        Buy(g_params['qty'], Close()[-1])
    elif ma1[-1] < ma2[-1] and MarketPosition() >= 0:
        SellShort(g_params['qty'], Close()[-1])

    # 绘制策略线
    PlotNumeric('ma1', ma1[-1], 0xff0000)
    PlotNumeric('ma2', ma2[-1], 0x0000ff)
    # 盈亏曲线, 副图展示
    PlotNumeric('profit', NetProfit() - TradeCost(), RGB_Purple(), False)

# 历史回测阶段结束时执行该函数一次
def hisover_callback(context):    
    # 清空所有历史持仓
    if BuyPosition() > 0:
        Sell(BuyPosition(), Close()[-1])
    if SellPosition() > 0:
        BuyToCover(SellPosition(), Close()[-1])

# 策略退出前执行该函数一次
def exit_callback(context):
    LogInfo("策略退出")