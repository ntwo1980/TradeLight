import json
import math
import os
from datetime import datetime

import numpy as np
import pandas as pd
import requests
import talib


class BaseStrategy():
    def __init__(self, **kwargs):   # BaseStrategy
        self.context = None
        self.DailyPricesDate = None
        self.DailyPrices = {}
        self.ATRs = {}
        self.slopes = {}
        self.r_squareds = {}
        self.MinutePrices = {}
        self.LastPrices = {}
        self.base_price = 0
        self.buy_index = 0
        self.sell_index = 0
        self.last_buy_date = None
        self.last_sell_date = None
        self.send_order_count = 0
        self.max_send_order_count = 10
        self.deal = False
        self.is_state_loaded = False
        self.print_debug = True
        self.config_folder = f"D:\\data\\jizhi"
        self.dingding_token = None
        self.dingding_keyword = None
        self.waiting_list = []
        self.max_logical_holding = 0
        self.trade_quantity = 0
        self.order_deleted = False
        self.position_closed = False

    def initialize(self, context, **kwargs):   # BaseStrategy
        self.context = context
        self.params = kwargs['params']
        self.api = kwargs['api']
        self.IsBacktest = context.strategyStatus() != 'C'

        #self.api.SetTriggerType(1)   # 即时行情触发(测试时可放开屏蔽)
        #self.api.SetTriggerType(3, 1000) # 每隔1000毫秒触发一次
        self.api.SetTriggerType(5)
        self.api.SetTriggerType(6) #连接状态触发
        self.api.SetOrderWay(1)
        #self.api.SetUserNo('Q20702017')

        file = f"{self.config_folder}\\config.json"

        if not os.path.exists(file):
            self.print('Error: No config file')
        else:
            with open(file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.api.SetUserNo(config['account'])
                self.dingding_token = config['dingding_token']
                self.dingding_keyword = config['dingding_keyword']
                self.print(config['account'])

    def LastTradeDate(self):
        return str(self.api.TradeDate()) if self.IsBacktest else str(self.api.Q_LastDate())

    def today_str(self):
        return datetime.today().strftime('%Y%m%d')

    def _fetch_ohlcv(self, code, period):
        return pd.DataFrame({
            'Open':  self.api.Open(code, period, 1),
            'High':  self.api.High(code, period, 1),
            'Low':   self.api.Low(code, period, 1),
            'Close': self.api.Close(code, period, 1),
            'Vol':   self.api.Vol(code, period, 1),
        })

    def GetDailyPrices(self, codes):  # BaseStrategy
        if self.DailyPricesDate == self.LastTradeDate():
            return
        for code in codes:
            df = self._fetch_ohlcv(code, 'D')

            if len(df) >= 4:
                atr = talib.ATR(df['High'].values, df['Low'].values, df['Close'].values, timeperiod=10)[-1]

                atr_config = self.params.get('atr')
                fixed_atr = self.params.get('fixedAtr', False)
                if atr_config is not None:
                    if fixed_atr:
                        atr = atr_config
                    elif atr > atr_config * 1.3 or atr < atr_config * 0.7:
                        atr = atr_config

                self.ATRs[code] = atr
                x = np.arange(len(df['Close'].values[-20:]))
                vals = df['Close'].values[-20:]
                shift = vals.min() - 1e-6
                y = np.log(vals - shift)
                slope, intercept = np.polyfit(x, y, 1)
                self.slopes[code] = slope
                self.r_squareds[code] = 1 - (sum((y - (slope * x + intercept))**2) / ((len(y) - 1) * np.var(y, ddof=1)))
            else:
                self.ATRs[code] = None
                self.slopes[code] = None
                self.r_squareds[code] = None

            self.DailyPrices[code] = df.iloc[:-1] if self.IsBacktest else df
            self.DailyPricesDate = self.LastTradeDate()

    def GetMinutePrices(self, codes):  # BaseStrategy
        minute_prices = {}

        for code in codes:
            minute_prices[code] = self._fetch_ohlcv(code, 'M')

        return minute_prices

    def GetLastPrices(self, codes):  # BaseStrategy
        minute_prices = self.GetMinutePrices(codes)
        last_prices = {}

        for code in codes:
            if self.IsBacktest:
                last_prices[code] = minute_prices[code].iloc[-1]['Close']
            else:
                last_prices[code] = self.api.Q_Last(code)

        self.LastPrices = last_prices

    def handle_data(self, context):   # BaseStrategy
        self.context = context
        self.IsBacktest = context.strategyStatus() != 'C'

        now = self.api.CurrentTime()

        if context.triggerType() == 'N':
            if context.triggerData()['ServerType'] == 'T':# 交易
                if context.triggerData()['EventType'] == 1:# 交易连接
                    # 盘中重新启动实盘交易
                    self.api.StartTrade()
                    self.print('Error: StartTrade')
                else: # 交易断开
                    # 盘中暂时停止实盘交易
                    self.api.StopTrade()
                    self.print('Error: StopTrade')

                    return False

        if not self.IsBacktest and (0.0859 < now < 0.090010 or 0.2059 < now < 0.210010):
            if self.order_deleted:
                self.order_deleted = False
            if self.position_closed:
                self.position_closed = False

            self.max_send_order_count = 40
            return False

        if not self.IsBacktest and 0.2259 < now < 0.2310:
            if not self.order_deleted:
                self.order_deleted = True
                self.delete_orders()

            return False

        return True

    def GetBuyPosition(self, code):
        if self.IsBacktest:
            return self.api.BuyPosition(code)
        else:
            return self.api.A_BuyPositionCanCover(code)
            # return self.api.A_BuyPosition(code)

    def GetSellPosition(self, code):
        if self.IsBacktest:
            return self.api.SellPosition(code)
        else:
            return self.api.A_SellPositionCanCover(code)
            # return self.api.A_SellPosition(code)

    def _resolve_positions_for_order(self, code):
        if self.is_spread_code(code):
            if self.params.get('firstPosition', True):
                buy_position = self.GetBuyPosition(self.codes[2])
                sell_position = self.GetSellPosition(self.codes[2])
            else:
                buy_position = self.GetSellPosition(self.codes[3])
                sell_position = self.GetBuyPosition(self.codes[3])

            if buy_position == 0 and sell_position == 0 and self.logical_holding != 0:
                if self.logical_holding >= 0:
                    buy_position = self.logical_holding
                else:
                    sell_position = abs(self.logical_holding)
        else:
            buy_position = self.GetBuyPosition(code)
            sell_position = self.GetSellPosition(code)

            if buy_position == 0 and sell_position == 0 and self.logical_holding != 0:
                if self.logical_holding >= 0:
                    buy_position = self.logical_holding
                else:
                    self.print('Error: sell position is less than 0')

        return buy_position, sell_position

    def _log_trade(self, verb, direction, code, quantity, price, retEnter, EnterOrderID):
        self.print(f"{verb}{direction} {quantity} {code}, price: {price:.1f}, base:{self.base_price}, retEnter: {retEnter}, EnterOrderID: {EnterOrderID}")
        if not self.IsBacktest:
            msg = f"Name: {self.name}\n{verb.lower()}{direction}: {code}\nquantity: {quantity}\nprice: {price:.1f}\nbase:{self.base_price}"
            self.dingding(msg)

    def Buy(self, code, quantity, price):  # BaseStrategy
        # timestamp = int(time.time())
        # msg = f"{strategy_name}_buy_{quantity}_{timestamp}"
        retEnter = 0
        EnterOrderID = 0
        direction = '开'

        self.trade_quantity = quantity
        if self.IsBacktest:
            sell_position = self.GetSellPosition(code)
            if sell_position > 0:
                self.api.BuyToCover(quantity, price, code)
            else:
                self.api.Buy(quantity, price, code)
        else:
            if self.send_order_count > self.max_send_order_count:
                self.print('Error: reach order limit')
                return (False, 0)

            buy_position, sell_position = self._resolve_positions_for_order(code)

            if self._position_limit_exceeded(buy_position, sell_position):
                self.print('Error: reach buy position limit')
                return (False, 0)
            if sell_position >= quantity:
                direction = '平'
                retEnter, EnterOrderID = self.api.A_SendOrder(self.api.Enum_Buy(), self.api.Enum_Exit(), quantity, price, code)
            else:
                if sell_position > 0:
                    direction = '平'
                    self.trade_quantity = sell_position
                    retEnter, EnterOrderID = self.api.A_SendOrder(self.api.Enum_Buy(), self.api.Enum_Exit(), sell_position, price, code)
                else:
                    retEnter, EnterOrderID = self.api.A_SendOrder(self.api.Enum_Buy(), self.api.Enum_Entry(), quantity, price, code)
            self.send_order_count += 1

        self._log_trade('Buy', direction, code, quantity, price, retEnter, EnterOrderID)
        return (retEnter == 0, EnterOrderID)

    def Sell(self, code, quantity, price):  # BaseStrategy
        # timestamp = int(time.time())
        # msg = f"{strategy_name}_buy_{quantity}_{timestamp}"
        retEnter = 0
        EnterOrderID = 0
        direction = '开'
        self.trade_quantity = quantity
        if self.IsBacktest:
            buy_position = self.GetBuyPosition(code)
            if buy_position > 0:
                self.api.Sell(quantity, price, code)
            else:
                self.api.SellShort(quantity, price, code)
        else:
            if self.send_order_count > self.max_send_order_count:
                self.print('Error: reach order limit')
                return (False, 0)

            buy_position, sell_position = self._resolve_positions_for_order(code)

            if self._position_limit_exceeded(buy_position, sell_position):
                self.print('Error: reach sell position limit')
                return (False, 0)

            if buy_position >= quantity:
                direction = '平'
                retEnter, EnterOrderID = self.api.A_SendOrder(self.api.Enum_Sell(), self.api.Enum_Exit(), quantity, price, code)
            else:
                if buy_position > 0:
                    direction = '平'
                    self.trade_quantity = buy_position
                    retEnter, EnterOrderID = self.api.A_SendOrder(self.api.Enum_Sell(), self.api.Enum_Exit(), buy_position, price, code)
                else:
                    retEnter, EnterOrderID = self.api.A_SendOrder(self.api.Enum_Sell(), self.api.Enum_Entry(), quantity, price, code)

            self.send_order_count += 1

        self._log_trade('Sell', direction, code, quantity, price, retEnter, EnterOrderID)
        return (retEnter == 0, EnterOrderID)

    def _next_clamped_index(self, current_index, levels):
        return min(current_index + 1, len(levels) - 1)

    def _tick_floor(self, code, price):
        tick = self.api.PriceTick(code)
        return math.floor(price / tick) * tick

    def _tick_ceil(self, code, price):
        tick = self.api.PriceTick(code)
        return math.ceil(price / tick) * tick

    def _position_limit_exceeded(self, buy_position, sell_position):
        orderQty = self.params.get('orderQty', 1)
        maxPositionMultiplier = self.params.get('maxPositionMultiplier', 10)
        return abs(buy_position - sell_position) > orderQty * maxPositionMultiplier

    def _update_max_holding(self):
        holding = abs(self.logical_holding)
        if holding > self.max_logical_holding:
            self.max_logical_holding = holding

    def _check_in_session(self):
        if not self.IsBacktest and not self.api.IsInSession(self.codes[0]):
            if self.print_debug:
                self.print(f'Error: Not in session')
            return False
        return True

    def is_spread_code(self, code):
        return '|M|' in code or '|S|' in code

    def apply_changes(self, changes):
        for key, value in changes.items():
            setattr(self, key, value)

    def existing_order(self):
        tmp = []
        has_filled = False
        for order_id, changes in self.waiting_list:
            status = self.api.A_OrderStatus(order_id)
            if status != self.api.Enum_Filled() and status != self.api.Enum_Canceled():
                tmp.append((order_id, changes))
                self.print(f"Order {order_id} status={status} existing")
            else:
                if status == self.api.Enum_Filled():
                    has_filled = True
                    self.apply_changes(changes)
                    self.save_strategy_state()
                self.print(f"Order {order_id} status={status} removed from waiting list")

        if has_filled and tmp:
            for order_id, changes in tmp:
                self.api.A_DeleteOrder(order_id)
                self.print(f"Order {order_id} deleted due to other order filled")
            tmp = []

        self.waiting_list = tmp
        existing_buy_order = False
        existing_sell_order = False

        for order_id, _ in self.waiting_list:
            if self.api.A_OrderBuyOrSell(order_id) == self.api.Enum_Buy():
                existing_buy_order = True
            elif self.api.A_OrderBuyOrSell(order_id) == self.api.Enum_Sell():
                existing_sell_order = True

        return (existing_buy_order, existing_sell_order)
    def get_state_file_name(self): # BaseStrategy
        return f"{self.config_folder}\\{self.name}.json"

    def _load_strategy_state_raw(self):
        file = self.get_state_file_name()

        if not os.path.exists(file):
            return None
        try:
            with open(file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                self.is_state_loaded = True

                return state
        except Exception as e:
            self.print(f"Error: Failed to load strategy state: {e}")
            return None

    def load_strategy_state(self):
        if self.is_state_loaded:
            return

        state = self._load_strategy_state_raw()
        if state is None:
            self.save_strategy_state()
        elif not self.IsBacktest:
            self.base_price = state['base_price']
            self.logical_holding = state['logical_holding']
            self.buy_index = state['buy_index']
            self.sell_index = state['sell_index']

    def save_strategy_state(self):
        data = {
            'base_price': self.base_price,
            'logical_holding': self.logical_holding,
            'buy_index': self.buy_index,
            'sell_index': self.sell_index,
        }
        file = self.get_state_file_name()
        try:
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.print(f"Error: Failed to save strategy state: {e}")

    def _commit_changes(self, order_id, changes):
        if self.IsBacktest:
            self.apply_changes(changes)
        else:
            self.waiting_list.append((order_id, changes))

    def _reset_price_cache(self):
        self.DailyPricesDate = None
        self.DailyPrices = {}
        self.ATRs = {}
        self.slopes = {}
        self.r_squareds = {}
        self.is_state_loaded = False

    def exit_callback(self, context):
        self.delete_orders()

    def delete_orders(self):
        for order_id, changes in self.waiting_list:
            status = self.api.A_OrderStatus(order_id)
            if status == self.api.Enum_Filled():
                self.apply_changes(changes)
                self.save_strategy_state()
                self.print(f"Order {order_id} filled, applied changes")
            elif status != self.api.Enum_Canceled():
                self.api.A_DeleteOrder(order_id)
                self.print(f"Order {order_id} deleted")
        self.waiting_list = []

    def print(self, string, **kwargs):
        self.api.LogInfo(string, **kwargs)


    def dingding(self, msg):
        webhook_url = f"https://oapi.dingtalk.com/robot/send?access_token={self.dingding_token}"

        message = {
            "msgtype": "text",
            "text": {
                "content": f"{msg}\n{self.dingding_keyword}",
                "at": {
                    "isAtAll": False
                }
            }
        }

        headers = {'Content-Type': 'application/json'}
        try:
            response = requests.post(webhook_url, data=json.dumps(message), headers=headers, timeout=5)
        except Exception as e:
            self.print(f"DingDing exception (ignored): {e}")

class PairLevelGridStrategy(BaseStrategy):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def initialize(self, context, **kwargs):     # PairLevelGridStrategy
        super().initialize(context, **kwargs)
        self.logical_holding = 0
        self.codes = self.params['codes']
        self.name = self.params['name']
        self.buy_levels = [0.6, 0.7, 0.8, 1, 1.5, 2, 4, 6, 8, 14, 22]
        self.sell_levels = [0.6, 0.7, 0.8, 1, 1.5, 2, 4, 6, 8, 14, 22]
        self.buy_index = 0
        self.sell_index = 0

        for code in self.codes:
            self.api.SetBarInterval(code, 'M', 1, 1)
            self.api.SetBarInterval(code, 'D', 1, 100)

        self.api.SetActual()

    def handle_data(self, context):     # PairLevelGridStrategy
        if not super().handle_data(context):
            return

        if not self._check_in_session():
            return

        self.load_strategy_state()

        codes = list(self.codes)

        self.GetDailyPrices(codes)
        self.GetLastPrices(codes)

        if self.IsBacktest and self.api.CurrentBar() == 1:   # PairLevelGridStrategy
            return

        self.RunGridTrading(self.codes[0])

    def RunGridTrading(self, code):    # PairLevelGridStrategy
        self.atr = self.ATRs[code]
        self.slope = self.slopes[code]
        self.r_squared = self.r_squareds[code]
        current_price = self.LastPrices[code]
        existing_buy_order, existing_sell_order = self.existing_order()
        existing_order = existing_buy_order or existing_sell_order

        base_price = self.base_price
        orderQty = self.params.get('orderQty', 1)
        limit = self.params.get('limit')
        order_qty = orderQty
        buy_position = self.GetBuyPosition(code)

        if self.logical_holding == 0 and buy_position == 0:
            ma_20 = talib.MA(self.DailyPrices[code]['Close'], timeperiod=20)
            days_above_ma = np.sum(self.DailyPrices[code]['Close'][-20:] > ma_20[-20:])
            if 6 <= days_above_ma <= 14 and (limit is None or current_price < limit):
            # if up_days >= 2 and (limit is None or current_price < limit):
                base_price = self.DailyPrices[code]['Close'].iloc[-20:].min() + 2 * self.atr
                if self.atr > 0:
                    order_qty = int((self.DailyPrices[code]['Close'].iloc[-20:].max() - self.DailyPrices[code]['Close'].iloc[-20:].min()) / self.atr)
                    if order_qty < orderQty:
                        order_qty = orderQty
                    elif order_qty > orderQty * 5:
                        order_qty = orderQty * 5
                else:
                    order_qty = orderQty * 3
            else:
                base_price = self.DailyPrices[code]['Close'].iloc[-1] / 2

        executed = False

        sell_threshold = 0
        buy_threshold = 0
        if self.sell_index < len(self.sell_levels):
            if buy_position > 0:
                level = self.sell_levels[self.sell_index]
                diff = self.atr * level
                sell_threshold = base_price + diff

                if current_price >= sell_threshold and not existing_order:
                    if buy_position > 5 * order_qty:
                        order_qty = order_qty + 1
                    executed = self.ExecuteSell(code, current_price, order_qty if buy_position >= order_qty else buy_position)
        else:
            self.print(f'Error: sell_index error')

        if self.buy_index < len(self.buy_levels) and not executed:
            level = self.buy_levels[self.buy_index]
            diff = self.atr * level
            buy_threshold = base_price - diff

            if current_price <= buy_threshold and not existing_order:
                executed = self.ExecuteBuy(code, current_price, order_qty)
        elif not executed:
            self.print(f'Error: buy_index error')

        self._update_max_holding()

        if self.print_debug:
            self.print({
                'b_price': base_price,
                'r_b_position': self.GetBuyPosition(code),
                'r_s_position': self.GetSellPosition(code),
                'l_holding': self.logical_holding,
                'b_threshold': buy_threshold,
                's_threshold': sell_threshold,
                'c_price': current_price,
                'e_order': existing_order,
                'yesterday_price': self.DailyPrices[code]['Close'].iloc[-1],
                'b_index': self.buy_index,
                's_index': self.sell_index,
                'code': code,
                'current_date': self.api.TradeDate(),
                'current_time': self.api.CurrentTime(),
                'atr': self.atr,
                'slope': self.slope,
                'r_squared': self.r_squared,
            })
    def ExecuteBuy(self, code, price, quantity):    # PairLevelGridStrategy
        trade_price = self._tick_floor(code, price)
        succeed, order_id = self.Buy(code, quantity, trade_price)
        if not succeed:
            return False

        changes = {}
        changes["logical_holding"] = self.logical_holding + self.trade_quantity
        changes["base_price"] = trade_price
        changes["last_buy_date"] = self.today_str()
        changes["buy_index"] = self._next_clamped_index(self.buy_index, self.buy_levels)
        changes["sell_index"] = 0

        self._commit_changes(order_id, changes)
        return True

    def ExecuteSell(self, code, price, quantity):    # PairLevelGridStrategy
        trade_price = self._tick_ceil(code, price)
        succeed, order_id = self.Sell(code, quantity, trade_price)
        if not succeed:
            return False

        changes = {}
        changes["logical_holding"] = self.logical_holding - self.trade_quantity
        changes["base_price"] = trade_price
        changes["last_sell_date"] = self.today_str()
        changes["sell_index"] = self._next_clamped_index(self.sell_index, self.sell_levels)
        changes["buy_index"] = 0

        self._commit_changes(order_id, changes)
        return True

    def hisover_callback(self, context):   # PairLevelGridStrategy
        self._reset_price_cache()

        if self.api.BuyPosition(self.codes[0]) > 0:
            self.api.Sell(self.api.BuyPosition(self.codes[0]), self.LastPrices[self.codes[0]], self.codes[0])
        if self.api.SellPosition(self.codes[0]) > 0:
            self.api.BuyToCover(self.api.SellPosition(self.codes[0]), self.LastPrices[self.codes[0]], self.codes[0])

        self.print('max position:' + str(self.max_logical_holding))

class SpreadGridStrategy(BaseStrategy):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def initialize(self, context, **kwargs):     # SpreadGridStrategy
        super().initialize(context, **kwargs)
        self.logical_holding = 0
        self.codes = self.params['codes']
        self.name = self.params['name']
        self.buy_levels = [0.6, 0.7, 0.8, 1, 1.5, 2, 4, 6, 8, 14, 22]
        self.sell_levels = [0.6, 0.7, 0.8, 1, 1.5, 2, 4, 6, 8, 14, 22]
        self.buy_index = 0
        self.sell_index = 0
        self.ignore_days_above_ma = self.params.get('ignoreDaysAboveMa', False)
        self.double_first_position = self.params.get('doubleFirstPosition', True)

        for code in self.codes:
            self.api.SetBarInterval(code, 'M', 1, 1)
            self.api.SetBarInterval(code, 'D', 1, 100)

        self.api.SetActual()

    def _calc_order_quantity(self, orderQty):
        orderQuantity = orderQty
        if orderQty == 1 and abs(self.logical_holding) >= 4:
            orderQuantity = 2
        if orderQty > 1 and abs(self.logical_holding) > 3 * orderQty:
            orderQuantity += orderQty // 3
        return orderQuantity

    def _execute_trade(self, trade_func, code, price, quantity, condition_price, is_buy):
        if not self.IsBacktest:
            if is_buy:
                trade_price = self._tick_floor(code, min(price, condition_price))
            else:
                trade_price = self._tick_ceil(code, max(price, condition_price))
            return trade_func(code, trade_price, quantity)
        elif (is_buy and price <= condition_price) or (not is_buy and price >= condition_price):
            if is_buy:
                trade_price = self._tick_floor(code, price)
            else:
                trade_price = self._tick_ceil(code, price)
            return trade_func(code, trade_price, quantity)
    def handle_data(self, context):     # SpreadGridStrategy
        if not super().handle_data(context):
            return

        if not self._check_in_session():
            return

        self.load_strategy_state()

        codes = list(self.codes)

        self.GetDailyPrices([codes[0]])
        self.GetLastPrices([codes[0]])

        if len(self.codes) != 4:
            self.print('Error: codes length should be 4')
            return

        self.RunGridTrading()

    def RunGridTrading(self):    # SpreadGridStrategy
        existing_buy_order, existing_sell_order = self.existing_order()
        existing_order = existing_buy_order or existing_sell_order

        if self.position_closed:
            self.print('position closed')
            return

        self.atr = self.ATRs[self.codes[0]]
        self.slope = self.slopes[self.codes[0]]
        self.r_squared = self.r_squareds[self.codes[0]]
        current_price = self.LastPrices[self.codes[0]]

        base_price = self.base_price
        if self.params.get('firstPosition', True):
            buy_position = self.GetBuyPosition(self.codes[2])
            sell_position = self.GetSellPosition(self.codes[2])
        else:
            buy_position = self.GetSellPosition(self.codes[3])
            sell_position = self.GetBuyPosition(self.codes[3])

        close_prices = self.DailyPrices[self.codes[0]]['Close']
        ma_20 = talib.MA(close_prices, timeperiod=20)
        ma_20_last = ma_20.iat[-1]
        days_above_ma = np.sum(close_prices[-20:] > ma_20[-20:])

        if self.logical_holding == 0 and buy_position == 0 and sell_position == 0:
            base_price = ma_20_last

        sell_threshold = 0
        buy_threshold = 0
        orderQty = self.params.get('orderQty', 1)
        if self.sell_index < len(self.sell_levels):   # SpreadGridStrategy
            level = self.sell_levels[self.sell_index]
            diff = self.atr * level
            sell_threshold = base_price + diff

            orderQuantity = self._calc_order_quantity(orderQty)

            if (self.logical_holding < 0 and abs(self.logical_holding) > orderQty * 5 and abs(self.slope) > 0.3) \
                or (current_price >= sell_threshold and self.logical_holding < 0 and (abs(self.logical_holding) + orderQuantity) >= 7 * orderQty) \
                or (current_price >= sell_threshold and self.logical_holding < 0 and (abs(self.logical_holding) + orderQuantity) > 5 * orderQty and abs(self.slope) > 0.3):
                self.delete_orders()
                self.ExecuteBuy(self.codes[1], current_price, abs(self.logical_holding), True)
                self.position_closed = True
                return

            if not existing_sell_order:
                if self.logical_holding == 0 and abs(self.slope) < 0.3 and current_price <= base_price + self.atr:
                    if 6 <= days_above_ma <= 14 or self.ignore_days_above_ma:
                        quantity = orderQuantity * 2 if self.double_first_position else orderQuantity
                        self._execute_trade(self.ExecuteSell, self.codes[1], current_price, quantity, sell_threshold, is_buy=False)
                else:
                    if self.logical_holding < 0:
                        self._execute_trade(self.ExecuteSell, self.codes[1], current_price, orderQuantity, sell_threshold, is_buy=False)
                    else:
                        if self.double_first_position and self.logical_holding <= orderQty * 2:
                            orderQuantity = orderQty * 2

                        if self.logical_holding <= orderQuantity and buy_position <= orderQuantity:
                            if current_price >= ma_20_last - self.atr * self.buy_levels[0]:
                                self._execute_trade(self.ExecuteSell, self.codes[1], current_price, orderQuantity, sell_threshold, is_buy=False)
                            else:
                                self._execute_trade(self.ExecuteSell, self.codes[1], current_price, orderQuantity, max(ma_20_last - self.atr * self.buy_levels[0], sell_threshold), is_buy=False)
                        else:
                            self._execute_trade(self.ExecuteSell, self.codes[1], current_price, orderQuantity, sell_threshold, is_buy=False)

        else:
            self.print(f'Error: sell_index error')

        if self.buy_index < len(self.buy_levels):   # SpreadGridStrategy
            level = self.buy_levels[self.buy_index]
            diff = self.atr * level
            buy_threshold = base_price - diff

            orderQuantity = self._calc_order_quantity(orderQty)

            if (self.logical_holding > 0 and self.logical_holding > orderQty * 5 and abs(self.slope) > 0.3) \
                or (current_price <= buy_threshold and self.logical_holding > 0 and (self.logical_holding + orderQuantity) >= 7 * orderQty) \
                or (current_price <= buy_threshold and self.logical_holding > 0 and (self.logical_holding + orderQuantity) > 5 * orderQty and abs(self.slope) > 0.3):
                self.delete_orders()
                self.ExecuteSell(self.codes[1], current_price, abs(self.logical_holding), True)
                self.position_closed = True
                return

            if not existing_buy_order:
                if self.logical_holding == 0 and abs(self.slope) < 0.3 and current_price >= base_price - self.atr:
                    if 6 <= days_above_ma <= 14 or self.ignore_days_above_ma:
                        quantity = orderQuantity * 2 if self.double_first_position else orderQuantity
                        self._execute_trade(self.ExecuteBuy, self.codes[1], current_price, quantity, buy_threshold, is_buy=True)
                else:
                    if self.logical_holding > 0:
                        self._execute_trade(self.ExecuteBuy, self.codes[1], current_price, orderQuantity, buy_threshold, is_buy=True)
                    else:
                        if self.double_first_position and abs(self.logical_holding) <= orderQty * 2:
                            orderQuantity = orderQty * 2

                        if abs(self.logical_holding) <= orderQuantity and sell_position <= orderQuantity:
                            if current_price <= ma_20_last + self.atr * self.sell_levels[0]:
                                self._execute_trade(self.ExecuteBuy, self.codes[1], current_price, orderQuantity, buy_threshold, is_buy=True)
                            else:
                                self._execute_trade(self.ExecuteBuy, self.codes[1], current_price, orderQuantity, min(ma_20_last + self.atr * self.sell_levels[0], buy_threshold), is_buy=True)
                        else:
                            self._execute_trade(self.ExecuteBuy, self.codes[1], current_price, orderQuantity, buy_threshold, is_buy=True)
        else:
            self.print(f'Error: buy_index error')

        self._update_max_holding()

        if self.print_debug:
            self.print({
                'b_price': base_price,
                'r_b_position': buy_position,
                'r_s_position': sell_position,
                'l_holding': self.logical_holding,
                'b_threshold': buy_threshold,
                's_threshold': sell_threshold,
                'c_price': current_price,
                'e_order': existing_order,
                'yesterday_price': self.DailyPrices[self.codes[0]]['Close'].iloc[-1],
                'b_index': self.buy_index,
                's_index': self.sell_index,
                'code': self.codes[1],
                'current_date': self.api.TradeDate(),
                'current_time': self.api.CurrentTime(),
                'atr': self.atr,
                'slope': self.slope,
                'r_squared': self.r_squared,
                'days_above_ma': days_above_ma
            })

    def ExecuteBuy(self, code, price, quantity, force = False):    # SpreadGridStrategy
        self.print('ExecuteBuy')

        if not self.IsBacktest and not force:
            for order_id, _ in self.waiting_list:
                if self.api.A_OrderBuyOrSell(order_id) == self.api.Enum_Buy():
                    return False

        succeed, order_id = self.Buy(code, quantity, price)
        if not succeed:
            return False

        changes = {}
        new_holding = self.logical_holding + self.trade_quantity
        changes["logical_holding"] = new_holding
        changes["base_price"] = price
        changes["last_buy_date"] = self.today_str()
        if (self.logical_holding * new_holding < 0) or (new_holding == 0):
            changes["buy_index"] = 0
        else:
            changes["buy_index"] = self._next_clamped_index(self.buy_index, self.buy_levels)
        changes["sell_index"] = 0

        self._commit_changes(order_id, changes)
        return True

    def ExecuteSell(self, code, price, quantity, force = False):    # SpreadGridStrategy
        self.print('ExecuteSell')

        if not self.IsBacktest and not force:
            for order_id, _ in self.waiting_list:
                if self.api.A_OrderBuyOrSell(order_id) == self.api.Enum_Sell():
                    return False

        succeed, order_id = self.Sell(code, quantity, price)
        if not succeed:
            return False

        changes = {}
        new_holding = self.logical_holding - self.trade_quantity
        changes["logical_holding"] = new_holding
        changes["base_price"] = price
        changes["last_sell_date"] = self.today_str()
        if (self.logical_holding * new_holding < 0) or (new_holding == 0):
            changes["sell_index"] = 0
        else:
            changes["sell_index"] = self._next_clamped_index(self.sell_index, self.sell_levels)
        changes["buy_index"] = 0

        self._commit_changes(order_id, changes)
        return True

    def hisover_callback(self, context):   # SpreadGridStrategy
        self._reset_price_cache()

        if self.api.BuyPosition(self.codes[1]) > 0:
            self.api.Sell(self.api.BuyPosition(self.codes[1]), self.LastPrices[self.codes[0]], self.codes[1])
        if self.api.SellPosition(self.codes[1]) > 0:
            self.api.BuyToCover(self.api.SellPosition(self.codes[1]), self.LastPrices[self.codes[0]], self.codes[1])

        self.print('max position:' + str(self.max_logical_holding))
