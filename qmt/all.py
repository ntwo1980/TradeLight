#encoding:gbk

class a():
    pass

universe = a()
with open('Strategy.py', "r", encoding="utf-8") as f:
    exec(f.read(), globals())  # 注入全局

levelGridStrategySettings = [
    #{'stocks': ["513080.SH"], 'stockNames':['法国CAC40']},
    #{'stocks': ["159691.SZ"], 'stockNames':['港股红利']},518
    #{'stocks': ["159851.SZ"], 'stockNames':['金融科技']},
    {'stocks': ["513090.SH"], 'stockNames':['香港证券']},
    {'stocks': ["159552.SZ"], 'stockNames':['中证2000增强']},
    #{'stocks': ["515100.SH"], 'stockNames':['红利低波100']},
    #{'stocks': ["515400.SH"], 'stockNames':['大数据']},
    #{'stocks': ["159869.SZ"], 'stockNames':['游戏']},
    {'stocks': ["159687.SZ"], 'stockNames':['亚太精选']},
    #{'stocks': ["159605.SZ"], 'stockNames':['中概互联网格']},
    #{'stocks': ["515880.SH"], 'stockNames':['通信']},
    #{'stocks': ["159509.SZ"], 'stockNames':['纳指科技']},
    #{'stocks': ["159928.SZ"], 'stockNames':['消费']},
    #{'stocks': ["159530.SZ"], 'stockNames':['机器人']},
    {'stocks': ["513290.SH"], 'stockNames':['纳斯达克生物科技']},
    #{'stocks': ["512400.SH"], 'stockNames':['有色金属']},
    {'stocks': ["159766.SZ"], 'stockNames':['旅游']},
    #{'stocks': ["515220.SH"], 'stockNames':['煤炭']},
    #{'stocks': ["159967.SZ"], 'stockNames':['创业板成长']},
    #{'stocks': ["518880.SH"], 'stockNames':['黄金']},
    #{'stocks': ["159866.SZ"], 'stockNames':['日经']},
    #{'stocks': ["159825.SZ"], 'stockNames':['农业']},
    #{'stocks': ["561910.SH"], 'stockNames':['电池']},
]

simpleGridStrategies = [
    #{'stocks': ["159980.SZ"], 'stockNames':['有色'], 'priority': 9},
    {'stocks': ["159985.SZ"], 'stockNames':['豆粕'], 'priority': 10},
]

stockLevelGridStrategies = [
    #{'stocks': ["300059.SZ"], 'stockNames':['东方财富']},
    #{'stocks': ["601166.SH"], 'stockNames':['兴业银行']},
]

pairLevelGridStrategies = [
    {'stocks': ["515070.SH", "159819.SZ"], 'stockNames':['人工智能', '人工智能']},
    {'stocks': ["513350.SH", "159518.SZ"], 'stockNames':['标普油气', '标普油气'], 'priority': 10, 'threshold_ratio':0.02},
    {'stocks': ["512660.SH", "512710.SH"], 'stockNames':['军工', '军工']},
    {'stocks': ["516780.SH", "159713.SZ"], 'stockNames':['稀土', '稀土']},
    {'stocks': ["159570.SZ", "159567.SZ"], 'stockNames':['创新药', '创新药']},
    {'stocks': ["516160.SH", "159875.SZ"], 'stockNames':['新能源', '新能源']},
    #{'stocks': ["159562.SZ", "517520.SH"], 'stockNames':['黄金股', '黄金股']},
    {'stocks': ["512050.SH", "563220.SH"], 'stockNames':['A500', 'A500']},
    {'stocks': ["513920.SH", "520990.SH"], 'stockNames':['央企红利', '央企红利']},
    {'stocks': ["515050.SH", "515880.SH"], 'stockNames':['通信', '通信']},
    {'stocks': ["513520.SH", "159866.SZ"], 'stockNames':['日经', '日经']},
    {'stocks': ["159530.SZ", "159770.SZ"], 'stockNames':['机器人', '机器人']},
    {'stocks': ["159851.SZ", "516860.SH"], 'stockNames':['金融科技', '金融科技']},
    {'stocks': ["513050.SH", "159605.SZ"], 'stockNames':['中概互联', '中概互联']},
    {'stocks': ["512890.SH", "515100.SH"], 'stockNames':['红利低波100', '红利低波100']},
    {'stocks': ["588200.SH", "159995.SZ"], 'stockNames':['芯片', '芯片']},
    #{'stocks': ["516000.SH", "515400.SH"], 'stockNames':['大数据', '大数据']},
    {'stocks': ["588020.SH", "159967.SZ"], 'stockNames':['创业板成长', '创业板成长'], 'threshold_ratio':0.02},
    {'stocks': ["513290.SH", "159502.SZ"], 'stockNames':['生物科技', '生物科技'], 'threshold_ratio':0.02},
    {'stocks': ["588080.SH", "159915.SZ"], 'stockNames':['科创板', '科创板'], 'threshold_ratio':0.02},
    #{'stocks': ["159561.SZ", "513030.SH"], 'stockNames':['德国', '德国']},
]

strategies = []

for setting in levelGridStrategySettings:
    strategy = LevelGridStrategy(
    universe = universe,
    stocks=setting['stocks'],
    stockNames=setting['stockNames'],
    priority=setting.get('priority', 0),
    get_trade_detail_data_func = get_trade_detail_data,
    pass_order_func = passorder,
    cancel_func = cancel,
    timetag_to_datetime_func = timetag_to_datetime,
    download_history_data_func = download_history_data)

    strategies.append(strategy)

for setting in stockLevelGridStrategies:
    strategy = StockLevelGridStrategy(
    universe = universe,
    stocks=setting['stocks'],
    stockNames=setting['stockNames'],
    priority=setting.get('priority', 0),
    get_trade_detail_data_func = get_trade_detail_data,
    pass_order_func = passorder,
    cancel_func = cancel,
    timetag_to_datetime_func = timetag_to_datetime,
    download_history_data_func = download_history_data)

    strategies.append(strategy)

for setting in simpleGridStrategies:
    strategy = SimpleGridStrategy(
    universe = universe,
    stocks=setting['stocks'],
    stockNames=setting['stockNames'],
    priority=setting.get('priority', 0),
    get_trade_detail_data_func = get_trade_detail_data,
    pass_order_func = passorder,
    cancel_func = cancel,
    timetag_to_datetime_func = timetag_to_datetime,
    download_history_data_func = download_history_data)

    strategies.append(strategy)

for setting in pairLevelGridStrategies:
    strategy = PairLevelGridStrategy(
    universe = universe,
    stocks=setting['stocks'],
    stockNames=setting['stockNames'],
    priority=setting.get('priority', 0),
    get_trade_detail_data_func = get_trade_detail_data,
    pass_order_func = passorder,
    cancel_func = cancel,
    timetag_to_datetime_func = timetag_to_datetime,
    download_history_data_func = download_history_data)

    strategies.append(strategy)

def init(C):
    for s in strategies:
        if not C.do_back_test:
            s.SetAccount(account, accountType)

        s.init(C)

    if not s.IsBacktest:
        C.run_time("f","60nSecond","2019-10-14 09:30:00")
        C.run_time("g","1nDay","2019-10-14 14:59:30")

def handlebar(C):
    if not strategies[0].IsBacktest:
        return

    max_retries = 100  # 最大重试次数，可根据需要调整
    retry_count = 0

    while retry_count < max_retries:
        executed_flag = False
        # 每次都按当前 PriceRatio 重新排序
        for s in sorted(strategies, key=lambda x: (-x.Priority, -x.SellCount, x.PriceRatio)):
            s.f(C)
            if s.SellExecuted:
                executed_flag = True
                break  # 一旦有策略执行成功，立即跳出 for，重新开始 while
        if not executed_flag:
            break  # 本轮无任何策略执行，退出循环
        retry_count += 1

    if retry_count >= max_retries:
        print("警告：达到最大重试次数，可能存在死循环或策略持续触发 Executed。")

def f(C):
    max_retries = 100  # 最大重试次数，可根据需要调整
    retry_count = 0

    while retry_count < max_retries:
        executed_flag = False
        # 每次都按当前 PriceRatio 重新排序
        for s in sorted(strategies, key=lambda x: (-x.Priority, -x.SellCount, x.PriceRatio)):
            s.f(C)
            if s.SellExecuted:
                executed_flag = True
                break  # 一旦有策略执行成功，立即跳出 for，重新开始 while
        if not executed_flag:
            break  # 本轮无任何策略执行，退出循环
        retry_count += 1

    if retry_count >= max_retries:
        print("警告：达到最大重试次数，可能存在死循环或策略持续触发 Executed。")


def g(C):
    for s in strategies:
        s.g(C)






