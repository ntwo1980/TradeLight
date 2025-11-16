########################系统示例不支持修改########################
# 布林强盗交易
##################################################################
import talib
code1 = 'ZCE|Z|SR|MAIN'
g_params['BollingerLengths'] = 50    #布林通道参数
g_params['Offset'] = 125    #布林通道参数
g_params['RocCalcLength'] = 30    #过滤器参数
g_params['LiqLength'] = 50    #自适应出场均线参数
g_params['Lots'] = 1    #交易手数

#布林通道中轨
MidLine = []
#布林通道上轨
UpBand = []
#布林通道下轨 
DnBand = []
#过滤器
RocCalc = []
#自适应出场均线的参数
LiqDays = []
#自适应的出场均线
LiqPoint = []
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

def initialize(context):
    SetBarInterval(code1, 'M', 1, 200, 200)
    SetTriggerType(5)
    SetOrderWay(2)
    SetActual()

def handle_data(context):
    #买开处理标志
    BKDFLG = 0
    #卖开处理标志
    SKDFLG = 0
    #买平处理标志
    BPDFLG = 0
    #卖平处理标志
    SPDFLG = 0

    global MidLine
    global UpBand
    global DnBand
    global RocCalc
    global LiqDays
    global LiqPoint

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
    global BKT
    global SKT
    global BPT
    global SPT

    if(CurrentBar()>=len(RocCalc)):
        if(len(RocCalc))==0:
            RocCalc.append(0)  
            LiqDays.append(0)   
        else:
            RocCalc.append(RocCalc[-1])         
            LiqDays.append(LiqDays[-1])    

    if len(Close()) < g_params['BollingerLengths']:
        return  

    #布林通道中轨
    MidLine = talib.MA(Close(), g_params['BollingerLengths'])
    Band = talib.STDDEV(Close(), g_params['BollingerLengths'])
    #布林通道上轨
    UpBand = MidLine + g_params['Offset'] / 100 * Band
    #布林通道下轨
    DnBand = MidLine - g_params['Offset'] / 100 * Band

    #画线
    PlotNumeric("MidLine", MidLine[-1], RGB_Red())
    PlotNumeric("upBand", UpBand[-1], RGB_Green())
    PlotNumeric("dnBand", DnBand[-1], RGB_Blue())

    #进场过滤器
    RocCalc[-1] = Close()[-1] - Close()[-g_params['RocCalcLength']]
    #满足过滤条件，且价格突破布林通道上轨，开多单
    if MarketPosition() <= 0 and RocCalc[-2] > 0 and High()[-1] >= UpBand[-2]:
        BKDFLG = 1
    #满足过滤条件，且价格突破布林通道下轨，开空单
    if MarketPosition() >= 0 and RocCalc[-2] < 0 and Low()[-1] <= DnBand[-2]:
        SKDFLG = 1
    #自适应出场均线
    if MarketPosition() == 0:
        LiqDays[-1] = (g_params['LiqLength'])
    else:
        LiqDays[-1] = LiqDays[-1] - 1
        LiqDays[-1] = 10 if LiqDays[-1]<10 else LiqDays[-1]
        
    LiqPoint = talib.MA(Close(), LiqDays[-1])
    PlotNumeric("liqPoint", LiqPoint[-1], RGB_Blue())

    #持有多单时，自适应出场均线低于布林通道上轨，且价格下破自适应出场均线，平多单
    if MarketPosition() > 0 and BarsSinceEntry() >= 1 and LiqPoint[-2] < UpBand[-2] and Low()[-1] <= LiqPoint[-2]:
        SPDFLG = 1
    #持有空单时，自适应出场均线高于布林通道下轨，且价格上破自适应出场均线，平空单
    if MarketPosition() < 0 and BarsSinceEntry() >= 1 and LiqPoint[-2] > DnBand[-2] and High()[-1] >= LiqPoint[-2]:
        BPDFLG = 1

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

    if ExchangeStatus(ExchangeName(code1)) != '3':   
        return  
    
    #//------------------------变量赋值------------------------//
    N = 2 #下单手数
    T = 3 #时间间隔
    NOW = CurrentTime() #当前时间
    BIDP = 0 if Q_BidPrice() is None else Q_BidPrice() #买一价
    ASKP = 0 if Q_AskPrice() is None else Q_AskPrice() #卖一价
    BRP = A_BuyPositionCanCover() #多头可用持仓
    SRP = A_SellPositionCanCover() #空头可用持仓
    if ExchangeName(code1) == 'SHFE': #如果是上期所合约
        SH = Enum_ExitToday() #平仓参数
    else: #如果非上期所合约
        SH = Enum_Exit() #平仓参数

    #//------------------------成交判断------------------------//
    if BKFLG == 1:
        if A_OrderStatus(BKID) == Enum_Filled():
            LogInfo("BK信号：买开委托成交！")
            BKFLG = 0 #买开标志归0
            BKDEL = 0 #买开撤单标志归0
        elif A_OrderStatus(BKID) == Enum_Canceled():
            LogInfo("BK信号：买开委托已撤！")
            if A_OrderFilledLot(BKID) > 0: #如果买开委托部分成交
                BKM = BKM - A_OrderFilledLot(BKID) #买开委托手数
            if BKM > 0: #如果买开委托手数大于0
                BKP = ASKP #买开委托价格
                LogInfo("BK信号：买开委托追价！")
                retCode, BKID = A_SendOrder(Enum_Buy(),Enum_Entry(),BKM,BKP) #发出买开委托
                BKT = NOW #买开委托时间
            BKDEL = 0 #买开撤单标志归0
        elif A_OrderStatus(BKID) == Enum_Suspended() or A_OrderStatus(BKID) == Enum_FillPart():
            if BKDEL == 0: #如果未撤单
               if (BKT - NOW) * 1000000 >= T: #如果时间间隔T秒
                    LogInfo("BK信号：买开委托撤单！")
                    A_DeleteOrder(BKID) #撤掉买开委托挂单
                    BKDEL = 1 #已发出撤掉买开委托挂单
    if SPFLG == 1:
        if A_OrderStatus(SPID) == Enum_Filled():
            LogInfo("SP信号：卖平委托成交！")
            SPFLG = 0 #卖平标志归0
            SPDEL = 0 #卖平撤单标志归0
        elif A_OrderStatus(SPID) == Enum_Canceled():
            LogInfo("SP信号：卖平委托已撤！");
            if A_OrderFilledLot(SPID) > 0: #如果卖平委托部分成交
                SPM = SPM - A_OrderFilledLot(SPID) #卖平委托手数
            if BRP > 0 and SPM > 0 and SPM <= BRP: #如果卖平委托手数不超过多头可用持仓
                SPP = BIDP #卖平委托价格
                LogInfo("SP信号：卖平委托追价！")
                retCode, SPID = A_SendOrder(Enum_Sell(),SH,SPM,SPP) #发出卖平委托
                SPT = NOW #卖平委托时间
            SPDEL = 0 #卖平撤单标志归0
        elif A_OrderStatus(SPID) == Enum_Suspended() or A_OrderStatus(SPID) == Enum_FillPart():
            if SPDEL == 0: #如果未撤单
               if (SPT - NOW) * 1000000 >= T: #如果时间间隔T秒
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
                retCode, SKID = A_SendOrder(Enum_Sell(),Enum_Entry(),SKM,SKP) #发出卖开委托
                SKT = NOW #卖开委托时间
            SKDEL = 0 #卖开撤单标志归0
        elif A_OrderStatus(SKID) == Enum_Suspended() or A_OrderStatus(SKID) == Enum_FillPart():
            if SKDEL == 0: #如果未撤单
               if (SKT - NOW) * 1000000 >= T: #如果时间间隔T秒
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
                LogInfo("BP信号：买平委托追价！")
                retCode, BPID = A_SendOrder(Enum_Buy(),SH,BPM,BPP) #发出买平委托
                BPT = NOW #买平委托时间
            BPDEL = 0 #买平撤单标志归0
        elif A_OrderStatus(BPID) == Enum_Suspended() or A_OrderStatus(BPID) == Enum_FillPart():
            if BPDEL == 0: #如果未撤单
               if (BPT - NOW) * 1000000 >= T: #如果时间间隔T秒
                    LogInfo("BP信号：买平委托撤单！")
                    A_DeleteOrder(BPID) #撤掉买平委托挂单
                    BPDEL = 1 #已发出撤掉买平委托挂单
    #//------------------------委托处理------------------------//
    if BKDFLG == 1:
        if BKFLG == 0: #如果没有买开委托
            BKM = N #买开委托手数
            BKP = ASKP #买开委托价格
            LogInfo("BK信号：买开委托发出】")
            retCode, BKID = A_SendOrder(Enum_Buy(),Enum_Entry(),BKM,BKP) #发出买开委托
            BKT = NOW #买开委托时间
            BKFLG = 1 #已发出买开委托
    if SPDFLG == 1:
        if SPFLG == 0: #如果没有卖平委托
            if BRP > 0: #如果有多头可用持仓
                SPM = BRP #卖平委托手数
                SPP = BIDP #卖平委托价格
                LogInfo("SP信号：卖平委托发出！")
                retCode, SPID = A_SendOrder(Enum_Sell(),SH,SPM,SPP) #发出卖平委托
                SPT = NOW #卖平委托时间
                SPFLG = 1 #已发出卖平委托
    if SKDFLG == 1:
        if SKFLG == 0: #如果没有卖开委托
            SKM = N #卖开委托手数
            SKP = BIDP #卖开委托价格
            LogInfo("SK信号：卖开委托发出！")
            retCode, SKID = A_SendOrder(Enum_Sell(),Enum_Entry(),SKM,SKP) #发出卖开委托
            SKT = NOW #卖开委托时间
            SKFLG = 1 #已发出卖开委托
    if BPDFLG == 1:
        if BPFLG == 0: #如果没有买平委托
            if SRP > 0: #如果有空头可用持仓
                BPM = SRP #买平委托手数
                BPP = ASKP #买平委托价格
                LogInfo("BP信号：买平委托发出！")
                retCode, BPID = A_SendOrder(Enum_Buy(),SH,BPM,BPP) #发出买平委托
                BPT = NOW #买平委托时间
                BPFLG = 1 #已发出买平委托
