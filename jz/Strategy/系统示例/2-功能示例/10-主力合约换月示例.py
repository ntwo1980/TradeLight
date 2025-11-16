########################系统示例不支持修改########################
# 主力合约切换示例
# 用户需要主力合约对应的具体合约切换事件触发策略时，需要通过SetTriggerType(8)设置该触发方式
# 当该事件触发时，可以在handle_data函数中通过triggerData()获取事件详情
# 策略收到该事件触发时，可以选择针对该事件的策略执行逻辑。
# 本示例策略演示收到该事件时，发送微信通知，并停止运行策略。
# 
# 备注：
#     1. 默认情况下，该事件的处理根据用户是否订阅该合约分为两种情况处理：
#        1> 当用户未订阅主力合约触发时，程序会在收到后台推送的主力合约切换事件时，自动为用户停止策略，避免产生非用户本意的交易行为；
#        2> 当用户订阅该事件时，将该事件的处理行为交给用户处理，不再自动停止策略执行，这时该事件的行为需要用户自己控制。
#        
#     2. 推送微信消息，在"系统示例->5-工具示例->微信推送.py中以做过说明，这里不再赘述。
##################################################################

import talib
from wechat_notice import ServerChanNotice
SendKey = "SCT**************************" # 这里输入你自己的SendKey

notice = ServerChanNotice(sckey=SendKey)

# 策略参数字典
g_params['p1'] = 20    # 参数示例
contract = "ZCE|Z|TA|MAIN"

# 策略开始运行时执行该函数一次
def initialize(context): 
    SetBarInterval(contract, "M", 1, 50)
    # 设置主力合约换月触发
    SetTriggerType(8) 
    SetActual()


# 策略触发事件每次触发时都会执行该函数
def handle_data(context):
    if context.triggerType() == 'U':
        data = context.triggerData()
        notice.send('合约换月提醒', '{}换月前对应合约为：{}， 换月后对应合约为: {}'\
            .format(data["Cont"], data["OriginCont"], data["NewCont"]))
        UnloadStrategy()


