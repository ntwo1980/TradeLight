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
    past = (today - dt.timedelta(1100))

    stocks = get_all_securities(types=['stock'])
    forever = dt.date( 2200 ,  1 ,  1 )
    stocks = stocks[(stocks['end_date'] > today)&(stocks['start_date']<=past)]
    all_stocks_with_name = get_all_securities(date=today)[['display_name']]

    prices = get_price(list(stocks.index), end_date=today, count = 301, fields=['close', 'low'])
    closes = prices['close']
    closes_M = pd.DataFrame(closes.asfreq('M', method='ffill'))
    stat = closes_M.pct_change().dropna().apply(count_positive_count)
    stat.sort(ascending=False)

    df = pd.DataFrame({'positive_count': stat}).head(int(len(stocks) * 0.1))

    close_ma39 = pd.rolling_mean(closes, 39)
    close_ma60 = pd.rolling_mean(closes, 60)

    above_ma39_count = {s:(closes[s][-240:] > close_ma39[s][-240:]).sum() for s in closes.columns}
    above_ma39_count = pd.DataFrame.from_dict(above_ma39_count, orient='index')
    above_ma39_count.columns = ['above_ma39_count']

    above_ma60_count = {s:(closes[s][-240:] > close_ma60[s][-240:]).sum() for s in closes.columns}
    above_ma60_count = pd.DataFrame.from_dict(above_ma60_count, orient='index')
    above_ma60_count.columns = ['above_ma60_count']

    df = df.join(all_stocks_with_name).join(above_ma39_count).join(above_ma60_count)
    df = df.reindex(columns = ['display_name', 'positive_count', 'above_ma39_count', 'above_ma60_count'])

    print(df)


def market_open(context):
    pass

def after_market_close(context):
    pass
