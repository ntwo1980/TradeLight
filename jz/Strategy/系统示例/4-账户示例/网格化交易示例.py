'''
网格交易示例
需要设置看盘时间的震荡范围、选定网格数量、选定网格大小
'''
import talib
import numpy as np

# p用来设置SetBarInterval的引用根数参数
# 注意：p的值会影响handle_data中len(Close())的结果，在修改p参数时需要注意，
p = 201
p1 = 200

#1. 估计出看盘时间的震荡范围
#2. 选定网格数量
#3. 确定初始仓位
ContractNo = "DCE|Z|Y|MAIN"  # 交易的品种
GridStartPrice = 0 # 网格起始价格
GridStep = 5; # 网格的大小（在handle_data中乘以最小变动价位）
GridLength = 10;  # 网格格数


IncSection = list()      # 用于存储网格值，存储的值类似于[0, 4, 8, 12, 16, 20]
DecSection = list()      # 用于存储网格值，存储的值类似于[0, -4, -8, -12, -16, -20]
IncPriceLevels = list()  # 用于保存大于网格起始价格的网格价格
DecPriceLevels = list()  # 用于保存小于网格起始价格的网格价格

PreLevel = 0   # 记录上一次的网格线

def initialize(context): 
    SetOrderWay(1)   # 发单方式设置为实时发单
    # 设置基准合约，会覆盖界面设置的合约，建议通过界面设置(屏蔽SetBarInterval后则界面添加合约生效)
    SetBarInterval(ContractNo, 'M', 1, 5000, p)
    SetInitCapital(100000)  # 设置初始资金
    # SetActual()  # 未开启实盘运行！
    

def handle_data(context):
    global GridStep
    global IncSection
    global DecSection
    global GridStartPrice
    global IncPriceLevels
    global DecPriceLevels

    global PreLevel

    if len(Close()) < 200:
          return
    
    # 注意：len(Close())的结果会受p的值的影响，再修改p参数时需要注意！！
    if len(Close()) == 200:
        GridStep = GridStep * PriceTick()  # 设置网格大小
        IncSection = [x for x in np.arange(0, GridStep * GridLength / 2 + 0.5 * GridStep, GridStep)] # range函数不包括右边，因此+0.5
        DecSection = [x for x in np.arange(0, -GridStep * GridLength / 2 - 0.5 * GridStep, -GridStep)]
        GridStartPrice = int(talib.MA(Close(), p1)[-1])     # 设置网格起始价格
        IncPriceLevels = [GridStartPrice + x for x in IncSection]  # 设置价格大于网格起始价格的网格值列表
        DecPriceLevels = [GridStartPrice + x for x in DecSection]  # 设置价格小于网格起始价格的网格值列表
        return

    # 绘制网格线
    for i, p in enumerate(IncPriceLevels):
        color = RGB_Yellow() if i == 0 else RGB_Red()
        name = "Price" + str(i)
        PlotNumeric(name, p, color)
    for i, p in enumerate(DecPriceLevels):
        color = RGB_Yellow() if i == 0 else RGB_Red()
        LogInfo(i, p)
        name = "Price" + str(-i)
        PlotNumeric(name, p, color)
    
    delta = Close()[-1] - GridStartPrice
    level = int(delta / GridStep)

    if delta > 0 and delta <= IncSection[-1]:   # 做空
        if PreLevel <0:
            Sell(BuyPosition(), Close()[-1])
            PreLevel = 0
        
        if level > PreLevel:  # 加卖仓
            SellShort(level - PreLevel, Close()[-1])
        elif level < PreLevel:   # 平卖仓
            BuyToCover(PreLevel - level, Close()[-1])
        
        PreLevel = level  # 更新上一次的level值

    elif delta < 0 and delta >= DecSection[-1]:     # 做多
        if PreLevel > 0:
            BuyToCover(SellPosition(), Close()[-1])
            PreLevel = 0

        if level < PreLevel:  # 加买仓
            Buy(PreLevel - level, Close()[-1])

        elif level > PreLevel: # 平买仓
            Sell(level - PreLevel, Close()[-1])

        PreLevel = level  # 更新上一次的level值