########################系统示例不支持修改########################
# 参数优化示例
# 备注:  1、请保证策略文件名*.py不要重复，避免提取参数时出错
#        2、新建文件夹时，需要重启客户端，才能提取到参数（受限于Python不能重复初始化原因）
#        3、提取参数仅支持整型和浮点型，不支持字符串等类型
# 操作步骤： 在运行策略列表右键>>参数优化菜单>>设置步长和最小最大值>>设置参数关系>>运行
##################################################################
import talib

g_params['fast'] = 12 # 快周期
g_params['slow'] = 26 # 慢周期
g_params['back'] = 9  # dea周期

qty = 1   # 下单量
macd_dx = 0.01 #macd阀值

def initialize(context): 
    # 设置K线稳定后发单
    SetOrderWay(2)
    # 设置基准合约，会覆盖界面设置的合约，建议通过界面设置(屏蔽SetBarInterval后则界面添加合约生效)
    SetBarInterval('ZCE|Z|SR|MAIN', 'M', 1, 200, g_params['slow'] + g_params['back'] - 1) 

def handle_data(context):
    # 等待数据就绪，否则计算结果为异常值
    if CurrentBar() < g_params['slow'] + g_params['back'] - 1:
        return

    # 计算MACD   
    diff, dea, macd = talib.MACD(Close(), g_params['fast'], g_params['slow'], g_params['back'])

    # 突破下单
    if MarketPosition() <= 0 and macd[-1] > macd_dx:
        Buy(qty, Close()[-1]) 
    elif MarketPosition() >= 0 and macd[-1] < -macd_dx:
        SellShort(qty, Close()[-1]) 

    # 绘制MACD曲线    
    PlotStickLine('macd', 0, macd[-1], RGB_Red() if macd[-1] > 0 else RGB_Blue(), False, False) 
    PlotNumeric('diff', diff[-1], RGB_Red(), False, False)
    PlotNumeric('dea', dea[-1], RGB_Blue(), False, False) 
    # 绘制盈亏曲线
    PlotNumeric("profit", NetProfit() + FloatProfit() - TradeCost(), 0xcccccc, False, True) 
