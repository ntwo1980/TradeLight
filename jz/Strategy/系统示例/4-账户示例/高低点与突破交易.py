########################系统示例不支持修改########################
# 高低点与突破交易
##################################################################
import talib
import numpy as np

code1 = 'ZCE|Z|TA|MAIN'
g_params['AvgLen'] = 20
g_params['AbsDisp'] = 5
g_params['ExitBar'] = 5

UpperAvg = [] #通道上轨
LowerAvg = [] #通道下轨
ExitAvg = [] #通道中轨
MedianPrice = [] #K线中点
Range1 = [] #K线振幅
RangeLeadB = []
RangeLeadS = []

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
#开仓撤单标志
BKDEL = 0
SKDEL = 0
#平仓撤单标志
BPDEL = 0
SPDEL = 0
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
#开仓委托时间
BKT = 0
SKT = 0
#平仓委托时间
BPT = 0
SPT = 0

# 策略开始运行时执行该函数一次
def initialize(context): 
    SetBarInterval(code1, 'M', 1, 300)
    SetTriggerType(5)
    SetOrderWay(2)
    SetActual()


# 策略触发事件每次触发时都会执行该函数
def handle_data(context):
    BKDFLG = 0
    SKDFLG = 0
    BPDFLG = 0
    SPDFLG = 0
    BRP = 0
    SRP = 0
    
    global BKID
    global SKID

    global UpperAvg
    global LowerAvg
    global ExitAvg
    global MedianPrice
    global Range1
    global RangeLeadB
    global RangeLeadS

    global BPID
    global SPID
    global BKFLG
    global SKFLG
    global BPFLG
    global SPFLG
    global BKDEL
    global SKDEL
    global BPDEL
    global SPDEL
    global BKM
    global SKM
    global BPM
    global SPM
    global BKP
    global SKP
    global BPP
    global SPP
    global BKT
    global SKT
    global BPT
    global SPT

    if(CurrentBar()>=len(Range1)):
        if(len(Range1))==0:
            Range1.append(0.0)
            MedianPrice.append(0.0)
            RangeLeadB.append(False)
            RangeLeadS.append(False)
        else:
            Range1.append(Range1[-1])
            MedianPrice.append(MedianPrice[-1])
            RangeLeadB.append(RangeLeadB[-1])
            RangeLeadS.append(RangeLeadS[-1])

    if CurrentBar() < g_params['AvgLen']:
        return

    Range1[-1] = High()[-1] - Low()[-1] #K线振幅
    UpperAvg = talib.MA(High()[:-g_params['AbsDisp']], g_params['AvgLen']) #计算AvgLen周期内，AbsDisp周期前高点的均值
    LowerAvg = talib.MA(Low()[:-g_params['AbsDisp']], g_params['AvgLen']) #计算AvgLen周期内，AbsDisp周期前低点的均值
    MedianPrice[-1] = (High()[-1] + Low()[-1]) * 0.5 #计算K线中点
    ExitAvg = talib.MA(np.array(MedianPrice[:-g_params['AbsDisp']]), g_params['AvgLen']) #计算AvgLen周期内，AbsDisp周期前K线中点的均值
    RangeLeadB[-1] = MedianPrice[-1] > High()[-2] and Range1[-1] > Range1[-2] #当根K线满足中点大于前一根K线高点且振幅大于上一根振幅
    RangeLeadS[-1] = MedianPrice[-1] < Low()[-2] and Range1[-1] > Range1[-2] #当根K线满足中点小于前一根K线低点且振幅大于上一根振幅
    PlotNumeric("Lineu", UpperAvg[-1], RGB_Red()) #输出通道上轨
    PlotNumeric("LineM", ExitAvg[-1], RGB_Green()) #输出通道中轨
    PlotNumeric("Lingd", LowerAvg[-1], RGB_Blue()) #输出通道下轨

    if MarketPosition() == 0:
        if RangeLeadB[-2] and Close()[-2] > UpperAvg[-2]:
            BKDFLG = 1
        if RangeLeadS[-2] and Close()[-2] < LowerAvg[-2]:
            SKDFLG = 1
    if MarketPosition() > 0 and BarsSinceEntry() > 0:
        if BarsSinceEntry() <= g_params['ExitBar']:
            if Low()[-1] <= ExitAvg[-1]:
                SPDFLG = 1
        elif BarsSinceEntry() > g_params['ExitBar']:
            if Low()[-1] <= UpperAvg[-1] - PriceTick():
                SPDFLG = 1
    if MarketPosition() < 0 and BarsSinceEntry() > 0:
        if BarsSinceEntry() <= g_params['ExitBar']:
            if High()[-1] >= ExitAvg[-1]:
                BPDFLG = 1
        elif BarsSinceEntry() > g_params['ExitBar']:
            if High()[-1] >= LowerAvg[-1] + PriceTick():
                BPDFLG = 1

#//------------------------历史发单------------------------//
    if context.strategyStatus() != 'C':
        if BKDFLG:#多头建仓
            Buy(1, Close()[-1], needCover=False) 
        elif SKDFLG:#空头建仓
            SellShort(1, Close()[-1], needCover=False)
        elif SPDFLG:
            Sell(1, Close()[-1])
        elif BPDFLG:
            BuyToCover(1, Close()[-1])
        return

#//------------------------实时处理------------------------//
    if ExchangeStatus(ExchangeName()) != '3':
        return
    N = 2 #下单手数
    T = 3 #时间间隔
    NOW = CurrentTime() #当前时间
    BIDP = 0 if Q_BidPrice() is None else Q_BidPrice() #买一价
    ASKP = 0 if Q_AskPrice() is None else Q_AskPrice() #卖一价
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
            BKFLG = 1 #买开标志归0
            BKDEL = 0 #买开撤单标志归0
        elif A_OrderStatus(BKID) == Enum_Canceled():
            LogInfo("BK信号：买开委托已撤！")
            if A_OrderFilledLot(BKID) > 0: #如果买开委托部分成交
                BKM = BKM - A_OrderFilledLot(BKID) #买开委托手数
            if BKM > 0: #如果买开委托手数大于0
                BKP = ASKP #买开委托价格
                LogInfo("BK信号：买开委托追价！")
                retCode, BKID = A_SendOrder(Enum_Buy(), Enum_Entry(), BKM, BKP) #发出买开委托
                BKT = NOW #买开委托时间
            BKDEL = 0 #买开撤单标志归0
        elif A_OrderStatus(BKID) == Enum_Suspended() or A_OrderStatus(BKID) == Enum_FillPart():
            if BKDEL == 0:
                if TimeDiff(BKT,NOW) > T:
                    LogInfo("BK信号：买开委托撤单！")
                    A_DeleteOrder(BKID) #撤掉买开委托挂单
                    BKDEL = 1 #已发出撤掉买开委托挂单
    if SPFLG == 1:
        if A_OrderStatus(SPID) == Enum_Filled():
            LogInfo("SP信号：卖平委托成交！")
            SPFLG = 0 #卖平标志归0
            SPDEL = 0 #卖平撤单标志归0
        elif A_OrderStatus(SPID) == Enum_Canceled():
            LogInfo("SP信号：卖平委托已撤！")
            if A_OrderFilledLot(SPID) > 0: #如果卖平委托部分成交
                SPM = SPM - A_OrderFilledLot(SPID) #卖平委托手数
            if BRP > 0 and SPM > 0 and SPM <= BRP: #如果卖平委托手数不超过多头可用持仓
                SPP = BIDP #卖平委托价格
                LogInfo("SP信号：卖平委托追价！")
                retCode, SPID = A_SendOrder(Enum_Sell,SH,SPM,SPP) #发出卖平委托
                SPT = NOW #卖平委托时间
            SPDEL = 0 #卖平撤单标志归0
        elif A_OrderStatus(SPID) == Enum_Suspended() or A_OrderStatus(SPID) == Enum_FillPart():
            if SPDEL == 0: #如果未撤单
               if TimeDiff(SPT,NOW) >= T: #如果时间间隔T秒
                    LogInfo("SP信号：卖平委托撤单！")
                    A_DeleteOrder(SPID) #撤掉卖平委托挂单
                    SPDEL = 1 #已发出撤掉卖平委托挂单
    if SKFLG == 1:
        if A_OrderStatus(SKID) == Enum_Filled():
            LogInfo("SK信号：卖开委托成交！")
            SKFLG = 0 #卖开标志归0
            SKDEL = 0 #卖开撤单标志归0
        elif A_OrderStatus(SKID) == Enum_Canceled():
            LogInfo("SK信号：卖开委托已撤！")
            if A_OrderFilledLot(SKID) > 0: #如果卖开委托部分成交
                SKM = SKM - A_OrderFilledLot(SKID) #卖开委托手数
            if SKM > 0: #如果卖开委托手数大于0
                SKP = BIDP #卖开委托价格
                LogInfo("SK信号：卖开委托追价！")
                retCode, SKID = A_SendOrder(Enum_Sell(), Enum_Entry(), SKM, SKP) #发出卖开委托
                SKT = NOW #卖开委托时间
            SKDEL = 0 #卖开撤单标志归0
        elif A_OrderStatus(SPID) == Enum_Suspended() or A_OrderStatus(SPID) == Enum_FillPart():
            if SKDEL == 0: #如果未撤单
               if TimeDiff(SKT, NOW) >= T: #如果时间间隔T秒
                    LogInfo("SK信号：卖开委托撤单！")
                    A_DeleteOrder(SKID) #撤掉卖开委托挂单
                    SKDEL = 1 #已发出撤掉卖开委托挂单
    if BPFLG == 1:
        if A_OrderStatus(BPID) == Enum_Filled():
            LogInfo("BP信号：买平委托成交！")
            BPFLG = 0 #买平标志归0
            BPDEL = 0 #买平撤单标志归0
        elif A_OrderStatus(BPID) == Enum_Canceled():
            LogInfo("BP信号：买平委托已撤！")
            if A_OrderFilledLot(BPID) > 0: #如果买平委托部分成交
                BPM = BPM - A_OrderFilledLot(BPID) #买平委托手数
            if SRP > 0 and BPM > 0 and BPM <= SRP: #如果买平委托手数不超过空头可用持仓
                BPP = ASKP #买平委托价格
                LogInfo("BP信号：买平委托追价！");
                retCode, BPID = A_SendOrder(Enum_Buy(),SH,BPM,BPP) #发出买平委托
                BPT = NOW #买平委托时间
            BPDEL = 0 #买平撤单标志归0
        elif A_OrderStatus(BPID) == Enum_Suspended() or A_OrderStatus(BPID) == Enum_FillPart():
            if BPDEL == 0: #如果未撤单
               if TimeDiff(BPT, NOW) >= T: #如果时间间隔T秒
                    LogInfo("BP信号：买平委托撤单！")
                    A_DeleteOrder(BPID) #撤掉买平委托挂单
                    BPDEL = 1 #已发出撤掉买平委托挂单
    
    #//------------------------委托处理------------------------//
    if BKDFLG == 1:
        if BKFLG == 0:
            BKM = N #买开委托手数
            BKP = ASKP #买开委托价格
            LogInfo("BK信号：买开委托发出！")
            retCode, BKID = A_SendOrder(Enum_Buy(),Enum_Entry(),BKM,BKP) #发出买开委托
            BKT = NOW #买开委托时间
            BKFLG = 1 #已发出买开委托
    if SPDFLG == 1:
        if SPFLG == 0:
            if BRP > 0: #如果有多头可用持仓
                SPM = BRP #卖平委托手数
                SPP = BIDP #卖平委托价格
                LogInfo("SP信号：卖平委托发出！")
                retCode, SPID = A_SendOrder(Enum_Sell(),SH,SPM,SPP) #发出卖平委托
                SPT = NOW #卖平委托时间
                SPFLG = 1 #已发出卖平委托
    if SKDFLG == 1:
        if SKFLG == 0:
            SKM = N #卖开委托手数
            SKP = BIDP #卖开委托价格
            LogInfo("SK信号：卖开委托发出！")
            retCode, SKID = A_SendOrder(Enum_Sell(),Enum_Entry(),SKM,SKP) #发出卖开委托
            SKT = NOW #卖开委托时间
            SKFLG = 1 #已发出卖开委托
    if BPDFLG == 1:
        if BPFLG == 0:
            if SRP > 0: #如果有空头可用持仓
                BPM = SRP #买平委托手数
                BPP = ASKP #买平委托价格
                LogInfo("BP信号：买平委托发出！")
                retCode, BPID = A_SendOrder(Enum_Buy(),SH,BPM,BPP) #发出买平委托
                BPT = NOW #买平委托时间
                BPFLG = 1 #已发出买平委托

