# 微信推送功能需要用户安装wechat-notice
# 安装方法可以在客户端上点击”python包安装“按钮，输入"wechat-notice"，然后点击安装进行安装
# wechat-notice包的介绍及使用方法参见：https://pypi.org/project/wechat-notice/0.0.4/
# 使用微信推送消息功能可以参考链接中使用示例--2、使用Server酱
# 注意：需要关注公众号并申请SendKey
# 该策略演示当交易服务器和行情服务器状态改变时利用微信推送消息提示


import talib
from wechat_notice import ServerChanNotice
SendKey = "SCT**************************" # 这里输入你自己的SendKey

user = "Q00000000000"  # 这里填写登录的交易账号

notice = ServerChanNotice(sckey=SendKey)
contractNo = "ZCE|Z|TA|MAIN"

def initialize(context): 
    # 设置K线稳定后发单
    SetOrderWay(2)
    SetTriggerType(6)
    # 设置基准合约，会覆盖界面设置的合约，建议通过界面设置(屏蔽SetBarInterval后则界面添加合约生效)
    SetBarInterval(contractNo, 'M', 1, 10)

	# send第一个参数为主题，第二个参数为消息内容
    notice.send('Initialize','策略初始化函数运行完成')
    
def handle_data(context):  
    # 等待数据就绪，否则计算果结为异常值
    if context.triggerType() == "N" and context.triggerData()["ServerType"] == "Q":
        if context.triggerData()["EventType"] == 2:  # 行情服务器为断开状态
            notice.send('Quotation Server State','行情服务器断连！')
    
    # 连接状态触发且为交易服务器的状态触发
    if context.triggerType() == "N" and context.triggerData()["ServerType"] == "T":
        triData = context.triggerData()
        if triData["UserNo"] == user and triData["EventType"] == 2:  # user账号为未连接状态
            notice.send('Trade Server State','交易账号断连！')
        if triData["UserNo"] == user and triData["EventType"] == 1:  # user账号为未连接状态
            notice.send('Trade Server State','交易账号连接成功！')

