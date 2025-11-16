########################系统示例不支持修改########################
# 双均线交易
##################################################################
import talib
code1 = 'ZCE|Z|TA|MAIN'
g_params['FastLength'] = 5 
g_params['SlowLength'] = 20

#开仓标志
BKFLG = 0
SKFLG = 0
#平仓标志
BPFLG = 0
SPFLG = 0
#开仓委托
BKID = 0
SKID = 0
#平仓委托
BPID = 0
SPID = 0
#开仓撤单标志
BKDEL = 0
SKDEL = 0
#平仓撤单标志
BPDEL = 0
SPDEL = 0
#平仓委托手数
BKM = 0
SKM = 0
#平仓撤单标志
BPM = 0
SPM = 0
#开仓委托价格
BKP = 0
SKP = 0
#平仓委托价格
BPP = 0
SPP = 0

def initialize(context): 
    SetBarInterval(code1, 'M', 1, 500)
    SetTriggerType(5)
    SetOrderWay(2)
    SetActual()

def handle_data(context):
    BKDFLG = 0
    SKDFLG = 0
    BPKDFLG = 0
    SPKDFLG = 0
    BRP = 0
    SRP = 0
    global BKID
    global SKID
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

    if CurrentBar() < g_params['SlowLength']:
        return
        
    AvgValue1 = talib.MA(Close(), g_params['FastLength']) #快线周期均值
    AvgValue2 = talib.MA(Close(), g_params['SlowLength']) #慢线周期均值
    PlotNumeric("ma1", AvgValue1[-1], 0xFF0000)
    PlotNumeric("ma2", AvgValue2[-1], 0x00aa00)

    # 执行下单操作
    if MarketPosition() <= 0 and AvgValue1[-2] > AvgValue2[-2]:
        BPKDFLG = 1
    if MarketPosition() >= 0 and AvgValue1[-2] < AvgValue2[-2]:
        SPKDFLG = 1
    #//------------------------历史发单------------------------//   
    if context.strategyStatus() != 'C':
        if BPKDFLG:#多头建仓
            Buy(1, Close()[-1])
        elif SPKDFLG:#空头建仓
            SellShort(1, Close()[-1])
        return
    #//------------------------实时处理------------------------//
    if ExchangeStatus(ExchangeName()) != '3':
        return
    #//------------------------变量赋值------------------------//
    N = 2 #下单手数
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
    if BPFLG == 1:
        if A_OrderStatus(BPID) == Enum_Filled():
            LogInfo("BPK信号：买平委托成交!")
            BKDFLG = 1 #开启买开处理
            BPFLG = 0 #买平标志归0
    if BKFLG == 1:
        if A_OrderStatus(BKID) == Enum_Filled():
            LogInfo("BPK信号：买开委托成交！")
            if BKDEL > 0: #如果是SPK信号撤单
                SPKDFLG = 1 #开启卖平开处理
            BKFLG = 0 #买开标志归0
            BKDEL = 0 #买开撤单标志归0
        elif A_OrderStatus(BKID) == Enum_Canceled():
            LogInfo("SPK信号：买开委托已撤！")
            SPKDFLG = 1 #开启卖平开处理
            BKFLG = 0 #买开标志归0
            BKDEL = 0 #买开撤单标志归0
        elif A_OrderStatus(BKID) == Enum_Suspended() or A_OrderStatus(BKID) == Enum_FillPart():
            if BKDEL == 2: #如果是SPK信号撤单
               LogInfo("SPK信号：买开委托撤单！")
               A_DeleteOrder(BKID) #撤掉买开委托挂单
               BKDEL = 3 #SPK信号撤掉买开委托挂单
    if SPFLG == 1:
        if A_OrderStatus(SPID) == Enum_Filled():
            LogInfo("SPK信号：卖平委托成交！")
            SKDFLG = 1 #开启卖开处理
            SPFLG = 0 #卖平标志归0
    if SKFLG == 1:
        if A_OrderStatus(SKID) == Enum_Filled():
            LogInfo("SPK信号：卖开委托成交！")
            if SKDEL > 0: #如果是BPK信号撤单
                BPKDFLG = 1 #开启买平开处理
            SKFLG = 0 #卖开标志归0
            SKDEL = 0 #卖开撤单标志归0
        elif A_OrderStatus(SKID) == Enum_Canceled():
            LogInfo("BPK信号：卖开委托已撤！")
            BPKDFLG = 1 #开启买平开处理
            SKFLG = 0 #卖开标志归0
            SKDEL = 0 #卖开撤单标志归0
        elif A_OrderStatus(SKID) == Enum_Suspended() or A_OrderStatus(SKID) == Enum_FillPart():
            if SKDEL == 2: #如果是BPK信号撤单
               LogInfo("BPK信号：卖开委托撤单！")
               A_DeleteOrder(SKID) #撤掉卖开委托挂单
               SKDEL = 3 #BPK信号撤掉卖开委托挂单

    #//------------------------委托处理------------------------//
    if BPKDFLG == 1:
        if SKFLG == 1:
            if SKDEL == 0:
                if A_OrderStatus(SKID) == Enum_Suspended() or A_OrderStatus(SKID) == Enum_FillPart():
                    LogInfo("BPK信号：卖开委托撤单！")
                    A_DeleteOrder(SKID) #撤掉卖开委托挂单
                    SKDEL = 1 #BPK信号撤掉卖开委托挂单
                else:
                    SKDEL = 2 #BPK信号撤掉卖开委托挂单
        elif SKFLG == 0:
            if BPFLG == 0:
                if SRP > 0:
                    BPM = SRP #买平委托手数
                    BPP = RLP #买平委托价格
                    LogInfo("BPK信号：买平委托发出！")
                    retCode, BPID = A_SendOrder(Enum_Buy(), SH, BPM, BPP) #发出买平委托
                    BPFLG = 1 #已发出买平委托
                elif SRP == 0:
                    BKDFLG = 1 #开启买开处理
    if BKDFLG == 1:
        if BKFLG == 0:
            BKM = N #买开委托手数
            BKP = ASKP #买开委托价格
            LogInfo("BPK信号：买开委托发出！")
            retCode, BKID = A_SendOrder(Enum_Buy(), Enum_Entry(), BKM, BKP) #发出买开委托
            BKFLG = 1 #已发出买开委托
    if SPKDFLG == 1:
        if BKFLG == 1:
            if BKDEL == 0:
                if A_OrderStatus(BKID) == Enum_Suspended() or A_OrderStatus(BKID) == Enum_FillPart():
                    LogInfo("SPK信号：买开委托撤单！")
                    A_DeleteOrder(BKID) #撤掉买开委托挂单
                    BKDEL = 1 #SPK信号撤掉买开委托挂单
                else:
                    BKDEL = 2#SPK信号撤掉买开委托挂单
        elif BKFLG == 0:
            if SPFLG == 0:
                if BRP > 0:
                    SPM = BRP #卖平委托手数
                    SPP = FLP #卖平委托价格
                    LogInfo("SPK信号：卖平委托发出！")
                    retCode, SPID = A_SendOrder(Enum_Sell(), SH, SPM, SPP) #发出卖平委托
                    SPFLG = 1 #已发出卖平委托
                elif BRP == 0:
                    SKDFLG = 1 #开启卖开处理
    if SKDFLG == 1:
        if SKFLG == 0:
            SKM = N #卖开委托手数
            SKP = BIDP #卖开委托价格
            LogInfo("SPK信号：卖开委托发出！");
            retCode, SKID = A_SendOrder(Enum_Sell(), Enum_Entry(),SKM,SKP) #发出卖开委托
            SKFLG = 1 #已发出卖开委托
