########################系统示例不支持修改########################
# 平移布林通道交易
##################################################################
import talib
from EsSeries import *

code1 = 'ZCE|Z|MA|MAIN'
g_params['AvgLen'] = 3 #boll均线周期参数
g_params['Disp'] = 16 #boll平移参数
g_params['SDLen'] = 12 #boll标准差周期参数
g_params['SDev'] = 2 #boll通道倍数参数

AvgVal  = [] #中轨
SDmult = [] #通道距离
DispTop = [] #通道高点
DispBottom = [] #通道低点
#开仓委托
BKID = 0
SKID = 0
#平仓委托
BPID = 0
SPID = 0
#开仓标志
BKFLG = 0
SKFLG = 0
#平仓标志
BPFLG = 0
SPFLG = 0
#开仓委托手数
BKM = 0
SKM = 0
#平仓委托手数
BPM = 0
SPM = 0
#开仓委托价格
BKP = 0
SKP = 0
#平仓委托价格
BPP = 0
SPP = 0

# 策略开始运行时执行该函数一次
def initialize(context): 
    SetBarInterval(code1, 'M', 1, 500)
    SetTriggerType(5)
    SetOrderWay(2)
    SetActual()


# 策略触发事件每次触发时都会执行该函数
def handle_data(context):
    BKDFLG = 0
    SKDFLG = 0
    BPDFLG = 0
    SPDFLG = 0

    global AvgVal
    global SDmult
    global DispTop
    global DispBottom

    global BKID
    global SKID
    global BPID
    global SPID
    global BKFLG
    global SKFLG
    global BPFLG
    global SPFLG
    global BKM
    global SKM
    global BPM
    global SPM
    global BKP
    global SKP
    global BPP
    global SPP

    if(CurrentBar()>=len(DispTop)):
        if(len(DispTop))==0:
            DispTop.append(0)
            DispBottom.append(0)
        else:
            DispTop.append(DispTop[-1])
            DispBottom.append(DispBottom[-1])

    if CurrentBar() < g_params['Disp'] + g_params['AvgLen']:
        return

    #平移boll通道计算
    TPrice = Close()
    AvgVal = talib.MA(TPrice, g_params['AvgLen'])
    SDmult = talib.STDDEV(TPrice, g_params['SDLen']) * g_params['SDev']
    DispTop[-1] = AvgVal[-g_params['Disp'] - 1] + SDmult[-1]
    DispBottom[-1] = AvgVal[-g_params['Disp'] - 1] - SDmult[-1]

    if MarketPosition() == 0:
        if High()[-1] >= DispTop[-2]:
            BKDFLG = 1
        elif Low()[-1] <= DispBottom[-2]:
            SKDFLG = 1
    if MarketPosition() > 0 and BarsSinceEntry() > 0:
        if Low()[-1] <= DispBottom[-2]:
            SPDFLG = 1
    if MarketPosition() < 0 and BarsSinceEntry() > 0:
        if High()[-1] >= DispTop[-2]:
            BPDFLG = 1

    #//------------------------历史发单------------------------//   
    if context.strategyStatus() != 'C':
        if BKDFLG:
            Buy(1, Close()[-1], needCover=False) 
        elif SKDFLG:
            SellShort(1, Close()[-1], needCover=False)
        elif SPDFLG:
            Sell(BuyPosition(), Close()[-1])
        elif BPDFLG:
            BuyToCover(SellPosition(), Close()[-1])
        return
            
    #//------------------------实时处理------------------------//
    if ExchangeStatus(ExchangeName()) != '3':
        return
    N = 1 #下单手数
    ZYM = 3 #止盈价位倍数
    ZSM = 2 #止损价位倍数
    NEWP = Q_Last()#最新价
    BIDP = 0 if Q_BidPrice() is None else Q_BidPrice() #买一价 #买一价
    ASKP = 0 if Q_AskPrice() is None else Q_AskPrice() #卖一价
    RLP = Q_UpperLimit() #涨停价
    FLP = Q_LowLimit() #跌停价
    MINP = PriceTick() #最小变动价位
    BAP = A_BuyAvgPrice() #多头持仓均价
    SAP = A_SellAvgPrice() #空头持仓均价
    BRP = A_BuyPositionCanCover() #多头可用持仓
    SRP = A_SellPositionCanCover() #空头可用持仓
    if ExchangeName() == 'SHFE': #如果是上期所合约
        SH = Enum_ExitToday() #平仓参数
    else: #如果非上期所合约
        SH = Enum_Exit() #平仓参数

    #//------------------------成交判断------------------------//
    if BKFLG == 1:
        if A_OrderStatus(BKID) == Enum_Filled():
            LogInfo("BK信号：买开委托成交！")
            BKFLG = 2 #买开委托已成交
    if SPFLG > 0:
        if A_OrderStatus(SPID) == Enum_Filled(): #如果卖平委托成交
            if SPFLG == 1: #如果是SP信号卖平委托
                LogInfo("SP信号：卖平委托成交！")
            elif SPFLG == 2: #如果是多头止盈卖平委托
                LogInfo("多头止盈：卖平委托成交！")
            elif SPFLG == 3: #如果是多头止损卖平委托
                LogInfo("多头止损：卖平委托成交！")
            BKFLG = 0 #买开标志归0
            SPFLG = 0 #卖平标志归0
    if SKFLG == 1:
        if A_OrderStatus(SKID) == Enum_Filled():
            LogInfo("SK信号：卖开委托成交！");
            SKFLG = 2 #卖开委托已成交
    if BPFLG > 0:
        if A_OrderStatus(BPID) == Enum_Filled():
            if BPFLG == 1: #如果是BP信号买平委托
               LogInfo("BP信号：买平委托成交！")
            elif BPFLG == 2: #如果是空头止盈买平委托
               LogInfo("空头止盈：买平委托成交！")
            elif BPFLG == 3: #如果是空头止损买平委托
               LogInfo("空头止损：买平委托成交！")
            SKFLG = 0 #卖开标志归0
            BPFLG = 0 #买平标志归0
    
    #//------------------------止盈止损------------------------//
    if BKFLG == 2:
        if NEWP >= BAP + ZYM * MINP: #如果满足多头止盈条件
            SPDFLG = 2 #开启多头止盈卖平处理
        elif NEWP <= BAP - ZSM * MINP: #如果满足多头止损条件
            SPDFLG = 3 #开启多头止损卖平处理
    if SKFLG == 2:
        if NEWP <= SAP - ZYM * MINP: #如果满足空头止盈条件
            BPDFLG = 2 #开启空头止盈买平处理
        elif NEWP >= SAP + ZSM * MINP: #如果满足空头止损条件
            BPDFLG = 3 #开启空头止损买平处理
    
    #//------------------------委托处理------------------------//
    if BKDFLG == 1:
        if BKFLG == 0:
            BKM = N #买开委托手数
            BKP = ASKP #买开委托价格
            LogInfo("BK信号：买开委托发出！")
            retCode, BKID = A_SendOrder(Enum_Buy(), Enum_Entry(),BKM,BKP) #发出买开委托
            BKFLG = 1 #已发出买开委托
    if SPDFLG > 0:
        if SPFLG == 0:
            if BRP > 0: #如果有多头可用持仓
                SPM = BRP #卖平委托手数
                SPP = FLP #卖平委托价格
                if SPDFLG == 1: #如果是SP信号卖平
                    LogInfo("SP信号：卖平委托发出！")
                elif SPDFLG == 2: #如果是多头止盈卖平
                    LogInfo("多头止盈：卖平委托发出！")
                elif SPDFLG == 3: #如果是多头止损卖平
                    LogInfo("多头止损：卖平委托发出！")
                retCode, SPID = A_SendOrder(Enum_Sell(), SH,SPM,SPP) #发出卖平委托
                BKFLG = 3 #已多头平仓
                SPFLG = SPDFLG #已发出卖平委托
    if SKDFLG == 1:
        if SKFLG == 0:
            SKM = N #卖开委托手数
            SKP = BIDP #卖开委托价格
            LogInfo("SK信号：卖开委托发出！")
            retCode, SKID = A_SendOrder(Enum_Sell(), Enum_Entry(), SKM, SKP) #发出卖开委托
            SKFLG = 1 #已发出卖开委托
    if BPDFLG > 0:
        if BPFLG == 0:
            if SRP > 0:  #如果有空头可用持仓
                BPM = SRP #买平委托手数
                BPP = RLP #买平委托价格
                if BPDFLG == 1: #如果是BP信号买平
                    LogInfo("BP信号：买平委托发出！")
                elif BPDFLG == 2: #如果是空头止盈买平
                    LogInfo("空头止盈：买平委托发出！")
                elif BPDFLG == 3: #如果是空头止损买平
                    LogInfo("空头止损：买平委托发出！")
                retCode, BPID = A_SendOrder(Enum_Buy(), SH, BPM, BPP) #发出买平委托
                SKFLG = 3 #已空头平仓
                BPFLG = BPDFLG #已发出买平委托