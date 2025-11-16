########################系统示例不支持修改########################
# K线数据分为Tick、分钟、日线。多秒线由Tick生成、多分钟由1分钟生成、多日线由1日线生成。
# 可在设置界面订阅不同合约的K线数据；或通过SetBarInterval函数进行订阅
# 订阅数量较多时，请求等待时间相应会增加，请耐心等待。建议以分钟线和日线订阅回测，订阅秒线时请优先以起始时间点来订阅。
##################################################################
import talib

contractId = 'ZCE|Z|SR|MAIN'
kType = "D"
kSlice = 1 
qty = 10

def initialize(context):
    SetBarInterval(contractId, kType, kSlice, qty)
    SetTriggerType(5)

def handle_data(context):
    # 输出当前可以获取到的收盘价
    LogInfo("截止当前K线收盘价数据: ", Close()[-1])
    LogInfo("截止当前K线开盘价数据: ", Open()[-1])
    LogInfo("截止当前K线最高价数据: ", High()[-1])
    LogInfo("截止当前K线最低价数据: ", Low()[-1])
    LogInfo("截止当前K线成交量数据: ", Vol()[-1])
    LogInfo("截止当前K线持仓量数据: ", OpenInt()[-1])
    
    # 输出当前的K线索引，索引值从1开始
    LogInfo("当前K线索引: ", CurrentBar())
    # 输出当前Bar的状态值, 0表示第一个Bar,1表示中间普通Bar,2表示最后一个Bar
    LogInfo("当前Bar的状态值：", BarStatus())
    LogInfo("当前Bar的时间： ", Time())
    LogInfo("当前Bar的日期：", Date())
    LogInfo("当前Bar的交易日: ", TradeDate())

    # HisData可以获取指定历史数据类型的数据数组，如最高价、最低价、开盘价、收盘价等
    # 这里使用HisData获取收盘价数组数据，获取长度最大为100个的标准价数组，
    # 数组长度不足100个时，取当前可以取到的某长度的数组，
    # Enum_data_Typical()使用说明可以参考枚举函数的用法
    LogInfo("截止当前K线标准价信息： ", HisData(Enum_Data_Typical()))
    
    # 输出截止当前的K线的历史数据详情
    # HisBarsInfo可以获取当前可以获取到的全部K线的历史信息数组
    # 索引-1表示取最新的K线信息
    LogInfo("截止当前K线详细数据：", HisBarsInfo()[-1])