########################系统示例不支持修改########################
# 海龟交易
##################################################################
import talib
from EsTalib import *
import numpy as np

code1 = 'ZCE|Z|MA|MAIN'
g_params['RiskRatio'] = 1 #百分比参数
g_params['ATRLength'] = 20 #平均波动周期 ATR Length
g_params['boLength'] = 20 #短周期 BreakOut Length
g_params['fsLength'] = 55 #长周期 FailSafe Length
g_params['teLength']  = 10 #离市周期 Trailing Exit Length

TrueRange = []
AvgTR = [] #ATR
DonchianHi = [] #唐奇安通道上轨，延后1个Bar
DonchianLo = [] #唐奇安通道下轨，延后1个Bar
fsDonchianHi = [] #唐奇安通道上轨，延后1个Bar，长周期
fsDonchianLo = [] #唐奇安通道下轨，延后1个Bar，长周期
preEntryPrice = [] #前一次开仓的价格
PreBreakoutFailure = [] #前一次突破是否失败

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

# 价格矫正为最小变动价整数倍
def PriceCorrect(src,tick):
    if tick:
        return (int((src+0.5*tick)/tick))*tick
    else:
        src

# 策略开始运行时执行该函数一次
def initialize(context): 
    SetBarInterval(code1, 'D', 1, 200)
    SetTriggerType(5)
    SetOrderWay(2)
    SetActual()


# 策略触发事件每次触发时都会执行该函数
def handle_data(context):
    BKDFLG = 0
    SKDFLG = 0
    BPDFLG = 0
    SPDFLG = 0
    myEntryPrice = 0 #开仓价格
    myExitPrice = 0 #平仓价格

    global TrueRange
    global AvgTR
    global DonchianHi
    global DonchianLo
    global fsDonchianHi
    global fsDonchianLo
    global preEntryPrice
    global PreBreakoutFailure

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

    if(CurrentBar()>=len(DonchianHi)):
        if(len(DonchianHi))==0:
            TrueRange.append(0)
            AvgTR.append(0)
            DonchianHi.append(0)
            DonchianLo.append(0)
            fsDonchianHi.append(0)
            fsDonchianLo.append(0)
            preEntryPrice.append(0)
            PreBreakoutFailure.append(0)
        else:
            TrueRange.append(TrueRange[-1])
            AvgTR.append(AvgTR[-1])
            DonchianHi.append(DonchianHi[-1])
            DonchianLo.append(DonchianLo[-1])
            fsDonchianHi.append(fsDonchianHi[-1])
            fsDonchianLo.append(fsDonchianLo[-1])
            preEntryPrice.append(preEntryPrice[-1])
            PreBreakoutFailure.append(PreBreakoutFailure[-1])

    if CurrentBar() < g_params['fsLength'] + 1:
        return
#//------------------------变量赋值------------------------//
    rangeA = High()[-1] - Low()[-1]
    rangeB = abs(Close()[-2] - High()[-1])
    rangeC = abs(Close()[-2] - Low()[-1])
    TrueRange[-1] = U_Highest([rangeA, rangeB, rangeC], 3)
    #PlotNumeric("TrueRange", TrueRange[-1])
    AvgTR[-1] = U_XAverage(AvgTR, TrueRange, g_params['ATRLength']) #真实波幅平均值
    AN = AvgTR[-2] #一个周期前真实波幅
    if AN == 0:
        return
    TotalEquity = CurrentEquity() #权益
    TurtleUnits = (TotalEquity * g_params['RiskRatio'] / 100) / (AN * ContractUnit()) #开仓数量
    TurtleUnits = int(TurtleUnits) #对小数取整
    DonchianHi[-1] = U_Highest(High()[:-1], g_params['boLength']) #一个周期前boLength周期最高价
    DonchianLo[-1] = U_Lowest(Low()[:-1], g_params['boLength']) #一个周期前boLength周期最低价
    fsDonchianHi[-1] = U_Highest(High()[:-1], g_params['fsLength']) #一个周期前fsLength周期最高价
    fsDonchianLo[-1] = U_Lowest(Low()[:-1], g_params['fsLength']) #一个周期前fsLength周期最低价
    ExitHighestPrice = U_Highest(High()[:-1], g_params['teLength']) #一个周期前teLength周期最高价
    ExitLowestPrice = U_Lowest(Low()[:-1], g_params['teLength']) #一个周期前teLength周期最低价
    #PlotNumeric("DonchianHi", DonchianHi[-1])
    #PlotNumeric("fsDonchianHi", fsDonchianHi[-1])
    #PlotNumeric("ExitLowestPrice", ExitLowestPrice)
    #PlotNumeric("AvgTR", AvgTR[-1])
    if MarketPosition() == 0 and PreBreakoutFailure[-1] == 0:
        if High()[-1] > DonchianHi[-1] and TurtleUnits >= 1:
            #开仓价格取突破上轨+一个价位和最高价之间的较小值，这样能更接近真实情况，并能尽量保证成交
            myEntryPrice = High()[-1] if High()[-1] < DonchianHi[-1] + PriceTick() else DonchianHi[-1] + PriceTick()
            myEntryPrice = Open()[-1] if myEntryPrice < Open()[-1] else myEntryPrice
            preEntryPrice[-1] = myEntryPrice
            SGV = TurtleUnits
            BKDFLG = 1
            PreBreakoutFailure[-1] = 0
        if Low()[-1] < DonchianLo[-1] and TurtleUnits >= 1:
            #开仓价格取突破下轨-一个价位和最低价之间的较大值，这样能更接近真实情况，并能尽量保证成交
            myEntryPrice = Low()[-1] if Low()[-1] > DonchianLo[-1] - PriceTick() else DonchianLo[-1] - PriceTick()
            myEntryPrice = Open()[-1] if myEntryPrice > Open()[-1] else myEntryPrice #大跳空的时候用开盘价代替
            preEntryPrice[-1] = myEntryPrice
            SGV = TurtleUnits
            SKDFLG = 1
            PreBreakoutFailure[-1] = 0
    if MarketPosition() == 0:
        if High()[-1] > fsDonchianHi[-1] and TurtleUnits >= 1:
            #开仓价格取突破上轨+一个价位和最高价之间的较小值，这样能更接近真实情况，并能尽量保证成交
            myEntryPrice = High()[-1] if High()[-1] < fsDonchianHi[-1] + PriceTick() else fsDonchianHi[-1] + PriceTick()
            myEntryPrice = Open()[-1] if myEntryPrice < Open()[-1] else myEntryPrice #大跳空的时候用开盘价代替
            preEntryPrice[-1] = myEntryPrice
            SGV = TurtleUnits
            BKDFLG = 1
            PreBreakoutFailure[-1] = 0
        if Low()[-1] < fsDonchianLo[-1] and TurtleUnits >= 1:
            #开仓价格取突破下轨-一个价位和最低价之间的较大值，这样能更接近真实情况，并能尽量保证成交
            myEntryPrice = Low()[-1] if Low()[-1] > fsDonchianLo[-1] - PriceTick() else fsDonchianLo[-1] - PriceTick()
            myEntryPrice = Open()[-1] if myEntryPrice > Open()[-1] else myEntryPrice #大跳空的时候用开盘价代替
            preEntryPrice[-1] = myEntryPrice
            SGV = TurtleUnits
            SKDFLG = 1
            PreBreakoutFailure[-1] = 0
    if MarketPosition() > 0 or BKDFLG:
        if Low()[-1] < ExitLowestPrice:
            myExitPrice = Low()[-1] if Low()[-1] > ExitLowestPrice - PriceTick() else ExitLowestPrice - PriceTick()
            myExitPrice = Open()[-1] if myExitPrice > Open()[-1] else myExitPrice #大跳空的时候用开盘价代替
            SGV = 1
            SPDFLG = 1 #数量用0的情况下将全部平仓
        else:
            if preEntryPrice[-1] and TurtleUnits >= 1:
                if Open()[-1] >= preEntryPrice[-1] + 0.5 * AN:
                    if BKDFLG: 
                        preEntryPrice[-1] = Open()[-1]
                    else:
                        myEntryPrice = Open()[-1]
                        preEntryPrice[-1] = myEntryPrice
                    SGV = TurtleUnits
                    BKDFLG = 1
                if High()[-1] >= preEntryPrice[-1] + 0.5 * AN:
                    if BKDFLG:
                        preEntryPrice[-1] = preEntryPrice[-1] + 0.5 * AN
                    else:
                        myEntryPrice = preEntryPrice[-1] + 0.5 * AN;#  
                        preEntryPrice[-1] = myEntryPrice
                    SGV = TurtleUnits
                    BKDFLG = 1
            if Low()[-1] <= preEntryPrice[-1] - 2 * AN:
                myExitPrice = preEntryPrice[-1] - 2 * AN;
                SGV = 1
                SPDFLG = 1 #数量用0的情况下将全部平仓
                PreBreakoutFailure[-1] = 1
    elif MarketPosition() < 0:
        if High()[-1] > ExitHighestPrice:
            myExitPrice = High()[-1] if High()[-1] < ExitHighestPrice + PriceTick() else ExitHighestPrice + PriceTick()
            myExitPrice = Open()[-1] if myExitPrice < Open()[-1] else myExitPrice #大跳空的时候用开盘价代替
            SGV = 1
            BPDFLG = 1
        else:
            if preEntryPrice[-1] and TurtleUnits >= 1:
                if Open()[-1] <= preEntryPrice[-1] - 0.5 * AN:
                    if SKDFLG: 
                        preEntryPrice[-1] = Open()[-1]
                    else:
                        myEntryPrice = Open()[-1]
                        preEntryPrice[-1] = myEntryPrice
                    SGV = TurtleUnits
                    SKDFLG = 1
                if Low()[-1] <= preEntryPrice[-1] - 0.5 * AN:
                    if SKDFLG: 
                        preEntryPrice[-1] = preEntryPrice[-1] - 0.5 * AN
                    else:
                        myEntryPrice = preEntryPrice[-1] - 0.5 * AN;
                        preEntryPrice[-1] = myEntryPrice
                    SGV = TurtleUnits
                    SKDFLG = 1
            if High()[-1] >= preEntryPrice[-1] + 2 * AN:
                myExitPrice = preEntryPrice[-1] + 2 * AN;
                SGV = 1
                BPDFLG = 1
                PreBreakoutFailure[-1] = 1
    #//------------------------历史发单------------------------//   
    if context.strategyStatus() != 'C':
        if BKDFLG:#多头建仓
            Buy(1, PriceCorrect(myEntryPrice,PriceTick()), needCover=False) 
        elif SKDFLG:#空头建仓
            SellShort(1, PriceCorrect(myEntryPrice,PriceTick()), needCover=False)
        elif SPDFLG:
            Sell(BuyPosition(), PriceCorrect(myExitPrice,PriceTick()))
        elif BPDFLG:
            BuyToCover(SellPosition(), PriceCorrect(myExitPrice,PriceTick()))
        return

	#//------------------------实时发单------------------------//  
	#实时阶段调用的是A函数，MarketPosition需要替换成A_TotalPosition

    #//------------------------变量赋值------------------------//
    BRP = A_BuyPositionCanCover() #多头可用持仓
    SRP = A_SellPositionCanCover() #空头可用持仓
    if ExchangeName() == 'SHFE': #如果是上期所合约
        SH = Enum_ExitToday() #平仓参数
    else: #如果非上期所合约
        SH = Enum_Exit() #平仓参数
    #//------------------------信号处理------------------------//
    if BKFLG == 1: #如果有买开委托
        if A_OrderStatus(BKID) == Enum_Filled(): #如果买开委托成交
            LogInfo("BK信号：买开委托成交！")
            BKFLG = 0 #买开标志归0
    if SPFLG == 1: #如果有卖平委托
        if A_OrderStatus(SPID) == Enum_Filled(): #如果卖平委托成交
            LogInfo("SP信号：卖平委托成交！")
            SPFLG = 0 #卖平标志归0
    if SKFLG == 1: #如果有卖开委托
        if A_OrderStatus(SKID) == Enum_Filled(): #如果卖开委托成交
            LogInfo("SK信号：卖开委托成交！")
            SKFLG = 0 #卖开标志归0
    if BPFLG == 1: #如果有买平委托
        if A_OrderStatus(BPID) == Enum_Filled(): #如果买平委托成交
            LogInfo("BP信号：买平委托成交！")
            BPFLG = 0 #买平标志归0

    #//------------------------委托处理------------------------//
    if BKDFLG == 1: #如果已开启买开处理
        if BKFLG == 0: #如果没有买开委托
            BKM = SGV #买开委托手数
            BKP = PriceCorrect(myEntryPrice,PriceTick()) #买开委托价格
            LogInfo("BK信号：买开委托发出！")
            retCode, BKID = A_SendOrder(Enum_Buy(),Enum_Entry(),BKM,BKP) #发出买开委托
            BKFLG = 1; #已发出买开委托
    if SPDFLG == 1: #如果已开启卖平处理
        if SPFLG == 0: #如果没有卖平委托1
            if BRP > 0: #如果有多头可用持仓
                SPM = BRP #卖平委托手数
                SPP = PriceCorrect(myExitPrice,PriceTick()) #卖平委托价格
                LogInfo("SP信号：卖平委托发出！")
                retCode, SPID = A_SendOrder(Enum_Sell(),SH,SPM,SPP) #发出卖平委托
                SPFLG = 1 #已发出卖平委托
    if SKDFLG == 1: #如果已开启卖开处理
        if SKFLG == 0: #如果没有卖开委托
            SKM = SGV #卖开委托手数
            SKP = PriceCorrect(myEntryPrice,PriceTick()) #卖开委托价格
            LogInfo("SK信号：卖开委托发出！")
            retCode, SKID = A_SendOrder(Enum_Sell(), Enum_Entry(), SKM, SKP) #发出卖开委托
            SKFLG = 1 #已发出卖开委托
    if BPDFLG == 1: #如果已开启买平处理
        if BPFLG == 0: #如果没有买平委托
            if SRP > 0: #如果有空头可用持仓
                BPM = SRP #买平委托手数
                BPP = PriceCorrect(myExitPrice,PriceTick()) #买平委托价格
                LogInfo("BP信号：买平委托发出！")
                retCode, BPID = A_SendOrder(Enum_Buy(),SH,BPM,BPP) #发出买平委托
                BPFLG = 1 #已发出买平委托