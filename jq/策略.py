import operator
import sys
import datetime as dt
import numpy as np
import pandas as pd
import time
import talib
import random
import jqdata
import prettytable as pt
import mytrade as t
import jqlib.technical_analysis as ta
import warnings
from scipy import stats
from dateutil.relativedelta import *

warnings.filterwarnings("ignore")

def initialize(context):
    set_benchmark('000905.XSHG')
    set_option('use_real_price', True)
    #log.set_level('order', 'error')
    set_permanet_params(context)

    run_daily(before_market_open, time='before_open')
    run_daily(market_open, time='open')
    run_daily(after_market_close, time='after_close')
    run_daily(stat, time='morning')

def set_permanet_params(context):
    g.default_trade_day = 1
    g.trade_day = g.default_trade_day
    g.use_hl_index = False
    g.use_xp_index = False
    g.last_buy_day = None
    g.exact_last_buy_day = None
    g.cash_last_buy = None
    g.last_win_day = None
    g.last_win_total = None
    g.prev_stop_lose_date = None
    g.days_since_last_buy = None
    g.buy_orders = {}
    g.stock_max_price = {}
    g.holding_day_count = 0
    g.max_total_value = 0
    g.max_total_value_date = None
    g.prev_total_value = 0
    g.prev_buy_total_value = 0

def set_session_params(context):
    if t.trade_day is not None:
        g.trade_day = t.trade_day
    if t.default_trade_day is not None:
        g.default_trade_day = t.default_trade_day
    if t.trade_day is not None:
        g.trade_day = t.trade_day
    g.stop_win_day = g.default_trade_day + 22
    if g.stop_win_day > 30:
        g.stop_win_day = g.stop_win_day - 30
    g.stop_win_day = 40
    if t.use_hl_index is not None:
        g.use_hl_index = t.use_hl_index
    #g.trade_day = 30
    g.fundamental_selector_config = t.fundamental_selector_config
    g.xp_fundamental_selector_config1 = t.xp_fundamental_selector_config1
    g.xp_fundamental_selector_config2 = t.xp_fundamental_selector_config2

    g.exclude_industries = [
            'A02',     # 林业
            'C17',     # 纺织业
            'C21',     # 家具制造业
            'C27',     # 医药制造业
            'H61',     # 住宿业
            'H62',     # 餐饮业
            'M74',     # 专业技术服务业
            'R85',     # 新闻和出版业
            '850131',  # 林业III
            '851521',  # 中药III
            '852031',  # 百货III
            '801178',  # 物流II
        ]
    g.exclude_industries_low_slop = [
            '801160',  # 公用事业I
    ]
    g.days_above_ma = 0
    g.cyclical_industries = ['801020', '801040', '801050', '801143', '801711', '801011']
    g.treat_index_fall_a_lot = t.treat_index_fall_a_lot
    g.treat_stop_lose = t.treat_stop_lose
    g.index_fall_a_lot = False
    g.trading_days_of_last_month = None
    g.shift = 21
    g.prioritize_hl_stocks = True
    g.min_stock_money = 20000000
    g.max_stock_price = 10000
    g.min_stocks_to_buy = 5
    g.max_stocks_to_buy = 10
    g.stop_lose_total_threshold = 0.89
    g.stop_force = False
    g.stock_stop_lose_percentage = 0.9
    g.factors = None
    g.factor = None
    g.mandatory_month = [2]
    g.forbidden_month = [6]
    g.dangerous_month = [1, 6, 12]
    g.trading_postponed = False
    g.spring_festival_buy = True
    g.trading_spring_festival = False
    g.all_stocks = None
    g.is_bear_market = False
    g.index_slop = 0
    g.hl_index_slop = 0
    g.bear_market_slop = -10
    g.hl_bear_market_slop = -10
    g.bear_stock_slop = -15
    g.hl_check_slop = 0
    g.hl_check_diff = 5
    g.hl_check_max_slop = 50
    g.rebalance_return_ok = 1
    g.buy_stock = []
    g.sell_stock = []
    g.atr_stop_win = True
    g.buy_in_fall = False
    g.yy_index_slop = 0
    g.bj_index_slop = 0
    g.xny_index_slop = 0
    g.ys_index_slop = 0
    g.mt_index_slop = 0
    g.xp_index_slop = 0
    g.prefer_hl = False
    g.hbjj = '511880.XSHG'
    g.xf_index_slop = -100
    if context.run_params.type == "simple_backtest" or context.run_params.type == "full_backtest":
        g.print_candidates = False
        g.shuffle_list = False
        g.min_trade_amount = 0
        g.min_hl_trade_amount = 0
    else: # context.run_params.type == "live_trade"
        g.print_candidates = True
        g.shuffle_list = True
        g.min_trade_amount = 25000
        g.min_hl_trade_amount = 100000

def stat(context):
    set_session_params(context)

    holding_stocks = list(context.portfolio.positions.keys())
    not_holding_stocks = [s for s in g.stock_max_price if s not in holding_stocks]
    for s in not_holding_stocks:
        del g.stock_max_price[s]

    schduler = t.EverydayTradeScheduler(g, context, lambda: everyday_trade(context), 1)
    schduler.trade()

    if g.if_trade and not g.trading_postponed and g.feasible_stocks:
        (rebalance_status, to_hold_stocks, feasible_stocks) = rebalance(context, get_factors(g.feasible_stocks, context, g.factors))
        restore_backup = False
        print("stocks count is " + str(len(feasible_stocks)))
        if (not g.use_hl_index  and len(feasible_stocks) < g.min_stocks_to_buy * 3) or (g.hl_index_slop > 0 and g.prefer_hl):
            print("stocks count is " + str(len(feasible_stocks)) + " try hl stocks" )
            rebalance_status_backup = rebalance_status
            to_hold_stocks_backup = to_hold_stocks
            use_hl_index_backup = g.use_hl_index
            g.use_hl_index = True
            set_hl_feasible_stocks(context)

            if len(g.feasible_stocks):
                (rebalance_status, to_hold_stocks, feasible_stocks) = rebalance(context, get_factors(g.feasible_stocks, context, g.factors))
                if rebalance_status != g.rebalance_return_ok or len(feasible_stocks)  < g.min_stocks_to_buy:
                    restore_backup = True
            else:
                restore_backup = True
        elif g.use_hl_index and not feasible_stocks:
            set_feasible_stocks(context, False)
            if g.feasible_stocks:
                (rebalance_status, to_hold_stocks, feasible_stocks) = rebalance(context, get_factors(g.feasible_stocks, context, g.factors))

        if restore_backup:
            rebalance_status = rebalance_status_backup
            to_hold_stocks = to_hold_stocks_backup
            g.use_hl_index = use_hl_index_backup

        if rebalance_status == g.rebalance_return_ok:
            all_stocks_index = list(g.all_stocks.index)

            # 空仓只有买入操作
            if not list(context.portfolio.positions.keys()):
                if len(to_hold_stocks) >= g.min_stocks_to_buy:
                    for stock in to_hold_stocks:
                        g.buy_stock.append(stock)
            else:
                for stock in holding_stocks:
                    if stock not in to_hold_stocks and stock not in g.sell_stock:
                        g.sell_stock.append(stock)

                if len(to_hold_stocks) >= g.min_stocks_to_buy:
                    for stock in [s for s in to_hold_stocks if s not in holding_stocks]:
                        g.buy_stock.append(stock)

            to_sell_stocks = [(s, g.all_stocks.iloc[all_stocks_index.index(s)]['display_name'] if s in all_stocks_index else '') for s in g.sell_stock]
            to_buy_stocks = [(s, g.all_stocks.iloc[all_stocks_index.index(s)]['display_name'] if s in all_stocks_index else '') for s in g.buy_stock]

            msg = 'slop:{}|sell:{}|buy:{}'.format(g.index_slop,repr(to_sell_stocks).decode('unicode-escape'), repr(to_buy_stocks).decode('unicode-escape'))
            #msg = 'slop:{}|sell:{}|buy:{}'.format(g.index_slop,to_sell_stocks, to_buy_stocks)

            print(msg)
            send_message(msg)

def rebalance(context, df_all):
    current_year = context.current_dt.year
    current_month = context.current_dt.month
    current_day = context.current_dt.day
    is_mandatory_month = is_month_mandatory_month(current_month)
    sorted_by = g.factor + '_' + 'sorted_rank'
    holding_list = list(df_all.sort(sorted_by, ascending = True).index)

    prices_data = get_price(holding_list,
               count = 130,
               end_date = context.previous_date,
               frequency = 'daily',
               fields = ['close', 'volume', 'money'])

    original_holding_list = holding_list[:]
    stock_close = prices_data['close']
    stock_prices = stock_close[-50:]
    stock_volumes = prices_data['volume'][-50:]
    stock_money = prices_data['money'][-50:]
    stock_returns = prices_data['close'][-50:].pct_change()
    prices_data_ma = pd.rolling_mean(stock_close, 39)
    stock_above_ma = {s:(stock_close[s][-90:] > prices_data_ma[s][-90:]).sum()  for s in stock_close.columns}

    rsis = {s: talib.RSI(np.array(stock_prices[s]), timeperiod=5)[-1] for s in holding_list}
    min_slop = min(g.index_slop * 1.2 if g.index_slop < 0 else g.index_slop, g.bear_stock_slop)

    holding_list = [s for s in holding_list if stock_prices[s][-1] < g.max_stock_price]
    linears = {s: t.get_linear(talib.EMA(np.array(stock_prices[s]), timeperiod=20)[-19:]) for s in holding_list}
    len1= len([s for s in linears if linears[s][0] > min_slop])

    if len1 < g.min_stocks_to_buy:
        linears1 = {s: t.get_linear(stock_prices[s][-g.trading_days_of_last_month:]) for s in holding_list}
        len2= len([s for s in linears1 if linears1[s][0] > min_slop])
        if len2 > len1:
            linears = linears1

    holding_list_linears = [s for s in holding_list if (g.index_fall_a_lot
        or linears[s][0] > min_slop)
        and min(stock_prices[s][-5:]) > min(stock_prices[s][-g.trading_days_of_last_month:])]

    if (not is_mandatory_month or len(holding_list_linears) > g.min_stocks_to_buy) and not g.buy_in_fall and not g.trading_spring_festival:
        holding_list = holding_list_linears
    else:
        holding_list = holding_list_linears + [s for s in holding_list if s not in holding_list_linears]

    print(holding_list)

    if not g.use_hl_index and g.index_slop < 12:
        stock_prices_returns = prices_data['close'].pct_change()
        stocks_returns_var = stock_prices_returns.var()

        holding_list = [s for s in holding_list if  stocks_returns_var.ix[s] > 0.0002]
    '''
    if not g.use_hl_index and len(holding_list) > 30 and g.index_slop < 0:
        stock_money_avg = stock_money[-20:].mean()
        stock_money_avg.sort()
        least_money_stocks = stock_money_avg[:int(len(holding_list) * 0.1)].index
        holding_list = [s for s in holding_list if s not in least_money_stocks]
    '''

    if not g.use_hl_index and len(holding_list) > 30:
        stock_money_avg = stock_money[-20:].mean()
        excluded_stock_money = stock_money_avg[stock_money_avg < g.min_stock_money]
        holding_list = [s for s in holding_list if s not in excluded_stock_money.index]

    #holding_list = [s for s in holding_list if stock_prices[s][-1] < stock_prices[s][-20:].mean() * 1.4]

    if g.use_hl_index:
        for threshold in [40, 30, 20, 10, 0]:
            tmp_holding_list = [s for s in holding_list if stock_above_ma[s] > threshold]
            if len(tmp_holding_list) > g.min_stocks_to_buy:
                holding_list = tmp_holding_list
                break

    locked_shares = get_locked_shares(stock_list=holding_list, start_date=context.current_dt, forward_count=60)['code']
    holding_list = [s for s in holding_list if s not in locked_shares]

    all_stocks_index = list(g.all_stocks.index)
    if holding_list:
        x = pt.PrettyTable(["code", "name", "slop", "intercept", 'rvalue', 'pvalue', 'std_err', 'rsi'])
        for s in holding_list:
            name = g.all_stocks.iloc[all_stocks_index.index(s)]['display_name']
            linear = linears[s]
            (slop, intercept, rvalue, pvalue, std_err) = linear
            rsi = rsis[s]
            #print  list(g.all_stocks.index).index(s)
            x.add_row([s, name, slop, intercept, rvalue, pvalue, std_err, rsi])

        if g.trade_day == 'all' or g.print_candidates:
            print(x)

    num_stocks = len(holding_list)
    if g.max_stocks_to_buy > 0 and num_stocks > g.max_stocks_to_buy:
        num_stocks = g.max_stocks_to_buy

    if num_stocks < g.min_stocks_to_buy:
        holding_list = []

    if not g.use_hl_index and len(holding_list) < 12:
        zq_stocks = {s for industry in g.cyclical_industries for s in get_industry_stocks(industry, date=context.previous_date)}

        if len(zq_stocks & set(holding_list)) > len(holding_list) / 2:
            holding_list = []

    if (g.is_bear_market and not g.buy_in_fall and not g.trading_spring_festival) or not holding_list:
        return (g.rebalance_return_ok, [], [])

    '''
    zq = check_zq_industry(context)
    if zq:
        if zq in holding_list:
            holding_list.remove(zq)
        holding_list.insert(0, zq)
    '''

    operate_stock_list =  holding_list[:num_stocks]
    to_buy_stocks = [(s, g.all_stocks.iloc[all_stocks_index.index(s)]['display_name'] if s in all_stocks_index else '') for s in holding_list]

    if context.run_params.type == "live_trade":
        msg = 'buy:{}'.format(repr(to_buy_stocks).decode('unicode-escape'))
        print(msg)

    return (g.rebalance_return_ok, operate_stock_list, holding_list)

def check_zq_industry(context):
    if context.previous_date < dt.datetime(2015,3, 1).date():
        return None

    index_prices = get_price(
        '399987.XSHE',
        count = 60,
        end_date = context.previous_date,
        frequency = 'daily',
        fields = 'close')['close']

    index_ma = pd.rolling_mean(index_prices, 39)

    if sum(index_prices[-21:] > index_ma[-21:]) < 21 and not g.index_fall_a_lot:
        return None

    return '600519.XSHG'

def everyday_trade(context):
    t.set_slip_fee(context.current_dt)
    if g.treat_index_fall_a_lot and not g.last_buy_day:
        g.last_buy_day = context.current_dt.date() - dt.timedelta(days=60)

    g.if_trade = False
    if g.last_buy_day is not None:
        g.days_since_last_buy =  t.get_trading_day_num_from(g.last_buy_day, context.previous_date)

    is_stop_lose = stop_win_lose(context)
    current_year = context.current_dt.year
    current_month = context.current_dt.month
    current_day = context.current_dt.day
    last_month = 12 if current_month == 1 else current_month - 1
    first_day_of_last_month = dt.date(current_year - 1 if current_month == 1 else current_year,  12 if current_month == 1 else current_month - 1, 1)
    g.trading_days_of_last_month = t.get_trading_day_num_from(first_day_of_last_month, context.previous_date)
    if g.trading_days_of_last_month > 25:
        g.trading_days_of_last_month = g.shift

    if not is_stop_lose \
        or (is_month_mandatory_month(current_month) and not g.treat_stop_lose):
        if (g.days_since_last_buy is None or g.days_since_last_buy >= 10) and (current_month not in g.dangerous_month \
            or g.prev_stop_lose_date is None \
            or t.shift_trading_day(context.previous_date, -5) > g.prev_stop_lose_date):
            scheduler = t.MonthDayTradeScheduler(g, context, lambda: set_feasible_stocks(context, True), g.trade_day)
            scheduler.trade()

    if not g.if_trade and g.spring_festival_buy and len(context.portfolio.positions.keys()) < g.min_stocks_to_buy:
        schduler = t.SpringFestivalTradeScheduler(g, context, lambda: set_feasible_stocks(context, True), 3)
        #g.buy_in_fall = True
        schduler.trade()

        if g.if_trade:
            g.trading_spring_festival = True
            print("spring festival buy")

def set_feasible_stocks(context, check_hl_index):
    current_year = context.current_dt.year
    current_month = context.current_dt.month
    current_day = context.current_dt.day
    g.use_hl_index = False
    g.use_xp_index = False

    if context.previous_date >= dt.datetime(2013,1, 1).date():
        indexes = [
            '399001.XSHE',   # 深证成指 0
            '399006.XSHE',   # 创业板指 1
            '399550.XSHE',   # 央视50   2
            '000905.XSHG',   # 中证500  3
            '399316.XSHE',   # 巨潮小盘 4
            '000932.XSHG',   # 中证消费 5
            '399989.XSHE',   # 中证医疗 6
            '399997.XSHE',   # 中证白酒 7
            '399551.XSHE',   # 科技100  8
            '000001.XSHG',   # 上证指数 9
            '000016.XSHG',   # 上证50 10
            '399976.XSHE',	 # 中证新能源汽车 11
            '000819.XSHG',	 # 有色 12
            '000820.XSHG',	 # 煤炭 13
        ]
    else:
        indexes = [
            '399001.XSHE',   # 深证成指 0
            '399006.XSHE',   # 创业板指 1
            '000932.XSHG',   # 中证消费 2
            '000905.XSHG',   # 中证500  3
            '399316.XSHE',   # 巨潮小盘 4
            '000932.XSHG',   # 中证消费 5
            '399989.XSHE',   # 中证医疗 6
            '399997.XSHE',   # 中证白酒 7
            '399551.XSHE',   # 科技100  8
            '000001.XSHG',   # 上证指数 9
            '000016.XSHG',   # 上证50 10
            '399976.XSHE',	 # 中证新能源汽车 11
            '000819.XSHG',	 # 有色 12
            '000820.XSHG',	 # 煤炭 13
        ]

    index_prices = get_price(
       indexes,
       count = 240,
       end_date = context.previous_date,
       frequency = 'daily',
       fields = 'close')['close']

    index_fall_a_lot_days = g.days_since_last_buy if not g.days_since_last_buy is None and g.days_since_last_buy > 30 else 21
    if index_prices.ix[-index_fall_a_lot_days, 0] > index_prices.ix[-1, 0] * 1.18 or g.treat_index_fall_a_lot:
        g.index_fall_a_lot = True
    else:
        g.index_fall_a_lot = False

    index_index = 0 if not g.index_fall_a_lot else 4
    if index_prices.ix[-2, index_index] / index_prices.ix[-1, index_index] > 1.01:
        if g.trading_spring_festival:
            g.trading_postponed = True
            return
        elif current_day < 10:
            postpone_trading(context)
            return

    g.trade_day = g.default_trade_day
    is_mandatory_month = is_month_mandatory_month(current_month)
    g.all_stocks = get_all_securities(types=['stock', 'fund'], date=context.previous_date)[['display_name']]
    current_stocks = get_all_securities(date=context.previous_date)
    past_stocks = get_all_securities(date=t.shift_trading_day(context.previous_date, -21))
    is_new_stocks = len(current_stocks.index) / len(past_stocks.index) > 1.0001

    all_stocks = [s for s in current_stocks.index if not str(s).startswith('300') and not str(s).startswith('688')]
    #all_stocks = [s for s in current_stocks.index]

    hl_index_price = index_prices.ix[:, 2]
    index_500_price = index_prices.ix[:, 3]
    index_price = index_prices.ix[:, 3]
    xf_index_price = index_prices.ix[:, 5]
    yy_index_price = index_prices.ix[:, 6]
    bj_index_price = index_prices.ix[:, 7]
    xp_index_price = index_prices.ix[:, 4]
    sz_index_price = index_prices.ix[:, 9]
    xny_index_price = index_prices.ix[:,11]
    ys_index_price = index_prices.ix[:,12]
    mt_index_price = index_prices.ix[:,12]

    (g.index_slop, _, _, _, _) = t.get_linear(index_price[-g.trading_days_of_last_month:])
    (g.hl_index_slop, _, _, _, _) = t.get_linear(hl_index_price[-g.trading_days_of_last_month:])
    (g.xf_index_slop, _, _, _, _) = t.get_linear(xf_index_price[-g.trading_days_of_last_month:])
    (g.yy_index_slop, _, _, _, _) = t.get_linear(yy_index_price[-g.trading_days_of_last_month:])
    (g.bj_index_slop, _, _, _, _) = t.get_linear(bj_index_price[-g.trading_days_of_last_month:])
    (g.xp_index_slop, _, _, _, _) = t.get_linear(xp_index_price[-g.trading_days_of_last_month:])
    (sz_index_slop, _, _, _, _) = t.get_linear(sz_index_price[-g.trading_days_of_last_month:])
    (g.xny_index_slop, _, _, _, _) = t.get_linear(xny_index_price[-g.trading_days_of_last_month:])
    (g.ys_index_slop, _, _, _, _) = t.get_linear(ys_index_price[-g.trading_days_of_last_month:])
    (g.mt_index_slop, _, _, _, _) = t.get_linear(mt_index_price[-g.trading_days_of_last_month:])

    print({'index': g.index_slop, 'xf': g.xf_index_slop, 'yy': g.yy_index_slop, 'xny':g.xny_index_slop, 'hl': g.hl_index_slop, 'xp': g.xp_index_slop})

    if g.xf_index_slop > g.hl_index_slop:
        g.hl_index_slop = g.xf_index_slop
        hl_index_price = xf_index_price

    if g.yy_index_slop > g.hl_index_slop:
        g.hl_index_slop = g.yy_index_slop
        hl_index_price = yy_index_price

    if g.xp_index_slop > 0 \
        and g.xp_index_slop > sz_index_slop \
        and xp_index_price[-g.trading_days_of_last_month:].max() == xp_index_price[-120:].max():
        g.use_xp_index = True
        g.index_slop = g.xp_index_slop
        index_price = xp_index_price
        print("use xp")

    interval = 120
    threshold = 0.2
    g.prioritize_hl_stocks = (xf_index_price[-1] / xf_index_price[-interval]) - (index_500_price[-1] / index_500_price[-interval]) < threshold
    #g.prioritize_hl_stocks = True
    g.is_bear_market = (g.index_slop < g.bear_market_slop or \
        (check_hl_index and g.prioritize_hl_stocks and g.xf_index_slop > g.hl_bear_market_slop and not g.index_fall_a_lot and g.xf_index_slop < g.hl_check_max_slop) or \
        (check_hl_index and g.xf_index_slop > g.hl_bear_market_slop and not g.index_fall_a_lot and g.hl_index_slop > g.index_slop + g.hl_check_diff and g.index_slop < g.hl_check_slop and g.hl_index_slop < g.hl_check_max_slop)) and \
        not is_mandatory_month and g.trade_day != 'all'
    #g.is_bear_market = True
    index_ma = pd.rolling_mean(index_prices.ix[:, 0], 39)
    g.days_above_ma = (index_prices.ix[-90:, 0] > index_ma.ix[-90:]).sum()
    print("days above 39 ma in last 90 days: " + str(g.days_above_ma))
    if (index_prices.ix[-90:, 0] > index_ma.ix[-90:]).sum() < 20:
        g.is_bear_market = True
    elif g.is_bear_market and check_hl_index:
        g.index_slop =  g.hl_index_slop
        g.is_bear_market = g.index_slop < g.hl_bear_market_slop

        if not g.is_bear_market:
            g.use_hl_index = True

    if g.is_bear_market and current_month == 7:
        price_two_month_ago = get_price(
           indexes[3],
           count = 1,
           end_date = dt.datetime(current_year, 3, 31),
           frequency = 'daily',
           fields = 'close')['close']

        if index_prices.ix[-1:, 3][0] < price_two_month_ago[-1]:
            g.buy_in_fall = True

    if g.is_bear_market and is_month_mandatory_month(current_month):
        g.buy_in_fall = True

    if g.index_slop < 10:
        g.exclude_industries.extend(g.exclude_industries_low_slop)

    if not g.use_hl_index:
        print("no use hl")
        selector = t.NotIndustrySecuritySelector(all_stocks, context.previous_date, g.exclude_industries)
        selector = t.NotNewSecuritySelector(selector.get_stocks(), context.previous_date, 120)
        selector = t.NotSTSecuritySelector(selector.get_stocks(), context.previous_date)
        selector = t.NotBlackListSecuritySelector(selector.get_stocks())
        not_black_list_securities = selector.get_stocks()

        if not g.index_fall_a_lot or g.buy_in_fall or g.trading_spring_festival:
            if g.use_xp_index:
                selector= t.FundamentalSecuritySelector(not_black_list_securities, context.previous_date,
                                    mc = g.xp_fundamental_selector_config1['mc'],
                                    pe = g.xp_fundamental_selector_config1['pe'],
                                    pb = g.xp_fundamental_selector_config1['pb'],
                                    ps = g.xp_fundamental_selector_config1['ps'],
                                    iop = g.xp_fundamental_selector_config1['iop'],
                                    facr = g.xp_fundamental_selector_config1['facr'])

                fundamental_stocks = selector.get_stocks()

                if len(fundamental_stocks) < 30:
                    selector= t.FundamentalSecuritySelector2(not_black_list_securities, context.previous_date,
                                    mc = g.xp_fundamental_selector_config2['mc'],
                                    pe = g.xp_fundamental_selector_config2['pe'],
                                    pb = g.xp_fundamental_selector_config2['pb'],
                                    ps = g.xp_fundamental_selector_config2['ps'],
                                    iop = g.xp_fundamental_selector_config2['iop'],
                                    facr = g.xp_fundamental_selector_config2['facr'])

                    fundamental_stocks2 = selector.get_stocks()

                    if len(fundamental_stocks2) > len(fundamental_stocks) + 10:
                        fundamental_stocks = fundamental_stocks2
            else:
                selector= t.FundamentalSecuritySelector1(not_black_list_securities, context.previous_date,
                                    mc = g.fundamental_selector_config['mc'],
                                    pb = g.fundamental_selector_config['pb'],
                                    iop = g.fundamental_selector_config['iop'],
                                    roic = g.fundamental_selector_config['roic'])

                fundamental_stocks = selector.get_stocks()
        else:
            print("index fall a lot")
            (min_close, max_close) = t.get_turning_point(index_prices.ix[:,0], 40)
            falling_day = g.last_buy_day

            if max_close.size and (not falling_day or max_close.index[-1].date() < falling_day):
                falling_day = max_close.index[-1].date()

            selector = t.FallSecuritySelector(not_black_list_securities, falling_day, context.previous_date, 0.2)

            fundamental_stocks = selector.get_stocks()

        '''
        if g.ys_index_slop > 10:
            selector = t.StockIndicesSecuritySelector(['000819.XSHG'], context.previous_date)
            stocks = selector.get_stocks()

            fundamental_stocks = list(set(fundamental_stocks) | set(stocks))

        if g.mt_index_slop > 10:
            selector = t.StockIndicesSecuritySelector(['000820.XSHG'], context.previous_date)
            stocks = selector.get_stocks()

            fundamental_stocks = list(set(fundamental_stocks) | set(stocks))
        '''

        g.feasible_stocks = t.set_feasible_stocks(fundamental_stocks, g.shift, context.previous_date)
    else:
        print("use hl")
        set_hl_feasible_stocks(context)

    if len(g.feasible_stocks):
        set_factors(context)

def FundamentalSecuritySelector_get_stocks():
    pass

def set_hl_feasible_stocks1(context):
    selector= t.LongUpSecuritySelector(context.previous_date, 750, 0.1)
    stocks = selector.get_stocks()
    g.feasible_stocks = t.set_feasible_stocks(stocks, g.shift, context.previous_date)

def set_hl_feasible_stocks(context):
    indices = None
    exclude_bj = False

    if context.previous_date >= dt.datetime(2015,1, 21).date() and \
        (g.bj_index_slop < g.hl_bear_market_slop or g.bj_index_slop > 30):
        exclude_bj = True

    if context.previous_date >= dt.datetime(2013,1, 1).date():
        indices = ['399550.XSHE', '000932.XSHG']
        '''
        if g.xf_index_slop > 0:
            indices = ['399550.XSHE', '000932.XSHG']
        else:
            indices = ['399550.XSHE']
        '''
    else:
        indices = ['000932.XSHG']

    #if g.xny_index_slop > 0 and exclude_bj:
    #    indices.append('399976.XSHE')

    #if g.yy_index_slop > 0 and exclude_bj:
    #    indices.append('000933.XSHG')

    selector = t.StockIndicesSecuritySelector(indices, context.previous_date)
    stocks = selector.get_stocks()
    print(exclude_bj)
    if exclude_bj:
        bj_selector = t.StockIndicesSecuritySelector(['399997.XSHE'], context.previous_date)
        bj_stocks = bj_selector.get_stocks()
        #stocks = list(set(stocks) - set(bj_stocks))

    if g.yy_index_slop < g.xf_index_slop:
        selector = t.PegSecuritySelector(stocks, context.previous_date, 0.5, 50, True)
        stocks = selector.get_stocks()
    else:
        hl_stocks = []
        if g.xf_index_slop > 0:
            selector = t.PegSecuritySelector(stocks, context.previous_date, 0.3, 50, True)
            hl_stocks = selector.get_stocks()

        yy_stocks = []

        yy_selector = t.StockIndicesSecuritySelector(['399989.XSHE'], context.previous_date)
        yy_stocks = yy_selector.get_stocks()

        yy_peg_selector = t.PegSecuritySelector(yy_stocks, context.previous_date, 0.5, 300, True)
        yy_peg_stocks = selector.get_stocks()

        yy_pb_selector = t.PBHistorySelector(yy_stocks, context.previous_date, 400, 1)
        yy_stocks = list(set(yy_stocks) & set(yy_pb_selector.get_stocks()))

        stocks = hl_stocks + yy_stocks

    #selector= t.PBHistorySelector(stocks, context.previous_date, 400, 0.8)
    #stocks = list(set(selector.get_stocks()) & set(stocks1))

    last_year = context.current_dt.year - 1
    bank_fundamentals = get_fundamentals(query(
        bank_indicator.code,
        bank_indicator.non_performing_loan_provision_coverage,
    ).order_by(
        bank_indicator.non_performing_loan_provision_coverage.desc()
    ), statDate = last_year)

    bank_fundamentals = bank_fundamentals.dropna()
    all_banks = list(bank_fundamentals['code'])
    bank_count = len(all_banks)
    excluded_bank = []
    included_bank = []
    if bank_count > 15:
        excluded_bank = list(bank_fundamentals[int(bank_count / 3):]['code'])

    stocks = list(set(stocks) - set(excluded_bank))
    '''

    if g.yy_index_slop > -5 and g.bj_index_slop > -5:
        last_year = context.current_dt.year - 1
        bank_fundamentals = get_fundamentals(query(
            bank_indicator.code,
            bank_indicator.non_performing_loan_provision_coverage,
        ).order_by(
            bank_indicator.non_performing_loan_provision_coverage.desc()
        ), statDate = last_year)

        bank_fundamentals = bank_fundamentals.dropna()
        all_banks = list(bank_fundamentals['code'])
        stocks = list(set(stocks) - set(all_banks))
    '''
    g.feasible_stocks = t.set_feasible_stocks(stocks, g.shift, context.previous_date)

def set_factors(context):
    if g.index_fall_a_lot:
        days = g.days_since_last_buy if g.days_since_last_buy else g.shift
        g.factors = {
            'MTM'+str(days): (t.MtmStockFactor, {'data_type': 'price', 'prices_len': days}, {}, {'days': days, 'asc': True}),
        }
    else:
        g.factors = {
            'WeightVar': (t.WeightVarStockFactor, {'data_type': 'price', 'prices_len': g.shift + 1}, {}, {'days': g.shift, 'weight_days': 1,  'weight_factor': 1.5, 'asc': True})
        }

    if len(g.factors.keys()) == 1:
        g.factor = list(g.factors.keys())[0]

def postpone_trading(context):
    current_day = context.current_dt.day
    g.trade_day = current_day + 1
    g.feasible_stocks = []
    g.trading_postponed = True

    print("post trading day to " + str(g.trade_day))

def is_month_mandatory_month(month):
    return month in g.mandatory_month

def is_month_forbidden_month(date):
    month = date.month

    if not month in g.forbidden_month:
        return False

    index_prices = get_price(
        '399001.XSHE',
        count = 44,
        end_date = date,
        frequency = 'daily',
        fields = 'close')['close']

    return index_prices[-1] > index_prices[1]

def stop_win_lose(context):
    is_stop_lose = False
    today = context.current_dt
    current_year = today.year
    current_month = today.month
    current_day = today.day
    holding_stocks = list(context.portfolio.positions.keys())

    if context.portfolio.total_value == g.prev_total_value:
        g.holding_day_count = 0
    else:
        g.holding_day_count += 1

    prev_position_value = g.prev_total_value - g.cash_last_buy if g.cash_last_buy else 0
    g.prev_total_value = context.portfolio.total_value

    if(len(holding_stocks) == 0):
        return g.treat_stop_lose

    prices = get_price(holding_stocks,
               count = 30,
               end_date = context.previous_date,
               frequency = 'daily',
               fields = ['high', 'low', 'close'])
    last_return =  prices['close'].pct_change().iloc[-1]
    last_return.sort()
    most_down = last_return[:int(len(holding_stocks) * 0.8)]

    df = get_fundamentals(query(valuation.code,valuation.turnover_ratio
        ).filter(
            valuation.code.in_(holding_stocks)
        ), context.previous_date).set_index(['code'])

    all_down = current_month in g.dangerous_month \
        and current_day > 15 \
        and len(holding_stocks) > 5 \
        and mean(most_down) < -0.03 \
        and not g.use_hl_index

    days_since_max_value =  t.get_trading_day_num_from(g.max_total_value_date, context.previous_date) if g.max_total_value_date else 0
    days_since_stop_lose =  t.get_trading_day_num_from(g.prev_stop_lose_date, context.previous_date) if g.prev_stop_lose_date else 0

    if not all_down and g.treat_stop_lose:
        all_down = True

    if (not all_down
        and (context.portfolio.total_value < g.max_total_value * 0.95 or context.portfolio.total_value < g.prev_buy_total_value * 0.95)
        and len(holding_stocks) > 2
        and (days_since_stop_lose > 21 or not g.prev_stop_lose_date)):
        if g.use_hl_index and context.previous_date >= dt.datetime(2013,1, 1).date():
            for indices in [['399550.XSHE', '000932.XSHG'], ['000932.XSHG']]:
                if not all_down:
                    selector = t.StockIndicesSecuritySelector(indices, context.previous_date)
                    stocks = selector.get_stocks()
                    total_count = len(stocks)
                    closes = get_price(stocks, count = 21, end_date = today, fields=['close'])['close']
                    #down = closes.apply(lambda x: x[-1] < x[0] * 0.9 and x[-1] < x[-5]).dropna(axis=0, how='all')
                    down = closes.apply(lambda x: x[-1] < max(x) * 0.9 and x[-1] < x[-5]).dropna(axis=0, how='all')
                    down_pct = down.sum() * 100 / total_count

                    print("all hl down pct:" + str(down_pct))
                    if down_pct > 50:
                        all_down = True
        else:
            all_securities = get_all_securities(types=['stock'], date=context.current_dt)
            all_securities = t.set_feasible_stocks(all_securities.index, g.shift, context.current_dt)
            total_count = len(all_securities)
            closes = get_price(all_securities, count = 21, end_date = today, fields=['close'])['close']
            down = closes.apply(lambda x: x[-1] < max(x) * 0.9 and x[-1] < x[-5]).dropna(axis=0, how='all')
            down_pct = down.sum() * 100 / total_count
            print("all down pct:" + str(down_pct))
            if down_pct > 50:
                all_down = True

    if context.portfolio.total_value > g.max_total_value:
        g.max_total_value = context.portfolio.total_value
        g.max_total_value_date = today

    if context.portfolio.total_value < g.max_total_value * g.stop_lose_total_threshold \
        or all_down or g.stop_force:
        for stock in holding_stocks:
            print('{} stop loss1'.format(stock))
            g.sell_stock.append(stock)
        holding_stocks = []
        g.stock_max_price = {}

        g.max_total_value = context.portfolio.total_value * 1.05
        g.max_total_value_date = today

        is_stop_lose = True
        g.prev_stop_lose_date = context.current_dt.date()

    sell_count = 0

    buy_total = sum(g.buy_orders[s] for s in holding_stocks if s in g.buy_orders)
    current_total = sum(prices['close'][s][-1] for s in holding_stocks)

    #total_lose_pct = (current_total / buy_total) - 1 if buy_total > 0 else 0
    total_lose_pct = 0
    holding_stocks_buy = [s for s in holding_stocks if s in g.buy_orders]
    if len(holding_stocks_buy):
        total_lose_pct = sum(prices['close'][s][-1] / g.buy_orders[s] - 1 for s in holding_stocks_buy) / len(holding_stocks_buy)

    print('total lost pct {}'.format(total_lose_pct * 100))

    stop_win_all = False
    if total_lose_pct > 0.06 and today.day >= 21 and len(holding_stocks) > 5:
        index_code = '000932.XSHG' if g.use_hl_index else '000905.XSHG'

        index_prices = get_price(
            '399001.XSHE',
            count = 240,
            end_date = context.previous_date,
            frequency = 'daily',
            fields = 'close')['close']

        index_ma = pd.rolling_mean(index_prices, 39)

        if sum(index_prices[-21:] > index_ma[-21:]) < 17 and max(index_prices[-42:-21]) / min(index_prices[-42:-21]) < 1.04:
            stop_win_all = True
            print('stop win all1')
            for stock in (s for s in holding_stocks if s in g.buy_orders):
                g.sell_stock.append(stock)

            return False

    if (context.portfolio.total_value - g.cash_last_buy) > g.prev_buy_total_value * 1.07 and g.exact_last_buy_day and g.use_hl_index:
        index_code = '000932.XSHG' if g.use_hl_index else '000905.XSHG'

        index_prices = get_price(
            index_code,
            start_date = t.shift_trading_day(g.exact_last_buy_day, -1),
            end_date = context.previous_date,
            frequency = 'daily',
            fields = 'close')['close']

        if ((context.portfolio.total_value - g.cash_last_buy) / g.prev_buy_total_value - index_prices[-1] / index_prices[0]) > 0.04:
            stop_win_all = True
            print('stop win all2')
            for stock in (s for s in holding_stocks if s in g.buy_orders):
                g.sell_stock.append(stock)

            return False
        '''
        if (context.portfolio.total_value - g.cash_last_buy) > prev_position_value * 1.03:
            index_prices = get_price(
                index_code,
                count = 60,
                end_date = context.previous_date,
                frequency = 'daily',
                fields = 'close')['close']

            index_ma = pd.rolling_mean(index_prices, 20)
            if index_prices[-1] / index_ma[-1] > 1.1 and (context.portfolio.total_value - g.cash_last_buy) > g.prev_buy_total_value * 1.1:
                stop_win_all = True
                print('stop win all3')
                for stock in (s for s in holding_stocks if s in g.buy_orders):
                    g.sell_stock.append(stock)

                return False
        '''

    stocks_mtr, stocks_atr = ta.ATR(holding_stocks,context.previous_date, timeperiod=10)

    _is_forbidden_month = is_month_forbidden_month(context.previous_date)
    for i, stock in enumerate((s for s in holding_stocks if s in g.buy_orders)):
        prices_close = prices['close'][stock]
        prices_high = prices['high'][stock]
        prices_low = prices['low'][stock]
        prices_returns = prices['close'][stock].pct_change()
        turnover_ratio = df['turnover_ratio'][stock]

        stock_stop_lose = False
        current_price = prices_close.iloc[-1]
        buy_price = g.buy_orders[stock]
        max_price = g.stock_max_price.get(stock, 0)
        lose_pct = (current_price / buy_price) - 1
        if current_price > max_price:
            g.stock_max_price[stock] = current_price

        highest_close = max(prices_close)
        atr = stocks_atr[stock]
        max_price = max(max_price, highest_close)

        if context.run_params.type == "live_trade":
            print('stock {} current price: {}, buy price: {}, win pct: {}, var: {}'.format(stock, current_price, buy_price, lose_pct * 100, (max_price - current_price) / atr))

        if turnover_ratio > 20 and last_return[stock] > 0.095 and today.day >= g.stop_win_day:
            print('{} win stop'.format(stock))
            g.sell_stock.append(stock)
        elif (g.atr_stop_win and today.day >= g.stop_win_day and current_price > buy_price * 1.05) or \
            _is_forbidden_month:
            stop_win_atr_factor = 1.5 if _is_forbidden_month else 2

            if current_price < max_price - atr * stop_win_atr_factor:
                print('{} atr stop'.format(stock))
                g.sell_stock.append(stock)
        elif current_price < buy_price * g.stock_stop_lose_percentage:
            print('{} stop loss2'.format(stock))
            g.sell_stock.append(stock)
            stock_stop_lose = True
            sell_count = sell_count + 1

    if sell_count > 0 and sell_count == len(holding_stocks):
        g.max_total_value = context.portfolio.total_value * 1.05
        g.max_total_value_date = today
        is_stop_lose = True
        g.prev_stop_lose_date = context.current_dt.date()

    return is_stop_lose

def before_market_open(context):
    pass

def market_open(context):
    if g.trade_day == 'all':
        return

    #if '600310.XSHG' in context.portfolio.positions.keys():
    #    g.sell_stock.append('600310.XSHG')

    #g.sell_stock = ['002039.XSHE', '601369.XSHG', '601163.XSHG', '600874.XSHG', '600713.XSHG', '600308.XSHG', '600503.XSHG']
    #g.buy_stock = ['601666.XSHG']

    #g.buy_stock = ['000333.XSHE', '600690.XSHG', '600073.XSHG', '002385.XSHE', '002008.XSHE', '600438.XSHG']

    if context.run_params.type != "simple_backtest" and context.run_params.type != "full_backtest":
        if t.buy_stock is not None:
            g.buy_stock = t.buy_stock

        if t.sell_stock is not None:
            g.sell_stock = t.sell_stock

        if t.use_hl_index is not None:
            g.use_hl_index = t.use_hl_index

        if g.buy_stock:
            time.sleep(random.randrange(30))

    sell_stocks = list(g.sell_stock)

    if g.shuffle_list:
        random.shuffle (sell_stocks)

    for stock in sell_stocks:
        order_target_value(stock, 0)

    if g.treat_stop_lose:
        return

    if g.buy_stock:
        g.prev_buy_total_value = context.portfolio.total_value
        every_stock_amount = context.portfolio.total_value / (len(g.buy_stock) + len(context.portfolio.positions))

        buy_stocks = list(g.buy_stock)

        if g.use_hl_index:
            min_trade_amount = g.min_hl_trade_amount if every_stock_amount > g.min_hl_trade_amount else int(every_stock_amount)
        else:
            min_trade_amount = g.min_trade_amount if every_stock_amount > g.min_trade_amount else int(every_stock_amount)

        buy_turns = 2 if min_trade_amount == 0 else int(every_stock_amount / min_trade_amount) + 1
        current_buy_stock = None
        for i in range(1, buy_turns):
            if g.shuffle_list:
                random.shuffle(buy_stocks)

            for stock in buy_stocks:
                if stock is None or stock == "":
                    continue

                current_buy_stock = stock
                order_target_value(stock, min_trade_amount * i if i < buy_turns -1 else every_stock_amount)

        current_buy_stock_value = 0
        if current_buy_stock in context.portfolio.positions.keys():
            current_buy_stock_value = context.portfolio.positions[current_buy_stock].value

        if context.portfolio.available_cash > min_trade_amount:
            print('additional buy')
            order_value(current_buy_stock, context.portfolio.available_cash * 0.9)

def after_market_close(context):
    orders = get_orders()

    trades = get_trades()
    buy_order = None
    buy_day_append = False
    has_buy = False
    for trade in trades.values():
        buy_order = [order for order in orders.values()
            if trade.order_id == order.order_id and order.is_buy]

        if len(buy_order) > 0:
            g.buy_orders[buy_order[0].security] = buy_order[0].price
            if not g.buy_in_fall and not g.trading_spring_festival:
                g.last_buy_day = context.current_dt.date()

        if not has_buy and len(buy_order) > 0:
            has_buy = True

    sold_stocks = [s for s in g.buy_orders if s not in context.portfolio.positions]
    for s in sold_stocks:
        del g.buy_orders[s]

    if has_buy:
        g.exact_last_buy_day = context.current_dt.date()
        g.cash_last_buy = context.portfolio.cash
        print("Today's buy:")
        print(g.buy_orders)

    for s in context.portfolio.positions:
        if s not in g.buy_orders:
            g.buy_orders[s] = context.portfolio.positions[s].avg_cost
            print("add unscheduled buy :" + s + " price " + str(g.buy_orders[s]))

def get_factors(stocks_list, context, factors):
    if g.trading_postponed:
        return (None, None)

    need_price_data = any([config.get('data_type') == 'price' for _, (_, config, _, _) in g.factors.items()])
    prices = None

    if need_price_data:
        max_prices_len = max(config['prices_len'] for _, (_, config, _, _) in g.factors.items() if 'prices_len' in config)

        prices = get_price(stocks_list,
           count = max_prices_len,
           end_date = context.previous_date,
           frequency = 'daily',
           fields = 'close')['close']

    need_volume_data = any([config.get('data_type') == 'volume' for _, (_, config, _, _) in g.factors.items()])

    if need_volume_data:
        max_volumes_len = max(config['volumes_len'] for _, (_, config, _, _) in g.factors.items() if 'volumes_len' in config)

        volumes = get_price(stocks_list,
           count = max_volumes_len,
           end_date = context.previous_date,
           frequency = 'daily',
           fields = 'volume')['volume']

    # 从可行股票池中生成股票代码列表
    #df_all_raw = pd.DataFrame({'code': stocks_list}, index = stocks_list)
    df_all_raw = pd.DataFrame()

    factors = []

    # 每一个指标量都合并到一个dataframe里
    for factor_name, (factor_class, config, init_paras, paras) in g.factors.items():
        if config.get('data_type') == 'price':
            factor = factor_class(stocks_list, prices, **init_paras)
        elif config.get('data_type') == 'volume':
            factor = factor_class(stocks_list, volumes, **init_paras)
        else:
            factor = factor_class(stocks_list, **init_paras)

        factors.append((factor_name, factor, paras))

    fundamentals = [factor.fundamentals for (_, factor, _) in factors if hasattr(factor, 'fundamentals')]
    fundamentals = set(fundamental for factor_fundamentals in fundamentals for fundamental in factor_fundamentals)

    if len(fundamentals) > 0:
        df_fundamentals = get_fundamentals(query(*fundamentals).filter(indicator.code.in_(stocks_list)), context.previous_date)

    for (factor_name, factor, paras) in factors:
        if hasattr(factor, 'fundamentals'):
            paras['fundamentals'] = df_fundamentals

        df_factor = factor.generate(**paras)
        df_all_raw = pd.concat([df_all_raw, df_factor], axis=1)

    return df_all_raw
