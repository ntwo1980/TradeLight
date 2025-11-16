import talib

# 全局参数配置
g_params = {
    #'合约': 'ZCE|F|FG|509',
    '合约': 'DCE|Z|M|MAIN',
    '轴价': 3200,
    '每格跳数': 5,
    'K线数量': 2000,
    '保证金': 1999,
    '手续费': 10
}

# 全局变量
pivot_pre = -99999
n_long = 0
write = 0
n_day = 1
HH = -99999
LL = 99999


def log(str1):
    """记录日志到指定文件"""
    path = f"D:\\data\\jizhi\\{StrategyName()}.txt"  # 文件路径
    with open(path, 'a+', encoding='utf-8') as f:
        content = (
            f"\n{SymbolName()} 轴价{g_params['轴价']} "
            f"每格{g_params['每格跳数']}跳 "
            f"手续费{g_params['手续费']}  {str1}"
        )
        f.write(content)


def initialize(context):
    """初始化函数：设置K线周期"""
    SetBarInterval(g_params['合约'], 'M', 1, g_params['K线数量'])


def handle_data(context):
    """策略主逻辑：每次K线更新时执行"""
    global pivot0, pivot_pre, n_long, write, n_day, HH, LL

    # 数据不足，跳过
    if CurrentBar() < 9:
        return

    pivot0 = g_params['轴价']
    grid = g_params['每格跳数'] * PriceTick()
    taoli = 'SPD' not in g_params['合约']  # 判断是否为套利合约

    # 每日重置计数器
    if BarsSinceToday() == 0:
        n_day += 1

    # 根据是否为套利合约选择价格
    p1 = High()[-1] if taoli else Close()[-1]   # 当前K线高点或收盘价
    p2 = High()[-2] if taoli else Close()[-2]   # 上一根K线高点或收盘价
    p3 = Low()[-1]  if taoli else Close()[-1]   # 当前K线低点或收盘价
    p4 = Low()[-2]  if taoli else Close()[-2]   # 上一根K线低点或收盘价

    # 更新日内高低点
    HH = max(HH, p1)
    LL = min(LL, p3)
    HL = HH - LL
    max_lot = round((HH - LL) / grid)

    # 特定品种时间过滤（示例：AG夜盘）
    sym = Time() < 0.03 if SymbolType() == 'SHFE|F|AG' else True

    if sym:
        for i in range(199):
            pivot = pivot0 - i * grid

            # 多头平仓信号（上穿网格线）
            if p2 <= pivot and p1 > pivot and pivot != pivot_pre:
                LogInfo('平仓')
                Sell(1)
                pivot_pre = pivot
                n_long += 1
                # PlotText(pivot, f'{round(pivot)}平{n_long}')

            # 多头开仓信号（下穿网格线）
            if p3 >= pivot and p4 < pivot and pivot != pivot_pre:
                LogInfo('开仓')
                Buy(1)
                pivot_pre = pivot
                # PlotText(pivot, '多')

    # 策略结束时输出统计信息（BarStatus()==2 表示最后一根K线）
    if BarStatus() == 2 and write == 0:
        write = 1
        手续费 = g_params['手续费']
        p_day = round(n_long / n_day, 1)
        profit = p_day * (grid * ContractUnit() - 手续费)
        保证金 = round(g_params['保证金'] * max_lot / 10000, 1)
        年化 = int(profit * 240 / 保证金 / 100)

        log(
            f"交易{n_day}日总平多{n_long}次  "
            f"日均平多{p_day}次 盈利={profit}元  "
            f"年化={年化}%  高{HH}_{LL}低 差={HL}  "
            f"最大持仓{max_lot}手 保证金={保证金}万"
        )