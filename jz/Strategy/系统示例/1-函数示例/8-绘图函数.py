########################系统示例不支持修改########################
#绘图函数
##################################################################
import talib

p1=5
p2=20

def initialize(context): 
    SetBarInterval('ZCE|Z|SR|MAIN', 'M', 1, 200)
    SetTriggerType(5)
    SetOrderWay(2)

def numeric():
    if CurrentBar() < p2:
        return
    # 使用talib计算均价
    ma1 = talib.MA(Close(), p1)
    ma2 = talib.MA(Close(), p2) 
    # 绘制指标图形 主图
    PlotNumeric("ma1", ma1[-1], RGB_Red())
    
    PlotNumeric("ma2", ma2[-1], RGB_Green(), True, False)
    # 回溯偏移2
    PlotNumeric("ma3", ma2[-1], RGB_Blue(), True, False, 2)
    # 副图
    PlotNumeric("fit", ma2[-1], RGB_Red(), False, True)
    #UnPlotNumeric("ma1", True, 3)

def partLine():
    #绘制斜线段
    idx1 = CurrentBar()
    a = Close()[-1]
    b = Close()[-2]
    if idx1 >= 100:
        count = 1
        PlotPartLine("PartLine", idx1, a, count, b, RGB_Green(), True, False, 1)
        #UnPlotPartLine("PartLine", idx1 - 3, count, True)

def text():
    #绘制文字
    PlotText(Close()[-1], "ORDER", RGB_Green(), main=True)
    #UnPlotText(True, 3)

def icon():
    #绘制系统图标
    PlotIcon(Close()[-1], 0, True, 0)
    #UnPlotIcon(True, 3)

def dot():
    #绘制点
    PlotDot("Dot", Close()[-1], 2, RGB_Red(), True, 1)
    #UnPlotDot("Dot", True, 3)

def bar():
    #绘制柱子
    PlotBar("Bar", Open()[-1], Close()[-1], RGB_Red(), True, True, 1)
    #UnPlotBar("Bar", True, 3)

def vertLine():
    #绘制竖线
    PlotVertLine(RGB_Red(), True, True, 0)
    #UnPlotVertLine(True, 3)

def stickLine():
    #绘制竖线段
    PlotStickLine("StickLine", Close()[-1], Open()[-1], RGB_Green(), True, False, 1)
    #UnPlotStickLine("StickLine")
    
def handle_data(context):
    numeric()
