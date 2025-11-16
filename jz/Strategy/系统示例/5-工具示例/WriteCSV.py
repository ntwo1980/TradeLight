'''
该示例策略演示将数据写入CSV格式，展示了将tick和非tick历史数据写入文件的过程。

CSV是比较通用的一种文件格式，该格式的文件是以纯文本形式存储表格数据。
因为是纯文本格式，相比于xls或xlsx格式不论是写入还是读取速度都要快的多。
CSV文件由任意数目的记录组成，每条记录由字段组成，字段间的分隔符是其它字符或字符串，最常见的是逗号或制表符。
CSV格式的文件可以使用记事本或excel打开，用记事本打开时显示逗号，用excel打开时不显示逗号，逗号用来分列。

注意：用户如果使用产品提供的利用本地历史数据运行策略时，需要保证本地数据的数据格式和本示例演示的数据格式相同，
      即第一行为表头，并且数据条目的顺序要与表头一致。
'''

import talib
import csv

cont = "ZCE|Z|TA|MAIN"
kType = 'M'
kSlice = 1

# K线数据表头
headers = ['TradeDate','DateTimeStamp','TotalQty','PositionQty', 'LastPrice', \
            'KLineQty','OpeningPrice','HighPrice','LowPrice','SettlePrice']
# Tick数据标头
tick_headers = ['TradeDate', 'DateTimeStamp', 'TotalQty', 'PositionQty', 'LastPrice', 'LastQty', 'PositionChg', \
                 'BuyPrice', 'SellPrice', 'BuyQty', 'SellQty',  'InnerSideQty', 'OutSideQty']

# 使用命令打开文件时，需要保证该文件没有被其他应用打开，否则会提示Permission denied错误
# 注意：只填文件名时，如果该文件存在会打开已经存在的文件，向文件中写入内容会覆盖原有文件内容！！！
# 文件不存在时，会自动创建一个新文件， 文件默认存储在客户端所在文件夹
# 这里将数据文件存放到策略文件夹中，用户也可以修改文件路径，打开和存到文件指定路径
f = open(r'./Quant/Strategy/hisdata.csv', 'w', encoding='utf-8', newline='')  # 创建文件对象
csv_writer = csv.writer(f)


# 策略开始运行时执行该函数一次
def initialize(context): 
    SetBarInterval(cont, kType, kSlice, 20000)
    SetTriggerType(5)
    SetOrderWay(2)
    
    # 根据K线类型构建列表头
    if kType == 'T' and kSlice == 0:
        csv_writer.writerow(tick_headers)
    else:
        csv_writer.writerow(headers)


# 策略触发事件每次触发时都会执行该函数
def handle_data(context):
    d = context.triggerData()
    if context.triggerType() == 'H' or context.triggerType() == 'K':  # K线触发
        if context.kLineType() == 'T' and context.kLineSlice() == 0:  # Tick数据
            data = [d['TradeDate'], d['DateTimeStamp'], d['TotalQty'], d['PositionQty'], \
                    d['LastPrice'], d['LastQty'], d['PositionChg'], d['BuyPrice'], d['SellPrice'], \
                    d['BuyQty'], d['SellQty'], d['InnerSideQty'], d['OutSideQty']]
        else: # 不为Tick的K线数据
            data = [d['TradeDate'], d['DateTimeStamp'], d['TotalQty'], d['PositionQty'], d['LastPrice'], d['KLineQty'], \
                    d['OpeningPrice'], d['HighPrice'], d['LowPrice'], d['SettlePrice']]
        
        csv_writer.writerow(data)
    
def exit_callback(context):
    # 退出时关闭文件
    f.close()

