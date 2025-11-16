# ************************************************************************************************
# 策略向企业微信推送消息功能介绍
# ************************************************************************************************
# 企业微信推送消息功能需要安装企业微信和python的requests库
#   1>. requests安装方法：在极智量化客户端上点击”python包安装“按钮，输入"requests"，然后点击安装进行安装，
#                       request库用于向企业微信发送消息，requests的其他用法用户可参考互联网
#   2>. 企业微信安装方法： 用户可根据自身需求在官网下载桌面端或手机端：https://work.weixin.qq.com/#indexDownload
#                       手机端也可在应用市场搜索企业微信安装
#                       企业微信的其他使用方法参见：https://open.work.weixin.qq.com/help2/pc
#
# 使用前准备：
#   0>. 需先打开企业微信并使用手机号或微信授权登录
#   1>. 注册企业微信，可参见链接：https://open.work.weixin.qq.com/help2/pc/15422
#   2>. 设置群机器人，可参见链接：
#           https://open.work.weixin.qq.com/help2/pc/14931#%E4%BA%8C%E3%80%81%E7%BE%A4%E6%9C%BA%E5%99%A8%E4%BA%BA%E6%B7%BB%E5%8A%A0%E5%85%A5%E5%8F%A3
#   3>. 获取群机器人webhook地址，可参见链接：
#           https://open.work.weixin.qq.com/help2/pc/14931#%E5%85%AD%E3%80%81%E7%BE%A4%E6%9C%BA%E5%99%A8%E4%BA%BAWebhook%E5%9C%B0%E5%9D%80
#           获取的群机器人webhook地址作为requests发送消息时的接收地址，格式为：https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=***************
#           用户需要根据自己的webhook地址填入key=后面的key信息
#
# requests支持发送文本消息、markdown消息、图片消息或文件消息
# 本策略仅提供简单的文本消息推送方法，其他类型的消息推送用户可自行研究。
# 示例策略提供两种发送消息的方式：
#          1>. 直接发送文本消息：即在代码中直接调用send_text_msg
#          2>. 创建线程，将发消息的操作放到线程中去完成：即在代码中调用send_msg_thread
#          第1>种"直接发送文本消息"方式可能会受到网络延迟和响应时间、服务器响应速度、请求数据大小等的影响导致发送时间较长，影响后续程序执行， 
#          此时用户可考虑第2>种"将发消息的操作放到线程中执行"的方式
import requests
import threading

send_url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=******"  # 填入自己的机器人的webhook地址，此地址无效

# 发送文本消息
def send_txt_msg(message):
    """
    request的post() 方法可以发送 POST 请求到指定 url，一般格式如下：
        requests.post(url, data={key: value}, json={key: value}, args)
        url 请求 url
        data 参数为要发送到指定 url 的字典、元组列表、字节或文件对象。
        json 参数为要发送到指定 url 的 JSON 对象。
        args 为其他参数，比如 cookies、headers、verify等。
    """
    try:
        send_data = {
            "msgtype": "text",  
            "text": {"content": message}
        }
        res = requests.post(url = send_url, json = send_data)

        if res.json()["errmsg"] != "ok":
            LogError(f"此消息发送失败：{message}, errmsg: {res.json()['errmsg']}")
    except Exception as e:
        LogInfo("运行出错: ", e)
        

# 多线程
def send_txt_msg_thread(message):
    thread = threading.Thread(target=send_txt_msg, args=(message,))
    thread.start()

def initialize(context):        
    SetBarInterval("ZCE|Z|SR|MAIN", Enum_Period_Min(), 1, 1)
    
def handle_data(context):
    if context.strategyStatus() == "H":
        # send_txt_msg("文本测试信息")
        send_txt_msg_thread('线程文本测试信息')

        
        


        


