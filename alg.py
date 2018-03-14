import operator
import sys
import datetime as dt
import numpy as np
import pandas as pd
import time
import talib
import jqdata
import prettytable as pt
import mytrade as t
import jqlib.technical_analysis as ta
from scipy import stats

'''
================================================================================
总体回测前
================================================================================
'''
def stat(context):
#def before_trading_start(context):
    g.feasible_stocks = []  # 当前可交易股票池
    g.holding_list_backup = []
    g.num_stocks = 0        # 设置持仓股票数目
    g.buy_stock = []
    g.sell_stock = []
    g.change_use_hl_index = False
    g.fundamental_selector_config = {'mc': (0, 0.8), 'pb': (0, 0.4), 'iop': (0.6, 1), 'roic': (0.6, 1)}

    schduler = t.EverydayTradeScheduler(g, context, lambda: trade(context), 1)
    schduler.trade()

    if g.if_trade:
        if bool(g.factors) == True:
            rebalance(context, *get_factors(g.feasible_stocks, context, g.factors))
        else:
            rebalance(context, g.feasible_stocks)

    g.if_trade = False

#总体回测前要做的事情
def initialize(context):
    set_params(context)    #1 设置策参数
    t.set_backtest(g)
    set_benchmark('000905.XSHG')
    run_daily(stat, time='morning')

#1 设置策略参数
def set_params(context):
    #g.fundamental_selector_config = {'mc': (0, 0.8), 'pb': (0, 0.4), 'iop': (0.6, 1), 'roic': (0.6, 1)}  # for parameters optim
    g.trade_day = 1
    g.buy_orders = {}
    g.stock_max_price = {}
    g.factor = 'VAR'          # 前回测的单因子
    g.shift = 21           # 设置一个观测天数（天数）
    g.precent = 1       # 持仓占可选股票池比例
    g.min_stocks_to_buy = 5
    g.max_stocks_to_buy = 10
    g.indices = ['000001.XSHG']  # 定义股票池
    g.max_positions_value = 0
    g.max_total_value = 0
    g.max_total_value_date = None
    g.prev_total_value = 0
    g.holding_day_count = 0
    g.total_value = 0
    g.xp_bear_market_slop = -12
    g.bear_market_slop = -10
    g.hl_bear_market_slop = 0
    g.index_slop = 0
    g.consecutive_bear_month = 0
    g.bear_stock_slop = -15
    g.prev_stop_lose_date = None
    g.stop_lose_total_threshold = 0.90
    g.all_stocks = None
    g.exclude_industries = ['HY480', 'HY481']
    g.mandatory_month = [2]
    g.forbidden_month = [6]
    g.dangerous_month = [1, 6, 12]
    g.stop_win_day = 23
    g.atr_stop_win = True
    g.last_buy_day = None
    g.days_since_last_buy = None
    g.index_fall_a_lot = False
    g.trading_days_of_last_month = None
    g.is_bull_market = False
    g.is_bear_market = False
    g.stock_stop_lose_percentage = 0.85
    g.buy_in_fall = False
    g.use_hl_index = False
    g.print_candidates = True

def set_factors(context, is_hl_win):
     # 多因子合并称DataFrame，单因子测试时可以把无用部分删除提升回测速度
    # 定义因子以及排序方式，默认False方式为降序排列，原值越大sort_rank排序越小
    if is_hl_win:
        g.factors = {
            'BP': (t.BpStockFactor, {}, {}, {'asc': False}),
        }
    elif g.days_since_last_buy > 30 and g.index_fall_a_lot:
        g.factors = {
            'MTM'+str(g.days_since_last_buy): (t.MtmStockFactor, {'data_type': 'price', 'prices_len': g.days_since_last_buy}, {}, {'days': g.days_since_last_buy, 'asc': True}),
        }
    else:
        g.factors = {
            'VAR': (t.VarStockFactor, {'data_type': 'price', 'prices_len': g.shift + 1}, {}, {'days': g.shift, 'asc': True})
        }

    '''
    g.factors = {
        #122'VAR': (t.VarStockFactor, {'data_type': 'price', 'prices_len': g.shift + 1}, {}, {'days': g.shift, 'asc': True}),
        'VVAR': (t.VVarStockFactor, {'data_type': 'volume', 'volumes_len': g.shift + 1}, {}, {'days': g.shift, 'asc': True}),
        #'VARC': (t.VarChangeStockFactor, {'data_type': 'price', 'prices_len': 2 * g.shift + 1}, {}, {'days': g.shift, 'asc': False}),
        #105'FLUC': (t.FlucStockFactor, {'data_type': 'price', 'prices_len': g.shift }, {}, {'days': g.shift, 'asc': True}),
        #'MTM21': (t.MtmStockFactor, {'data_type': 'price', 'prices_len': 21}, {}, {'days': 21, 'asc': False}),
        #'TR': (t.TrStockFactor, {'data_type': 'volume', 'volumes_len': g.shift}, {}, {'asc': True}),
        #'TRC': (t.TrChangeStockFactor, {'data_type': 'volume', 'volumes_len': g.shift}, {}, {'days': 21, 'end_date': context.previous_date, 'asc': True}),
        #'ROE': (t.RoeStockFactor, {}, {}, {'asc': False}),
        #331.34
        #'ROEC': (t.RoeChangeStockFactor, {}, {}, {'days': 95, 'end_date': context.previous_date, 'asc': True}),
        #'ROA': (t.RoaStockFactor, {}, {}, {'asc': False}),
        #199'ROAC': (t.RoaChangeStockFactor, {}, {}, {'days': 95, 'end_date': context.previous_date, 'asc': True}),
        #244'OPTP': (t.OptpStockFactor, {}, {}, {'asc': False}),
        #142'NPOR': (t.NporStockFactor, {}, {}, {'asc': False}),
        #170'NPORC': (t.NporChangeStockFactor, {}, {}, {'days': 95, 'end_date': context.previous_date, 'asc': True}),
        #223'BP': (t.BpStockFactor, {}, {}, {'asc': False}),
        #268'EP': (t.EpStockFactor, {}, {}, {'asc': True}),
        #103'PEG': (t.PegStockFactor, {}, {}, {'asc': True}),
        #244'DP': (t.DpStockFactor, {}, {}, {'asc': False}),
        #292'CFP': (t.CfpStockFactor, {}, {}, {'asc': False}),
        #255'PS': (t.PsStockFactor, {}, {}, {'asc': True}),
        #197'ALR': (t.AlrStockFactor, {}, {}, {'asc': True}),
        #233'CMC': (t.CmcStockFactor, {}, {}, {'asc': True}),
        #183'FACR': (t.FacrStockFactor, {}, {}, {'asc': True}),
    }
    '''

    if len(g.factors.keys()) == 1:
        g.factor = g.factors.keys()[0]

def set_feasible_stocks(context):
    current_month = context.current_dt.month
    g.use_hl_index = False

    if False and current_month in g.forbidden_month:
        g.feasible_stocks = []
    else:
        index_prices = get_price(
            [
                '399001.XSHE',   # 深证成指
                '399006.XSHE',   # 创业板指
                '399550.XSHE',   # 央视50
                '000905.XSHG',   # 中证500
                '399316.XSHE',   # 巨潮小盘
            ],
           count = 240,
           end_date = context.previous_date,
           frequency = 'daily',
           fields = 'close')['close']

        is_gem_win = (index_prices.ix[-21, 0] / index_prices.ix[-21, 1]) > (index_prices.ix[-1, 0] / index_prices.ix[-1, 1])
        is_hl_win = (index_prices.ix[-21, 0] / index_prices.ix[-21, 2]) > (index_prices.ix[-1, 0] / index_prices.ix[-1, 2])
        is_xp_win = (index_prices.ix[-21, 0] / index_prices.ix[-21, 3]) > (index_prices.ix[-1, 0] / index_prices.ix[-1, 3])
        is_xxp_win = (index_prices.ix[-21, 3] / index_prices.ix[-21, 4]) > (index_prices.ix[-1, 3] / index_prices.ix[-1, 4])

        is_hl_win = False
        index_fall_a_lot_days = g.days_since_last_buy if g.days_since_last_buy > 30 else 21

        if index_prices.ix[-index_fall_a_lot_days, 0] > index_prices.ix[-1, 0] * 1.2:
            g.index_fall_a_lot = True
        else:
            g.index_fall_a_lot = False

        g.all_stocks = get_all_securities(types=['stock', 'fund'], date=context.previous_date)[['display_name']]

        if not is_gem_win or True:
            all_stocks = [s for s in g.all_stocks.index if not str(s).startswith('300')]
        else:
            all_stocks = [s for s in g.all_stocks.index]

        hl_index_price = index_prices.ix[:, 2]
        index_price = index_prices.ix[:, 3]
        #g.is_bear_market = min(index_price[-21:]) < min(index_price[:-21]) * 0.97
        #g.is_bull_market = min(index_price[-21:]) < min(index_price[:-21]) * 1.03

        index_ratio = index_prices.ix[-21:, 3] / index_prices.ix[-21:, 2]
        (index_ratio_slop, _, _, _, _) = t.get_linear(index_ratio)
        is_mandatory_month = current_month in g.mandatory_month
        (g.index_slop, _, _, _, _) = t.get_linear(index_price[-g.trading_days_of_last_month:])
        (sma_slop, _, _, _, _) = t.get_linear(talib.EMA(np.array(index_price[-100:]), timeperiod=20)[-19:])
        (hl_index_slop, _, _, _, _) = t.get_linear(hl_index_price[-g.trading_days_of_last_month:])
        g.is_bear_market = (g.index_slop < g.bear_market_slop or \
            (hl_index_slop > g.index_slop + 5 and g.index_slop < 0)) and \
            not is_mandatory_month and g.trade_day != 'all'


        #if not g.is_bear_market and g.holding_day_count > 25 and days_since_max_total > 25 and hl_index_slop >= g.hl_bear_market_slop:
            #g.is_bear_market = True

        if g.is_bear_market:
            g.index_slop =  hl_index_slop
            g.is_bear_market = g.index_slop < g.hl_bear_market_slop

            if not g.is_bear_market:
                g.use_hl_index = True
            else:
                g.consecutive_bear_month = g.consecutive_bear_month + 1
        elif (g.consecutive_bear_month >= 3
            and index_price[-1] < index_price[-39:].mean()
            and g.trade_day != 'all'):
            g.consecutive_bear_month = g.consecutive_bear_month + 1
            g.is_bear_market = True
            print('still bear market')
        else:
            g.consecutive_bear_month = 0

        use_xp = False
        if g.days_since_last_buy > 30 and g.index_fall_a_lot:
            use_xp = True
            #g.fundamental_selector_config['mc'] = (0, 0.25)
            #g.fundamental_selector_config['iop'] = (0, 1)
            #g.fundamental_selector_config['roic'] = (0, 1)


        if not g.use_hl_index:
            selector = t.NotIndustrySecuritySelector(all_stocks, context.previous_date, g.exclude_industries)
            selector = t.NotNewSecuritySelector(selector.get_stocks(), context.previous_date)
            selector = t.NotSTSecuritySelector(selector.get_stocks(), context.previous_date)
            selector = t.NotBlackListSecuritySelector(selector.get_stocks())
            not_black_list_securities = selector.get_stocks()

            if not use_xp:
                selector= t.FundamentalSecuritySelector1(not_black_list_securities, context.previous_date,
                                        mc = g.fundamental_selector_config['mc'],
                                        pb = g.fundamental_selector_config['pb'],
                                        iop = g.fundamental_selector_config['iop'],
                                        roic = g.fundamental_selector_config['roic'])
            else:
                selector= t.FundamentalSecuritySelector(not_black_list_securities, context.previous_date,
                                    mc = (0, 0.25),
                                    pe = (0, 0.9),
                                    pb = (0, 0.4),
                                    ps = (0, 0.4),
                                    iop = 0,
                                    facr = (0, 1))

            fundamental_stocks = selector.get_stocks()

            g.feasible_stocks = t.set_feasible_stocks(fundamental_stocks, g.shift, context.previous_date)
        else:
            set_hl_feasible_stocks(context)

    set_factors(context, False)
    #set_factors(context, g.use_hl_index)

    # 设置手续费与手续费
    t.set_slip_fee(context.current_dt)

    # 购买股票为可行股票池对应比例股票

    g.num_stocks = int(len(g.feasible_stocks)*g.precent)

def set_hl_feasible_stocks(context):
    selector = t.StockIndicesSecuritySelector(['399550.XSHE', '000932.XSHG'], context.previous_date)
    '''
    selector = t.FundamentalSecuritySelector(selector.get_stocks(), context.previous_date,
                            mc = (0, 1),
                            pe = (0, 0.5),
                            pb = (0, 0.5),
                            ps = (0, 1),
                            iop = 5,
                            facr = (0, 1))
    '''
    selector = t.PegSecuritySelector(selector.get_stocks(), context.previous_date, 0.5)
    stocks = selector.get_stocks()
    g.feasible_stocks = t.set_feasible_stocks(stocks, g.shift, context.previous_date)

def trade(context):
    # 设置手续费与手续费
    t.set_slip_fee(context.current_dt)
    # 购买股票为可行股票池对应比例股票

    #g.num_stocks = int(len(g.feasible_stocks)*g.precent)

    g.if_trade = False
    g.buy_in_fall = False
    if g.last_buy_day is not None:
        g.days_since_last_buy =  t.get_trading_day_num_from(g.last_buy_day, context.previous_date)

    is_stop_lose = stop_win_lose(context)
    current_year = context.current_dt.year
    current_month = context.current_dt.month
    current_day = context.current_dt.day
    last_month = 12 if current_month == 1 else current_month - 1
    first_day_of_last_month = dt.date(current_year - 1 if current_month == 1 else current_year,
                                                   12 if current_month == 1 else current_month - 1, 1)
    g.trading_days_of_last_month = t.get_trading_day_num_from(first_day_of_last_month, context.previous_date)
    if g.trading_days_of_last_month > 25:
        g.trading_days_of_last_month = g.shift

    if not is_stop_lose \
        or current_month in g.mandatory_month \
        or last_month in g.mandatory_month:

        if (g.days_since_last_buy is None or g.days_since_last_buy >= 10) and (current_month not in g.dangerous_month \
            or g.prev_stop_lose_date is None \
            or t.shift_trading_day(context.previous_date, -5) > g.prev_stop_lose_date):
            scheduler = t.MonthDayTradeScheduler(g, context, lambda: set_feasible_stocks(context), g.trade_day)
            if_trade = scheduler.trade()

'''
================================================================================
每天交易时
================================================================================
'''
def handle_data(context,data):
    operate(context)

#7 获得因子信息
# stocks_list调用g.feasible_stocks factors调用字典g.factors
# 输出所有对应数据和对应排名，DataFrame
def get_factors(stocks_list, context, factors):
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


    return df_all_raw, prices

# 9交易调仓
# 依本策略的买入信号，得到应该买的股票列表
# 借用买入信号结果，不需额外输入
# 输入：context（见API）
def rebalance(context, df_all, stock_prices = None):
    is_bear_market = g.is_bear_market
    is_mandatory_month = context.current_dt.month in g.mandatory_month

    if type(df_all) is not list:
        score = g.factor + '_' + 'sorted_rank'
        holding_list = list(df_all.sort(score, ascending = True).index)
    else:
        holding_list = df_all

    prices_data = get_price(holding_list,
               count = 100,
               end_date = context.previous_date,
               frequency = 'daily',
               fields = ['close', 'volume', 'money'])

    original_holding_list = holding_list[:]

    stock_prices = prices_data['close'][-50:]
    stock_volumes = prices_data['volume'][-50:]
    stock_money = prices_data['money'][-50:]

    linears = {s: t.get_linear(talib.EMA(np.array(stock_prices[s]), timeperiod=20)[-19:]) for s in holding_list}

    #linears = {s: t.get_linear(stock_prices[s][-g.trading_days_of_last_month:]) for s in holding_list}
    rsis = {s: talib.RSI(np.array(stock_prices[s]), timeperiod=5)[-1] for s in holding_list}

    min_slop = min(g.index_slop * 1.2 if g.index_slop < 0 else g.index_slop, g.bear_stock_slop)
    if not g.buy_in_fall:
        holding_list_linears = [s for s in holding_list if ((g.days_since_last_buy > 30 and g.index_fall_a_lot)
            or linears[s][0] > min_slop)
            and min(stock_prices[s][-5:]) > min(stock_prices[s][-g.trading_days_of_last_month:])]
    else:
        holding_list_linears = [s for s in holding_list if ((g.days_since_last_buy > 30 and g.index_fall_a_lot)
        or g.use_hl_index or linears[s][0] > min_slop)]

    if not is_mandatory_month or len(holding_list_linears) > g.min_stocks_to_buy:
        holding_list = holding_list_linears
    else:
        holding_list = holding_list_linears + list(set(holding_list) - set(holding_list_linears))


    if not g.use_hl_index and g.index_slop < 12:
        stock_prices_returns = prices_data['close'].pct_change()
        stocks_returns_var = stock_prices_returns.var()
        #print(stocks_returns_var)
        holding_list = [s for s in holding_list if  stocks_returns_var.ix[s] > 0.0002]

    if not g.use_hl_index and len(holding_list) > 30 and g.index_slop < 0:
        stock_money_avg = stock_money[-20:].mean()
        stock_money_avg.sort()
        least_money_stocks = stock_money_avg[:int(len(holding_list) * 0.1)].index
        holding_list = [s for s in holding_list if s not in least_money_stocks]

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

    is_bear_market = is_bear_market and not g.buy_in_fall

    if is_bear_market:
        holding_list = []

    # 每只股票购买金额

    #industrySecuritySelector = t.IndustrySecuritySelector(holding_list, context.previous_date, t.cyclical_industries)

    if not g.use_hl_index and len(holding_list) < g.min_stocks_to_buy * 3:
        g.use_hl_index = True
        g.holing_list_backup = holding_list
        g.change_use_hl_index = True
        set_hl_feasible_stocks(context)
        rebalance(context, *get_factors(g.feasible_stocks, context, g.factors))
        return
    elif g.use_hl_index and g.change_use_hl_index and len(holding_list) < g.min_stocks_to_buy:
        holding_list = g.holing_list_backup
        g.use_hl_index = False
        g.change_use_hl_index = False

    num_stocks = min(len(holding_list), g.num_stocks)
    if g.max_stocks_to_buy > 0 and num_stocks > g.max_stocks_to_buy:
        num_stocks = g.max_stocks_to_buy

    if num_stocks < g.min_stocks_to_buy:
         holding_list = []

    g.every_stock_amount = context.portfolio.total_value / num_stocks if num_stocks > 0 else 0
    operate_stock_list =  holding_list[:num_stocks]

    # 空仓只有买入操作
    if len(list(context.portfolio.positions.keys()))==0:
        if len(holding_list) >= g.min_stocks_to_buy and not is_bear_market:
            for stock in operate_stock_list:
                #g.buy_stock.append((stock, operate_cyclical_stock_amount if stock in operate_cyclical_stock_list else non_operate_cyclical_stock_amount))
                g.buy_stock.append(stock)
    else:
        for stock in context.portfolio.positions.keys():
            if stock not in operate_stock_list:
                g.sell_stock.append(stock)

        if len(holding_list) >= g.min_stocks_to_buy and not is_bear_market:
            for stock in operate_stock_list:
                #g.buy_stock.append((stock, operate_cyclical_stock_amount if stock in operate_cyclical_stock_list else non_operate_cyclical_stock_amount))
                g.buy_stock.append(stock)

    sell_stocks = [(s, g.all_stocks.iloc[all_stocks_index.index(s)]['display_name']) for s in g.sell_stock]
    buy_stocks = [(s, g.all_stocks.iloc[all_stocks_index.index(s)]['display_name']) for s in g.buy_stock]

    msg = 'slop:{}|sell:{}|buy:{}'.format(g.index_slop,repr(sell_stocks).decode('unicode-escape'), repr(buy_stocks).decode('unicode-escape'))
    print(msg)
    send_message(msg)

def operate(context):
    if g.trade_day == 'all':
        return

    today = context.current_dt

    for stock in g.sell_stock:
        order_target_value(stock, 0)
    #for stock, amount in g.buy_stock:
    #    order_target_value(stock, amount)
    for stock in g.buy_stock:
        order_target_value(stock, g.every_stock_amount)

    if g.max_positions_value == 0:
        g.max_positions_value = context.portfolio.positions_value

def need_by_price_slop(context, stock):
    df_price_info = get_price(stock,
        count = 20,
        end_date=context.previous_date,
        frequency='daily',
        fields='close')['close']

    linear = t.get_linear(df_price_info)

    return linear[0] > g.bear_stock_slop

def stop_win_lose(context):
    is_stop_lose = False
    today = context.current_dt
    current_month = today.month
    current_day = today.day
    holding_stocks = list(context.portfolio.positions.keys())

    if context.portfolio.total_value == g.prev_total_value:
        g.holding_day_count = 0
    else:
        g.holding_day_count += 1

    g.prev_total_value = context.portfolio.total_value
    if(len(holding_stocks) == 0):
        return is_stop_lose

    prices = get_price(holding_stocks,
               count = 30,
               end_date = context.previous_date,
               frequency = 'daily',
               fields = ['high', 'low', 'close'])
    last_return =  prices['close'].pct_change().iloc[-1]
    last_return.sort()
    most_down = last_return[:int(len(holding_stocks) * 0.8)]

    all_down = current_month in g.dangerous_month \
        and current_day > 15 \
        and len(holding_stocks) > 5 \
        and mean(most_down) < -0.03 \
        and not g.use_hl_index

    days_since_max_value =  t.get_trading_day_num_from(g.max_total_value_date, context.previous_date) if g.max_total_value_date else 0
    days_since_stop_lose =  t.get_trading_day_num_from(g.prev_stop_lose_date, context.previous_date) if g.prev_stop_lose_date else 0

    if (not all_down
        and context.portfolio.total_value < g.max_total_value * 0.95
        and len(holding_stocks) > 2
        and (days_since_stop_lose > 21 or not g.prev_stop_lose_date)
        and not g.use_hl_index):
        all_securities = get_all_securities(types=['stock'])
        all_securities = t.set_feasible_stocks(all_securities.index, g.shift, context.current_dt)
        total_count = len(all_securities)
        closes = get_price(all_securities, count = 21, end_date = today, fields=['close'])['close']

        down = closes.apply(lambda x: x[-1] < x[0] * 0.9 and x[-1] < x[-5]).dropna(axis=0, how='all')
        down_pct = down.sum() * 100 / total_count
        if down_pct > 30:
            all_down = True

    if context.portfolio.total_value > g.max_total_value:
        g.max_total_value = context.portfolio.total_value
        g.max_total_value_date = today

    if g.max_positions_value == 0 and not all_down:
        g.max_positions_value = context.portfolio.positions_value
    elif context.portfolio.total_value < g.max_total_value * g.stop_lose_total_threshold \
        or all_down:
        #or context.portfolio.positions_value < g.max_positions_value * g.stop_lose_total_threshold \
        for stock in holding_stocks:
            order_target_value(stock, 0)
            holding_stocks = []
            g.stock_max_price = {}

        g.max_total_value = context.portfolio.total_value
        g.max_total_value_date = today
        g.max_positions_value = context.portfolio.positions_value
        is_stop_lose = True
        g.prev_stop_lose_date = context.current_dt.date()
    elif context.portfolio.positions_value > g.max_positions_value:
        g.max_positions_value = context.portfolio.positions_value

    sell_count = 0
    buy_total = sum(g.buy_orders[s] for s in holding_stocks if s in g.buy_orders)
    current_total = sum(prices['close'][s][-1] for s in holding_stocks)

    total_lose_pct = (current_total / buy_total) - 1 if buy_total > 0 else 0

    _, stocks_atr = ta.ATR(holding_stocks,context.previous_date, timeperiod=10)

    for i, stock in enumerate((s for s in holding_stocks if s in g.buy_orders)):
        prices_close = prices['close'][stock]
        prices_high = prices['high'][stock]
        prices_low = prices['low'][stock]
        prices_returns = prices['close'][stock].pct_change()

        stock_stop_lose = False
        current_price = prices_close.iloc[-1]
        price_pct_change = prices_close.pct_change() * 100
        buy_price = g.buy_orders[stock]
        max_price = g.stock_max_price.get(stock, 0)
        lose_pct = (current_price / buy_price) - 1
        if current_price > max_price:
            g.stock_max_price[stock] = current_price

        highest_close = max(prices_close)
        _is_forbidden_month = current_month in g.forbidden_month
        if (g.atr_stop_win and today.day >= g.stop_win_day and current_price > buy_price * 1.05) or \
            _is_forbidden_month:

            stop_win_atr_factor = 1.5 if _is_forbidden_month else 2
            atr = stocks_atr[stock]
            if current_price < max(max_price, highest_close) - atr * stop_win_atr_factor:
                if g.max_positions_value > 0:
                    g.max_positions_value = g.max_positions_value - context.portfolio.positions[stock].value
                print('{} atr stop'.format(stock))
                order_target_value(stock, 0)
        elif (current_price < buy_price * g.stock_stop_lose_percentage or
            (total_lose_pct < -0.02 and lose_pct < total_lose_pct * 10)):
            if g.max_positions_value > 0:
                g.max_positions_value = g.max_positions_value - context.portfolio.positions[stock].value
            order_target_value(stock, 0)
            stock_stop_lose = True
            sell_count = sell_count + 1

    if sell_count > 0 and sell_count == len(holding_stocks):
        g.max_total_value = context.portfolio.total_value
        g.max_total_value_date = today
        is_stop_lose = True
        g.prev_stop_lose_date = context.current_dt.date()

    return is_stop_lose

'''
================================================================================
每天收盘后
================================================================================
'''
def after_trading_end(context):
    orders = get_orders()
    #for order in orders.values():
    #    log.info(order)

    trades = get_trades()
    buy_order = None
    for trade in trades.values():
        buy_order = [order for order in orders.values()
            if trade.order_id == order.order_id and order.is_buy]

        if len(buy_order) > 0:
            g.buy_orders[buy_order[0].security] = buy_order[0].price
            g.last_buy_day = context.current_dt.date()

    sold_stocks = [s for s in g.buy_orders if s not in context.portfolio.positions]
    for s in sold_stocks:
        del g.buy_orders[s]
