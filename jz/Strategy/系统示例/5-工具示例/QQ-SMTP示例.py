import smtplib
from email.mime.text import MIMEText

#发送邮箱地址(配置自己的邮箱)
sender = '120614139@qq.com'
#邮箱授权码，非登陆密码(配置自己的邮箱授权码)(授权码获取方式 https://jingyan.baidu.com/article/6079ad0eb14aaa28fe86db5a.html)
password = 'qwertyuiopasdfgh'
#收件箱地址(配置自己的邮箱)
receiver = '120614139@qq.com'
#smtp服务器
smtp_server = 'smtp.qq.com'

def sendmail(title,content):
    #发送纯文本格式的邮件
    msg = MIMEText(content,'plain','utf-8')
    #主题
    msg['Subject'] = title
    #发送邮箱地址
    msg['From'] = sender
    #收件箱地址
    msg['To'] = receiver
    #构造
    server = smtplib.SMTP(smtp_server,25)
    #登录 
    server.login(sender,password)
    #发送
    server.sendmail(sender,receiver,msg.as_string())
    #退出
    server.quit()

# 策略开始运行时执行该函数一次
def initialize(context): 
    SetBarInterval('ZCE|Z|SR|MAIN', "M", 1, 200) 
    sendmail('initialize','策略初始化')


# 策略触发事件每次触发时都会执行该函数
def handle_data(context):
    if(CurrentBar()==1):
        sendmail('handle_data','执行第一根K线')


# 历史回测阶段结束时执行该函数一次
def hisover_callback(context):
    sendmail('hisover_callback','历史回溯结束')


# 策略退出前执行该函数一次
def exit_callback(context):
    sendmail('exit_callback','退出')