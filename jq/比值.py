# 导入函数库
import jqdata
import mytrade as t
import pandas as pd
import talib
import math


def set_permanet_params(context):
    g.max_total_value = 0
    g.max_total_value_date = None
    g.prev_stop_lose_date = None
    g.last_buy_day = None
    g.buy = None
    g.sell = None

def initialize(context):
    set_benchmark('000932.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    set_permanet_params(context)
    run_daily(stat, time='morning')
    run_daily(market_open, time='open')

# 每个单位时间(如果按天回测,则每天调用一次,如果按分钟,则每分钟调用一次)调用一次
def stat(context):
    g.buy = None
    g.sell = None
    today = context.current_dt

    if context.portfolio.total_value > g.max_total_value:
        g.max_total_value = context.portfolio.total_value
        g.max_total_value_date = today

    if context.portfolio.total_value < g.max_total_value * 0.9:
        for s in context.portfolio.positions.keys():
            g.sell = s
            g.max_total_value = context.portfolio.total_value
            g.max_total_value_date = today
            g.prev_stop_lose_date = today

        print('stop loss')
        return

    #indexes = ['000932.XSHG', '000015.XSHG']  # 红利
    #securities = ['159928.XSHE', '510880.XSHG']
    indexes = ['000932.XSHG', '399006.XSHE']  # 创业板
    securities = ['159928.XSHE', '159915.XSHE']
    #indexes = ['000932.XSHG', '000688.XSHG']  # 科创50
    #securities = ['159928.XSHE', '588300.XSHG']
    #indexes = ['000932.XSHG', '000858.XSHG']  # 信息
    #securities = ['159928.XSHE', '159939.XSHE']
    #indexes = ['512690.XSHG', '399006.XSHE']  # 创业板
    #securities = ['512690.XSHG', '159915.XSHE']
    #indexes = ['000932.XSHG', '399976.XSHE']  # 新能源
    #securities = ['159928.XSHE', '501057.XSHG']
    #indexes = ['000932.XSHG', '399976.XSHE']
    #securities = ['159928.XSHE', '501057.XSHG']

    days = 250
    if g.last_buy_day:
        days_since_last_buy =  t.get_trading_day_num_from(g.last_buy_day, context.previous_date)
        days = max(days_since_last_buy, days)
    prices = get_price(indexes,  end_date=context.previous_date, fields='close', frequency='daily',count=days)['close'].dropna(axis=1)
    ratio = prices.ix[:, 0] / prices.ix[:, 1]

    (slop10_1, _, _, _, _) = t.get_linear(prices[indexes[0]][-10:])
    (slop10_2, _, _, _, _) = t.get_linear(prices[indexes[1]][-10:])
    (slop20_1, _, _, _, _) = t.get_linear(prices[indexes[0]][-20:])
    (slop20_2, _, _, _, _) = t.get_linear(prices[indexes[1]][-20:])

    ratio_ma = talib.KAMA(np.array(ratio), timeperiod=37)
    ma39 = pd.rolling_mean(prices, 39)
    df = pd.DataFrame({'ratio': ratio, 'ratio_ma': ratio_ma})
    df.dropna(inplace=True)

    days_since_prev_stop_lose_date = 100
    if g.prev_stop_lose_date:
        days_since_prev_stop_lose_date =  t.get_trading_day_num_from(g.prev_stop_lose_date, context.previous_date)

    record(ratio=df['ratio'][-1])
    record(ratio_ma=df['ratio_ma'][-1])

    signal = 0

    if df['ratio'][-1] > df['ratio_ma'][-1] and df['ratio'][-2] < df['ratio_ma'][-2]:
        signal = 1
        if securities[1] in context.portfolio.positions:
            if prices.ix[-1, 0] > prices.ix[-2, 0] or True:
                print(('sell', securities[1]))
                g.sell = securities[1]
            else:
                return

        days_above_ma = (prices.ix[-90:, 0] > ma39.ix[-90:, 0]).sum()

        if securities[0] not in context.portfolio.positions:
            if today.month not in [6] or days_since_prev_stop_lose_date > 10:
                g.last_buy_day = context.current_dt.date()
                g.buy = securities[0]
                print(('buy1', securities[0]))
    elif df['ratio'][-1] < df['ratio_ma'][-1] and df['ratio'][-2] > df['ratio_ma'][-2]:
            signal = -1
            if securities[0] in context.portfolio.positions:
                if prices.ix[-1, 1] > prices.ix[-2, 1] or True:
                    print(('sell', securities[0]))
                    g.sell = securities[0]
                else:
                    return

            days_above_ma = (prices.ix[-90:, 1] > ma39.ix[-90:, 1]).sum()

            if securities[1] not in context.portfolio.positions:
                if today.month not in [6] or days_since_prev_stop_lose_date > 10:
                    g.last_buy_day = context.current_dt.date()
                    g.buy = securities[1]

                    print(('buy1', securities[1]))
    elif len(context.portfolio.positions) == 0:
        if prices.ix[-1, 0] > ma39.ix[-1, 0] and prices.ix[-2, 0] < ma39.ix[-2, 0]:
            days_above_ma = (prices.ix[-90:, 0] > ma39.ix[-90:, 0]).sum()

            if days_above_ma > 60:
                g.last_buy_day = context.current_dt.date()
                g.buy = securities[0]

                print(('buy2', securities[0]))
        elif prices.ix[-1, 1] > ma39.ix[-1, 1] and prices.ix[-2, 1] < ma39.ix[-2, 1]:
            days_above_ma = (prices.ix[-90:, 1] > ma39.ix[-90:, 1]).sum()

            if days_above_ma > 60:
                g.last_buy_day = context.current_dt.date()
                g.buy = securities[1]

                print(('buy2', securities[1]))

    record(signal=signal * 3)

def market_open(context):
    if g.sell:
        order_target_value(g.sell, 0)

    if g.buy:
        order_target_value(g.buy, context.portfolio.available_cash)

