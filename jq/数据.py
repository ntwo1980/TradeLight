# 导入函数库
import jqdata
import datetime as dt
import pandas as pd
import mytrade as t
import talib

# 初始化函数，设定要操作的股票、基准等等
def initialize(context):
    # 000001(股票:平安银行)
    g.security = '000001.XSHE'
    # 设定沪深300作为基准
    set_benchmark('000300.XSHG')
    # 开启动态复权模式(真实价格)
    set_option('use_real_price', True)
    run_daily(stat, time='morning')

def count_positive_count(values):
    return sum(x>0 for x in values)

# 每个单位时间(如果按天回测,则每天调用一次,如果按分钟,则每分钟调用一次)调用一次
def stat(context):
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

    prices = get_price(list(stocks.index), end_date=today, count = 750, fields=['close'])['close']
    prices_M = pd.DataFrame(prices.asfreq('M', method='ffill'))
    stat = prices_M.pct_change().dropna().apply(count_positive_count)
    stat.sort(ascending=False)

    df = pd.DataFrame({'positive_count': stat}).head(int(len(stocks) * 0.1))
    stocks = list(df.index)
    stock_prices = prices[-90:]
    linears = {s: t.get_linear(talib.EMA(np.array(stock_prices[s]), timeperiod=20)[-19:])[0] for s in stocks}
    linears = pd.DataFrame.from_dict(linears, orient='index')
    linears.columns = ['slop']
    prices_ma = pd.rolling_mean(stock_prices, 39)
    above_ma_count = {s:(stock_prices[s] > prices_ma[s][-90:]).sum() for s in stocks}
    above_ma_count = pd.DataFrame.from_dict(above_ma_count, orient='index')
    above_ma_count.columns = ['above_ma_count']

    above_ma = {s:(stock_prices[s][-1] / prices_ma[s][-1:]) for s in stocks}
    above_ma = pd.DataFrame.from_dict(above_ma, orient='index')
    above_ma.columns = ['above_ma']

    fundamentals_list = []
    for i in range(0, 36):
        statDate = t.shift_trading_day(today, -21 * i)
        fundamentals = get_fundamentals(query(valuation.code,
            indicator.inc_operation_profit_year_on_year,
            valuation.pe_ratio,
            valuation.pb_ratio,
            valuation.ps_ratio,
            valuation.pcf_ratio,
            balance.statDate
        ).filter(
            indicator.code.in_(stocks)
        ), statDate)
        fundamentals = fundamentals.set_index(['code'])
        fundamentals.columns = ['inc', 'pe', 'pb', 'ps', 'pcf', 'statDate']
        fundamentals['peg'] = fundamentals['pe'] / fundamentals['inc']
        fundamentals_list.append(fundamentals)

    df_stat = pd.DataFrame()
    for factor in ['pe', 'pb', 'ps', 'pcf']:
        sum = fundamentals_list[0][factor]
        for j in range(1, len(fundamentals_list)):
            sum = sum + fundamentals_list[j][factor]
        df_stat[factor + '_pct'] = fundamentals_list[0][factor] / (sum / len(fundamentals_list))

    df = df.join(all_stocks_with_name).join(linears).join(above_ma_count).join(above_ma).join(fundamentals_list[0]).join(df_stat)
    df = df.reindex(columns = ['display_name', 'positive_count', 'slop', 'above_ma_count', 'above_ma', 'statDate', 'inc', 'pe', 'peg', 'pe_pct', 'pb', 'pb_pct', 'ps', 'ps_pct', 'pcf', 'pcf_pct'])
    #print(df)
    if context.run_params.type == "simple_backtest":
        print(df)
        write_file('data.csv', df.to_csv(header=True, index_label='code'), append=False)
    else:
        write_file('data.csv', df.to_csv(header=True, index_label='code'), append=False)

