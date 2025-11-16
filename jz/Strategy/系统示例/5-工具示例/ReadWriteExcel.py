'''
读写excel示例策略
该示例演示利用python库xlrd、xlwt读写excel文件，用户需要利用程序提供的python包安装功能安装xlrd、xlwt库
若没有安装这两个库，需要点击python包安装，分别输入xlrd、xlwt安装完成后再运行策略
首先读取要订阅的合约并订阅合约的即时行情，然后将订阅的合约的即时行情写入同一个excel文件中
首先在initialize订阅了三个合约，并给待写入文件写入数据表头，
然后在handle_data中演示将合约的K线数据记录到文件中，在hisover_callback中演示如何读取文件

注意：
操作策略中涉及的excel文件时文件不能被其他应用程序占用,否则会提示Permission denied错误
xlrd版本>=2.0时，只支持读取xls格式的文件
excel文件只支持写入.xls格式excel文件，且最大写入行数不能超过65536行，否则会报错
用户可考虑使用openpyxl库或其他操作excel文件的库，这里不再介绍

读取文件和写入文件的位置存放在Strategy目录下
'''
import talib
import xlrd
import xlwt

ex_file = r'./Quant/Strategy/cont_data.xls'  # 写入操作的文件路径

cont_sheet = 'Sheet1'  # excel中待读取的工作簿名

#合约列表
g_contList = ["ZCE|Z|TA|MAIN", "ZCE|Z|AP|MAIN", "ZCE|Z|SR|MAIN"]

wt_work = None
wt_table = None
row = 1  # 用于记录待写入excel文件的当前行号，表头是第0行，数据记录从第一行开始

def initialize(context):
    # 订阅g_congList中的合约
    for c in g_contList:
        SetBarInterval(c, "M", 1, 10, isTrigger=True)
    SetTriggerType(5)

    global wt_work
    global wt_table

    #行情表格
    wt_work  = xlwt.Workbook()   # 创建一个worksheet
    wt_table = wt_work.add_sheet(cont_sheet)  # 添加一个工作簿，并设置工作簿的名称

    # 写入表头
    table_head = ['合约', '时间', '最高价', '开盘价', '最低价', '收盘价', '成交量', '持仓量']
    for i in range(len(table_head)):
        wt_table.write(0, i, table_head[i])
    
    wt_work.save(ex_file)

def handle_data(context):
    global wt_work
    global wt_table

    global row

    #只记录历史阶段数据
    if context.triggerType() != 'H':
        return

    #保存合约号、最新价、成交量、买卖价、买卖量到excel表格中
    cont = context.contractNo()
    if cont in g_contList: # 只记录在策略中订阅的合约历史行情
        wt_table.write(row, 0, cont)
        wt_table.write(row, 1, Time(cont, 'M', 1)) # 当前bar的时间
        wt_table.write(row, 2, High(cont, 'M', 1)[-1])
        wt_table.write(row, 3, Open(cont, 'M', 1)[-1])
        wt_table.write(row, 4, Low(cont, 'M', 1)[-1])
        wt_table.write(row, 5, Close(cont, 'M', 1)[-1])
        wt_table.write(row, 6, int(Vol(cont, 'M', 1)[-1]))
        wt_table.write(row, 7, int(OpenInt(cont, 'M', 1)[-1]))
        row += 1
        wt_work.save(ex_file)


def hisover_callback(context):
    #历史阶段结束，打印合约的数据
    rd_work = xlrd.open_workbook(ex_file) # 打开待读取的excel文件
    rd_table = rd_work.sheet_by_name(cont_sheet)   # 获取待读入文件指定的工作部Sheet1

    # 这里只演示读取"ZCE|Z|TA|MAIN"合约的数据
    contract = "ZCE|Z|TA|MAIN"
    for i in range(rd_table.nrows): # 遍历工作簿的所有行
        rows = rd_table.row_values(i)  # 获取第i行的内容，rows为list类型，为第i行的数据
        if rows[0] == contract:
            LogInfo(rows[1:-1]) # 只访问contract的数据部分
