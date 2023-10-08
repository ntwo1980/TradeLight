# 导入函数库
import jqdata
import mytrade as t
import pandas as pd
import jqlib.technical_analysis as ta
import datetime as dt
import math

# 初始化函数，设定要操作的股票、基准等等
def set_permanet_params(context):
    g.max_total_value = 0
    g.max_total_value_date = None
    g.prev_stop_lose_date = None
    g.last_buy = {}
    g.money_security = "511880.XSHG"
    g.last_buy = {}

def set_session_params(context):
    pass

def count_positive_count(values):
    return sum(x>0 for x in values)

def initialize(context):
    #set_benchmark('515220.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    set_permanet_params(context)

    # run_daily(before_market_open, time='before_open')
    run_daily(market_open, time='open')
    run_daily(after_market_close, time='after_close')
    run_daily(stat, time='morning')

def stat(context):
    set_session_params(context)

    pd.set_option('display.notebook_repr_html', False)
    pd.set_option('display.max_rows', 9999)
    pd.set_option('display.max_columns', 500)
    pd.set_option('display.width', 1000)
    pd.set_option('precision', 3)
    pd.set_option('display.float_format', '{:.2f}'.format)
    today = context.current_dt.date()
    past = (today - dt.timedelta(120))

    stocks = get_all_securities(types=['stock'])
    forever = dt.date( 2200 ,  1 ,  1 )
    stocks = stocks[(stocks['end_date'] > today)&(stocks['start_date']>=past)].index
    all_stocks_with_name = get_all_securities(date=today)[['display_name']]

    prices = get_price(list(stocks), end_date=today, count = 120, fields=['high', 'close', 'low'])
    valid_stocks = prices['close'].isnull().sum() < 100
    stocks = stocks[valid_stocks]
    closes = prices['close']
    highs = prices['high']
    lows = prices['low']

    _, atr = ta.ATR(list(stocks), context.previous_date, timeperiod=20)

    holding_securities = list(context.portfolio.positions.keys())

    for s in stocks:
        try:
            high_date = highs[s].dropna()[1:].idxmax()
        except:
            continue

        dates_from_high = t.get_trading_day_num_from(high_date, context.previous_date)
        high = highs[s].max()
        low_s = lows[s][-dates_from_high:]
        low = low_s.min()
        low_date = low_s.idxmin()
        close = closes[s][-1]

        #print(s, close, high, close * 100 / high )
        if close < high * 0.6 and close < low * 1.1:
            dates_from_low = t.get_trading_day_num_from(low_date, context.previous_date)
            if dates_from_low > 20:
                print((s, low_date,  dates_from_low))
                '''
                close_ma39 = pd.rolling_mean(closes, 39)

                if s not in holding_securities:
                    if (closes[s][-1] > close_ma39[s][-1] and closes[s][-2] < close_ma39[s][-2]):
                        buy_cash = get_buy_one_unit(context, closes[s], atr[s])
                        buy_security(context, s, buy_cash)
                else:
                    max_value = context.portfolio.total_value * 0.1
                    if max_value - context.portfolio.positions[s].value > 10000:
                        units = (closes[s][-1] - g.last_buy[s]) * 2 / atr_secutiry
                        if units > 0.9:
                            buy_cash = get_buy_one_unit(context, closes[s], atr[s]) * units
                            #print(('buy', s))
                            if buy_cash > max_value - context.portfolio.positions[s].value:
                                buy_cash = max_value - context.portfolio.positions[s].value
                                buy_security(context, s, buy_cash)
                '''

def buy_security(context, security, value):
    order_value(security, value)

def get_buy_one_unit(context, closes, atr):
    factor = 0.001
    if closes[-1] < max(closes[-240:]) * 0.8:
        factor = 0.003
    elif closes[-1] < min(closes[-240:]) * 1.2:
        factor = 0.003

    factor = 0.001

    return context.portfolio.total_value * (closes[-1] / atr) * factor

def market_open(context):
    pass

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
