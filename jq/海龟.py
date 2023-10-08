# 导入函数库
import jqdata
import mytrade as t
import pandas as pd
import jqlib.technical_analysis as ta
import math

def set_permanet_params(context):
    g.max_total_value = 0
    g.max_total_value_date = None
    g.prev_stop_lose_date = None
    g.last_buy = {}
    g.money_security = "511880.XSHG"

def initialize(context):
    #set_benchmark('515220.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    set_permanet_params(context)
    run_daily(after_market_close, time='after_close')


# 每个单位时间(如果按天回测,则每天调用一次,如果按分钟,则每分钟调用一次)调用一次
def handle_data(context, data):
    #securities = ['159995.XSHE', '516160.XSHG', '512690.XSHG']
    hold_securities = [
        ## '159915.XSHE', # 创业板
        ## '159949.XSHE', # 创业板50
        '512170.XSHG', # 医药
        #'501057.XSHG', # 新能源车 LOF
        '512690.XSHG', # 酒
        ##'159928.XSHE', # 消费
        '515030.XSHG', # 新能源车
        #'512400.XSHG', # 有色
        #'515220.XSHG', # 煤炭
        ##'510880.XSHG', # 红利
        #'513050.XSHG', # 中概互联
        ##'512660.XSHG', # 军工
        ##'300012.XSHE', # 华测检测
        ]

    high_sell_securities = [
        #'516780.XSHG', # 稀土
        #'159995.XSHE', # 芯片
        #'512400.XSHG', # 有色
        #'515220.XSHG', # 煤炭
        #'512660.XSHG', # 军工
    ]

    securities = hold_securities + high_sell_securities
    #securities = ['159949.XSHE', '512690.XSHG', '501057.XSHG', '159929.XSHE']
    holding_securities = list(context.portfolio.positions.keys())
    prices = get_price(securities,  end_date=context.previous_date, fields=['close','high'], frequency='daily',count=300)
    _, atr = ta.ATR(securities, context.previous_date, timeperiod=20)

    closes = prices['close']
    highs = prices['high'][-20:-2]
    close_ma39 = pd.rolling_mean(closes, 39)
    close_ma10 = pd.rolling_mean(closes, 10)
    close_ma5 = pd.rolling_mean(closes, 10)

    stock_above_ma = {s:(closes[s][-90:] > close_ma39[s][-90:]).sum() for s in securities}

    for s in securities:
        close = closes[s][-1]
        max_high = max(highs[s][:-1])
        atr_secutiry = atr[s]

        #if close > max_high and s not in holding_securities:
        if s not in holding_securities:
            #if (closes[s][-1] > close_ma39[s][-1] and closes[s][-2] < close_ma39[s][-2]) or \
            #    (stock_above_ma[s] > 10 and closes[s][-1] > close_ma10[s][-1] and closes[s][-2] < close_ma10[s][-2]):
            if (closes[s][-1] > close_ma39[s][-1] and closes[s][-2] < close_ma39[s][-2]):
                buy_cash = get_buy_one_unit(context, closes[s], atr[s])
                #order_value(s, buy_cash)
                buy_security(context, s, buy_cash)

        if s in holding_securities:
            #if g.last_buy[s] > closes[s][-1] + 2 * atr_secutiry:
            #if (closes[s][-1] < close_ma39[s][-1] and closes[s][-2] > close_ma39[s][-2]) or \
            #    (g.last_buy[s] > closes[s][-1] + 2 * atr_secutiry):
            if (closes[s][-1] < close_ma39[s][-1] and closes[s][-2] > close_ma39[s][-2]):
                #print(('sell', s))
                order_target_value(s, 0)
            elif s in high_sell_securities and closes[s][-1] > close_ma39[s][-1] * 1.15 and closes[s][-1] > closes[s][-2] * 1.04:
                order_target_value(s, 0)
            elif s in high_sell_securities and closes[s][-1] > close_ma39[s][-1] * 1.15 and closes[s][-1] < close_ma5[s][-1] and closes[s][-2] > close_ma5[s][-2]:
                order_target_value(s, 0)
            else:
                max_value = context.portfolio.total_value * 0.3
                if max_value - context.portfolio.positions[s].value > 10000:
                    units = (closes[s][-1] - g.last_buy[s]) * 2 / atr_secutiry
                    if units > 0.9:
                        buy_cash = get_buy_one_unit(context, closes[s], atr[s]) * units
                        #print(('buy', s))
                        if buy_cash > max_value - context.portfolio.positions[s].value:
                            buy_cash = max_value - context.portfolio.positions[s].value
                            buy_security(context, s, buy_cash)

    if context.portfolio.available_cash > 10000:
        order_value(g.money_security, context.portfolio.available_cash)

def buy_security(context, security, value):
    holding_securities = list(context.portfolio.positions.keys())

    if context.portfolio.available_cash >= value:
         order_value(security, value)
    elif g.money_security in holding_securities:
        if context.portfolio.positions[g.money_security].value > value - context.portfolio.available_cash:
            order_value(g.money_security, context.portfolio.available_cash - value)

        order_value(security, context.portfolio.available_cash)

def get_buy_one_unit(context, closes, atr):
    factor = 0.001
    if closes[-1] < max(closes[-240:]) * 0.8:
        factor = 0.003
    elif closes[-1] < min(closes[-240:]) * 1.2:
        factor = 0.003

    factor = 0.001

    return context.portfolio.total_value * (closes[-1] / atr) * factor

def after_market_close(context):
    holding_securities = list(context.portfolio.positions.keys())
    orders = get_orders()
    trades = get_trades()

    for trade in trades.values():
        order = [order for order in orders.values() if trade.order_id == order.order_id][0]

        if not order.is_buy:
            if order.security in g.last_buy and order.security not in holding_securities:
                del g.last_buy[order.security]
        else:
            g.last_buy[order.security] = trade.price
