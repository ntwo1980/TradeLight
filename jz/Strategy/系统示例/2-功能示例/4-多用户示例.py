########################系统示例不支持修改########################
# 多用户示例
# 备注：多用户目前只能通过调用SetUserNo在设置函数中进行设置
# 只有设置了用户之后，才会收到该用户关于对应合约的交易数据
##################################################################
import talib as ta

ContractId = 'ZCE|Z|FG|MAIN'
user1 = 'Q554918351'
user2 = 'ES002'
user3 = 'ES003'
p1=5
p2=20

def initialize(context): 
    SetBarInterval(ContractId, Enum_Period_Min(), 1, 200)

    # 策略仅能收到 通过界面或者SetUserNo函数关联的账户的交易数据
    # 交易数据涵盖 委托、成交、市场状态、委托、成交、持仓
    # 仅支持访问本策略相关合约数据（通过界面或者SetBarInterval和SubQuote引用的合约）
    SetUserNo(user1,user2,user3) #修改账户为用户客户端登录的账户，最多设置10个

def handle_data(context):
    if CurrentBar() < p2:
        return

    # 使用talib计算均价
    ma1 = talib.MA(Close(), p1)
    ma2 = talib.MA(Close(), p2) 

    if MarketPosition(userNo=user1) == 0 and ma1[-1] > ma2[-1]:
        Buy(1, Close()[-1], userNo=user1)
        Buy(2, Close()[-1], userNo=user2)
        # 当通过SetUserNo设置多个交易账户时，该函数返回调用SetUserNo设置的第一个账户名称
        LogInfo("交易账户ID: ", A_AccountID())
        # 输出指定交易账户的当前商品的买入持仓量、买入持仓均价
        LogInfo("user1的买入持仓量: ", BuyPosition(userNo=user1))
        # 没有设置关联的账户，交易数据无法获取
        LogInfo("user3的买入持仓量: ", BuyPosition(userNo=user3))
    
    # 绘制指标图形
    PlotNumeric("ma1", ma1[-1], RGB_Red())
    PlotNumeric("ma2", ma2[-1], RGB_Green())