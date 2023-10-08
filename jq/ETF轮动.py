# 导入函数库
import jqdata
import mytrade as t
import pandas as pd
import talib
import math
import jqlib.technical_analysis as ta


def set_permanet_params(context):
    g.max_total_value = 0
    g.max_total_value_date = None
    g.prev_stop_lose_date = None
    g.prev_buy_date = None

def initialize(context):
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    set_permanet_params(context)


# 每个单位时间(如果按天回测,则每天调用一次,如果按分钟,则每分钟调用一次)调用一次
def handle_data(context, data):
    securities = [
        '159869.XSHE', # 游戏
        '510330.XSHG', # 沪深300
        '512690.XSHG', # 酒
        '512480.XSHG', # 半导体
        '516160.XSHG', # 新能源
        '515980.XSHG', # 人工智能
        '515120.XSHG', # 创新药
        '515700.XSHG', # 新能源车
        #'516780.XSHG', # 稀土
        #'512400.XSHG', # 有色金属
    ]
    money_security = "511880.XSHG"
    prices = get_price(securities,  end_date=context.previous_date, fields='close', frequency='daily',count=100)['close'].dropna(axis=1)
    prices_up = (prices.iloc[-1] / prices.iloc[-20])
    prices_up_count = sum(prices[-21:].pct_change() > 0)
    linears = {s: t.get_linear(talib.EMA(np.array(prices[s]), timeperiod=20)[-19:]) for s in prices.columns}
    (slop_300, _, _, _, _) = linears['510330.XSHG']
    '''
    buy_security_slop = -100
    for key in linears.keys():
        linear = linears[key]
        (slop, intercept, rvalue, pvalue, std_err) = linear
        if slop > buy_security_slop:
            buy_security_slop = slop
            buy_security = key
    '''
    prices_ma = pd.rolling_mean(prices, 39)
    security_above_ma = {s:(prices[s][-90:] > prices_ma[s][-90:]).sum()  for s in prices.columns}
    holding_securities = list(context.portfolio.positions.keys())
    holding_security = None
    if len(holding_securities) > 0:
        holding_security = holding_securities[0]
    #buy_security = prices_up[prices_up.index != '510330.XSHG'].idxmax()
    buy_security = prices_up.idxmax()

    (slop, intercept, rvalue, pvalue, std_err) = linears[buy_security]
    if '510330.XSHG' in security_above_ma:
        above_ma_count_300 = security_above_ma['510330.XSHG']
    else:
        above_ma_count_300 = 45
    above_ma_count = security_above_ma[buy_security]

    #stop_lose = context.portfolio.total_value < g.max_total_value * 0.9
    #reset_stop_lose = False
    #if stop_lose:
    #    print('total stop lose')
    #    reset_stop_lose = True
    #position = None
    stop_lose = False
    if holding_security:
        position = context.portfolio.positions[holding_security]
        #_, atr = ta.ATR(holding_securities,context.previous_date, timeperiod=10)
        #print((holding_security, atr[holding_security], position.avg_cost, position.avg_cost - atr[holding_security] * 3, position.price))
        #stop_lose = position.price < position.avg_cost - atr[holding_security] * 3
        stop_lose = position.price < position.avg_cost * 0.9

        '''
        if not stop_lose and slop_300 < 0 and position.price > position.avg_cost * 1.3:
            all_securities = get_all_securities(types=['stock'], date=context.current_dt)
            all_securities = t.set_feasible_stocks(all_securities.index, 21, context.current_dt)
            total_count = len(all_securities)
            closes = get_price(all_securities, count = 21, end_date = context.current_dt, fields=['close'])['close']
            down = closes.apply(lambda x: x[-1] < max(x) * 0.9 and x[-1] < x[-5]).dropna(axis=0, how='all')
            down_pct = down.sum() * 100 / total_count

            stop_lose = down_pct > 50
        '''


    if holding_security and stop_lose:
        print('stop lose: ' + holding_security)

        g.prev_stop_lose_date = context.current_dt.date()
        for s in holding_securities:
            order_target_value(s, 0, LimitOrderStyle(prices.iloc[-1][s]))

        g.max_total_value = context.portfolio.total_value
    #elif holding_security and buy_security != holding_security and position.price > position.avg_cost * 1.1 and linears[holding_security] < 100:
    #    for s in holding_securities:
    #        order_target_value(s, 0, LimitOrderStyle(prices.iloc[-1][s]))
    #elif holding_security and t.shift_trading_day(context.previous_date, -20) > g.prev_buy_date \
    #    and context.portfolio.positions[holding_security].price < context.portfolio.positions[holding_security].avg_cost * 1.02:
    #        for s in holding_securities:
    #            order_target_value(s, 0, LimitOrderStyle(prices.iloc[-1][s]))
    else:
        if prices_up[buy_security] > 1 \
            and slop_300 > -5 \
            and not holding_security:
            if buy_security not in holding_securities:
                for s in holding_securities:
                    order_target_value(s, 0, LimitOrderStyle(prices.iloc[-1][s]))

                if prices[buy_security][-1] < prices[buy_security][-3] * 1.05 \
                    and prices[buy_security][-2] * 0.97 < prices[buy_security][-1] < prices[buy_security][-2] * 1.03 \
                    and (g.prev_stop_lose_date is None \
                    or t.shift_trading_day(context.previous_date, -3) > g.prev_stop_lose_date):
                    order_target_value(buy_security, context.portfolio.available_cash, LimitOrderStyle(prices.iloc[-1][buy_security]))
                    g.prev_buy_date = context.current_dt.date()
        elif prices_up[buy_security] < 0.98:
            for s in holding_securities:
                order_target_value(s, 0, LimitOrderStyle(prices.iloc[-1][s]))

    if context.portfolio.total_value > g.max_total_value:
        g.max_total_value = context.portfolio.total_value
        g.max_total_value_date = context.current_dt
