########################系统示例不支持修改########################
# MACD交易-历史阶段使用BuySell函数--实时阶段使用A函数
# MACD指标是所有技术指标里最经典的一个技术指标，
# 正确运用这个指标，通过结合K线、行情走势等，基本上就可以达到较好地买卖效果。
##################################################################
import talib
from EsTalib import *

code1 = 'ZCE|Z|SR|MAIN'
g_params['FastMA'] = 4 #MACD短周期值
g_params['SlowMA'] = 10 #MACD长周期值
g_params['AvgMA'] = 16 #MACD慢线周期值
g_params['ATRLen'] = 10 #ATR周期值
g_params['EATRPcnt'] = 1 #入场通道波动率过滤数值
g_params['XATRPcnt'] = 1 #出场通道波动率过滤数值

#平仓委托
BPID = 0
SPID = 0
#平仓标志
BPFLG = 0
SPFLG = 0
#平仓委托手数
BPM = 0
SPM = 0
#平仓委托价格
BPP = 0
SPP = 0
#开仓委托
BKID = []
SKID = []
#开仓标志
BKFLG = []
SKFLG = []
#开仓委托手数
BKM = []
SKM = []
#开仓委托价格
BKP = []
SKP = []

#序列
TrueRange = []
AATR = [] #ATR
UpTrend = []
DnTrend = [] #空头趋势变量
BuySetup = [] #买入控制条件
SellSetup = [] #卖出控制条件
CTrendLow = [] #普通数值型序列变量
CTrendHigh = [] #普通数值型序列变量
SignalFlag = [] #普通数值型序列变量
UpperBand = [] #买入触发价
LowerBand = [] #卖出触发价
ExitBand = [] #出场触发价

def initialize(context): 
    SetBarInterval(code1, 'D', 1, 2000)
    SetTriggerType(5)
    SetOrderWay(2)
    SetActual()
    global BKID
    global SKID
    global BKFLG
    global SKFLG
    global BKM
    global SKM
    global BKP
    global SKP
    BKID = [0,0,0]
    SKID = [0,0,0]
    BKFLG = [0,0,0]
    SKFLG = [0,0,0]
    BKM = [0,0,0]
    SKM = [0,0,0]
    BKP = [0,0,0]
    SKP = [0,0,0]

def handle_data(context):
    global BPID
    global SPID
    global BPFLG
    global SPFLG
    global BPM
    global SPM
    global BPP
    global SPP
    global BKID
    global SKID
    global BKFLG
    global SKFLG
    global BKM
    global SKM
    global BKP
    global SKP

    BKDFLG = 0 #买开处理标志
    SKDFLG = 0 #卖开处理标志
    BPDFLG = 0 #买平处理标志
    SPDFLG = 0 #卖平处理标志
    
    global TrueRange
    global AATR
    global UpTrend
    global DnTrend
    global BuySetup
    global SellSetup
    global CTrendLow
    global CTrendHigh
    global SignalFlag
    global UpperBand
    global LowerBand
    global ExitBand
    
    #序列初始化和更新逻辑（模拟序列变量处理）
    if(CurrentBar()>=len(UpTrend)):
        if(len(UpTrend))==0:
            TrueRange.append(0)
            AATR.append(0)
            UpTrend.append(0)
            DnTrend.append(0)
            BuySetup.append(0)
            SellSetup.append(0)
            CTrendLow.append(0)
            CTrendHigh.append(0)
            SignalFlag.append(0)
            UpperBand.append(0)
            LowerBand.append(0)
            ExitBand.append(0)
        else:
            TrueRange.append(TrueRange[-1])
            AATR.append(AATR[-1])
            UpTrend.append(UpTrend[-1])
            DnTrend.append(DnTrend[-1])
            BuySetup.append(BuySetup[-1])
            SellSetup.append(SellSetup[-1])
            CTrendLow.append(CTrendLow[-1])
            CTrendHigh.append(CTrendHigh[-1])
            SignalFlag.append(SignalFlag[-1])
            UpperBand.append(UpperBand[-1])
            LowerBand.append(LowerBand[-1])
            ExitBand.append(ExitBand[-1])

    if CurrentBar() < g_params['AvgMA']+g_params['SlowMA']-1:
        return

    MACDLine = talib.EMA(Close(),g_params['FastMA'])- talib.EMA(Close(),g_params['SlowMA']) #计算MACD快线
    SignalLine = talib.EMA(MACDLine, g_params['AvgMA']) #计算MACD慢线
    #AATR = talib.ATR(High(), Low(), Close(), g_params['ATRLen']) #计算ATR波动率
    rangeA = High()[-1] - Low()[-1]
    rangeB = abs(Close()[-2] - High()[-1])
    rangeC = abs(Close()[-2] - Low()[-1])
    TrueRange[-1] = U_Highest([rangeA, rangeB, rangeC], 3)
    AATR[-1] = U_Average(TrueRange, g_params['ATRLen']) #真实波幅平均值

    ZeroLine=[0 for i in range(0, len(SignalLine))]#零轴
    
    #Macd离差值（DIF）、离差平均值（DEA）
    PlotNumeric('DIF', MACDLine[-1], RGB_Red(), False, False)
    PlotNumeric('DEA', SignalLine[-1], RGB_Blue(), False, False) 
   
    #上穿下穿判断
    Con1 = CrossOver(SignalLine,ZeroLine) #慢线上穿零轴
    if Con1 == 1: #当慢线上穿零轴时候,定义为多头趋势
        UpTrend[-1] = 1
        SignalFlag[-1] = 0
        DnTrend[-1] = 0
        SellSetup [-1] = 0
    Con2 = CrossUnder(SignalLine,ZeroLine) #慢线下穿零轴
    if Con2 == 1: #当慢线下穿零轴时候,定义为空头趋势
        UpTrend[-1] = 0
        BuySetup[-1] = 0
        SignalFlag[-1] = 0
        DnTrend[-1] = 1

    #入场条件判断
    if UpTrend[-1] == 1: #多头趋势时记录当前最低价以及设置入场条件
        if SignalFlag[-1] == 0:
            BuySetup[-1] = 1
            CTrendLow[-1] = Low()[-1]
        if MACDLine[-1] < SignalLine[-1] and Low()[-1] < CTrendLow[-2]: #MACD均线空头排列时候,且当前价格更低时更新最低价
            CTrendLow[-1] = Low()[-1]
    if DnTrend[-1] == 1:
        if SignalFlag[-1] == 0: #空头趋势时记录当前最低价以及设置入场条件
            SellSetup[-1] = 1
            CTrendHigh[-1] = High()[-1]
        if MACDLine[-1] > SignalLine[-1] and High()[-1] > CTrendHigh[-2]: #当MACD均线多头排列时候,且当前价格更高时更新最高价
            CTrendHigh[-1] = High()[-1]

    #更新波动率通道上下轨     
    if BuySetup[-2] == 1 and BuySetup[-3] == 0: #多头满足入场条件设定入场价格以及出场价格
        UpperBand[-1] = Close()[-2] + (g_params['EATRPcnt'] * AATR[-2])
        ExitBand[-1] = Close()[-2] - (g_params['XATRPcnt'] * AATR[-2])
  
    if SellSetup[-2] == 1 and SellSetup[-3] == 0: #空头满足入场条件设定入场价格以及出场价格
        LowerBand[-1] = Close()[-2] - (g_params['EATRPcnt'] * AATR[-2])
        ExitBand[-1] = Close()[-2] + (g_params['XATRPcnt'] * AATR[-2])

    #波动率进场通道上轨、下轨
    PlotNumeric('UpperBand', UpperBand[-1], RGB_Gray(), True, False) 
    PlotNumeric('LowerBand', LowerBand[-1], RGB_Yellow(), True, False) 

    #多头系统入场
    if BuySetup[-2] == 1 and MarketPosition() == 0: #做多
        if High()[-1] >= UpperBand[-1]:
            BKDFLG = 1
            BuySetup[-1] = 0 #持有多单时不再满足入场条件
            SignalFlag[-1] = 1
   
    #空头系统入场
    if SellSetup[-2] == 1 and MarketPosition() == 0: #做空
        if Low()[-1] <= LowerBand[-1]:
            SKDFLG = 1
            SellSetup[-1] = 0 #持有空单时不再满足入场条件
            SignalFlag[-1] = 1

    #多头系统出场
    if MarketPosition() > 0 and BarsSinceEntry() > 0:
        if DnTrend[-1] == 1:
            SPDFLG = 1
        elif Low()[-1] <= CTrendLow[-1] - PriceTick() and CTrendLow[-1] - PriceTick() >= ExitBand[-1]:
            SPDFLG = 1
        elif Low()[-1] <= ExitBand[-1]:
            SPDFLG = 1
   
    #空头系统出场
    if MarketPosition() < 0 and BarsSinceEntry() > 0:
        if UpTrend[-1] == 1:
            BPDFLG = 1
        elif High()[-1] >= CTrendHigh[-1] + PriceTick() and CTrendHigh[-1] + PriceTick() <= ExitBand[-1]:
            BPDFLG = 1
        elif High()[-1] >= ExitBand[-1]:
            BPDFLG = 1

	#//------------------------历史发单------------------------//
    if context.strategyStatus() != 'C':
        if BKDFLG:#多头建仓
            Buy(1, Close()[-1], code1,False) 
        elif SKDFLG:#空头建仓
            SellShort(1, Close()[-1], code1,False)   
        elif BPDFLG:
            BuyToCover(1, Close()[-1], code1)
        elif SPDFLG:
            Sell(1, Close()[-1], code1)
        return

	#//------------------------实时处理------------------------//
	#内盘交易账号登录ExchangeStatus有效，外盘需要屏蔽市场状态判断
	#实时阶段调用的是A函数，MarketPosition需要替换成A_TotalPosition
    if ExchangeStatus(ExchangeName()) != '3':
        return

	#//------------------------变量赋值------------------------//
    N = 2 #下单手数
    FN = 3 #分批批数
    BIDP = 0 if Q_BidPrice() is None else Q_BidPrice() #买一价
    ASKP = 0 if Q_AskPrice() is None else Q_AskPrice() #卖一价
    RLP = Q_UpperLimit() #涨停价
    FLP = Q_LowLimit() #跌停价
    BRP = A_BuyPositionCanCover() #多头可用持仓
    SRP = A_SellPositionCanCover() #空头可用持仓
    if ExchangeName() == 'SHFE': #如果是上期所合约
        SH = Enum_ExitToday() #平仓参数
    else: #如果非上期所合约
        SH = Enum_Exit() #平仓参数
#//------------------------成交判断------------------------//
    for X in range(0,FN):
        if BKFLG[X] == 1: #如果有买开委托
            if A_OrderStatus(BKID[X]) == Enum_Filled(): #如果买开委托成交
                LogInfo("BK信号：买开委托成交！")
                BKFLG[X] = 0 #买开标志归0
    if SPFLG == 1: #如果有卖平委托
        if A_OrderStatus(SPID) == Enum_Filled(): #如果卖平委托成交
            LogInfo("SP信号：卖平委托成交！");
            SPFLG = 0 #卖平标志归0
    for X in range(0,FN):
        if SKFLG[X] == 1: #如果有卖开委托
            if A_OrderStatus(SKID[X]) == Enum_Filled(): #如果卖开委托成交
               LogInfo("SK信号：卖开委托成交！")
               SKFLG[X] = 0 #卖开标志归0
    if BPFLG == 1: #如果有买平委托
        if A_OrderStatus(BPID) == Enum_Filled(): #如果买平委托成交
            LogInfo("BP信号：买平委托成交！");
            BPFLG = 0 #买平标志归0

#//------------------------委托处理------------------------//
    if BKDFLG == 1:
        for X in range(0, FN):
            if BKFLG[X] == 0: #如果没有买开委托
                BKM[X] = N #买开委托手数
                BKP[X] = ASKP #买开委托价格
                LogInfo("BK信号：买开委托发出！")
                BKID[X],_ = A_SendOrder(Enum_Buy(),Enum_Entry(),BKM[X],BKP[X]) #发出买开委托
                BKFLG[X] = 1
    if SPDFLG == 1:
        if SPFLH == 0:
            if BRP > 0:
                SPM = BRP #卖平委托手数
                SPP = FLP #卖平委托价格
                LogInfo("SP信号：卖平委托发出！")
                SPID = A_SendOrder(Enum_Sell(),SH,SPM,SPP) #发出卖平委托
                SPFLG = 1 #已发出卖平委托
    if SKDFLG == 1:
        for X in range(0,FN):
            if SKFLG[X] == 0: #如果没有卖开委托
                SKM[X] = N #卖开委托手数
                SKP[X] = BIDP #卖开委托价格
                LogInfo("SK信号：卖开委托发出！")
                SKID[X],s = A_SendOrder(Enum_Sell(), Enum_Entry(), SKM[X], SKP[X]) #发出卖开委托
                SKFLG[X] = 1 #已发出卖开委托
    if BPDFLG == 1:
        if BPFLG == 0:
            if SRP > 0:
                BPM = SRP #买平委托手数
                BPP = RLP #买平委托价格
                LogInfo("BP信号：买平委托发出！")
                BPID = A_SendOrder(Enum_Buy(), SH, BPM, BPP) #发出买平委托
                BPFLG = 1 #已发出买平委托