import json
import math
import os
from datetime import datetime

import numpy as np
import pandas as pd
import requests
import talib


class BaseStrategy():
    STATE_FIELDS = ['base_price', 'logical_holding', 'buy_index', 'sell_index']
    DEFAULT_LEVELS = [0.6, 0.7, 0.8, 1, 1.5, 2, 4, 6, 8, 14, 22]

    def __init__(self, **kwargs):   # BaseStrategy
        self.context = None
        self.logical_holding = 0
        self.name = ""
        self.DailyPricesDate = None
        self.DailyPrices = {}
        self.ATRs = {}
        self.slopes = {}
        self.r_squareds = {}
        self.LastPrices = {}
        self.base_price = 0
        self.buy_index = 0
        self.sell_index = 0
        self.last_buy_date = None
        self.last_buy_time = None
        self.last_sell_date = None
        self.last_sell_time = None
        self.send_order_count = 0
        self.consecutive_buy_count = 0
        self.consecutive_sell_count = 0
        self.max_consecutive_count = 2
        self.max_send_order_count = 20
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

        config_path = os.path.join(self.config_folder, 'config.json')

        if not os.path.exists(config_path):
            self.print('Error: No config file')
        else:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.api.SetUserNo(config['account'])
                self.dingding_token = config['dingding_token']
                self.dingding_keyword = config['dingding_keyword']
                self.print(config['account'])

    def LastTradeDate(self):
        return str(self.api.TradeDate()) if self.IsBacktest else str(self.api.Q_LastDate())

    def today_str(self):
        return datetime.today().strftime('%Y%m%d')

    def calc_log_regression(self, values):
        x = np.arange(len(values))
        shift = values.min() - 1e-6
        y = np.log(values - shift)
        slope, intercept = np.polyfit(x, y, 1)
        r_squared = 1 - (sum((y - (slope * x + intercept))**2) / ((len(y) - 1) * np.var(y, ddof=1)))
        return slope, r_squared

    def fetch_ohlcv(self, code, period):
        return pd.DataFrame({
            'Open':  self.api.Open(code, period, 1),
            'High':  self.api.High(code, period, 1),
            'Low':   self.api.Low(code, period, 1),
            'Close': self.api.Close(code, period, 1),
            'Vol':   self.api.Vol(code, period, 1),
        })

    def adjust_atr(self, atr):
        atr_config = self.params.get('atr')
        if atr_config is not None:
            if self.params.get('fixedAtr', False):
                return atr_config
            elif atr > atr_config * 1.3 or atr < atr_config * 0.7:
                return atr_config
        return atr

    def GetDailyPrices(self, codes):  # BaseStrategy
        if self.DailyPricesDate == self.LastTradeDate():
            return
        for code in codes:
            df = self.fetch_ohlcv(code, 'D')

            if len(df) >= 4:
                atr = talib.ATR(df['High'].values, df['Low'].values, df['Close'].values, timeperiod=10)[-1]
                self.ATRs[code] = self.adjust_atr(atr)
                slope, r_squared = self.calc_log_regression(df['Close'].values[-20:])
                self.slopes[code] = slope
                self.r_squareds[code] = r_squared
            else:
                self.ATRs[code] = None
                self.slopes[code] = None
                self.r_squareds[code] = None

            self.DailyPrices[code] = df.iloc[:-1] if self.IsBacktest else df
            self.DailyPricesDate = self.LastTradeDate()

    def GetLastPrices(self, codes):  # BaseStrategy
        last_prices = {}
        for code in codes:
            last_prices[code] = self.get_last_price(code)

        self.LastPrices = last_prices

    def get_last_price(self, code):
        """Return the most recent price for `code` depending on backtest mode.
        """
        if self.IsBacktest:
            minute_prices = self.fetch_ohlcv(code, 'M')
            return minute_prices.iloc[-1]['Close']
        return self.api.Q_Last(code)

    def daily_close_ma_and_days(self, code, lookback: int = 20, ma_period: int = 20):
        """Return close series, lookback slice, MA series, MA last value, and days above MA.
        """
        close_prices = self.DailyPrices[code]['Close']
        close_look = close_prices.iloc[-lookback:]
        ma = talib.MA(close_prices, timeperiod=ma_period)
        ma_last = ma.iat[-1]
        days_above_ma = np.sum(close_look > ma[-lookback:])
        return close_prices, close_look, ma, ma_last, days_above_ma

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

        if not self.IsBacktest and self.is_intraday_reset_period(now):
            if self.order_deleted:
                self.order_deleted = False
            if self.position_closed:
                self.position_closed = False

            self.send_order_count = 0
            self.consecutive_buy_count = 0
            self.consecutive_sell_count = 0

            return False

        if not self.IsBacktest and self.is_order_deletion_period(now):
            if not self.order_deleted:
                self.order_deleted = True
                self.delete_orders()

            return False

        return True

    def is_intraday_reset_period(self, now):
        """Return True if `now` is within intraday short reset windows.

        These windows reset counters and flags but do not alter semantics.
        """
        return (0.0859 < now < 0.090010) or (0.2059 < now < 0.210010)

    def is_order_deletion_period(self, now):
        """Return True if `now` is within the daily order-deletion window."""
        return 0.2259 < now < 0.2310

    def GetBuyPosition(self, code):    # BaseStrategy
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

    def resolve_positions_for_order(self):    # BaseStrategy
        position_code = self.GetPositionCode()
        buy_position = self.GetBuyPosition(position_code)
        sell_position = self.GetSellPosition(position_code)
        if isinstance(self, SpreadGridStrategy) and not self.params.get('firstPosition', True):
            buy_position, sell_position = sell_position, buy_position

        return buy_position, sell_position

    def log_trade(self, verb, direction, code, quantity, price, retEnter, EnterOrderID):    # BaseStrategy
        self.print(f"{verb}{direction} {quantity} {code}, price: {price:.1f}, base:{self.base_price}, retEnter: {retEnter}, EnterOrderID: {EnterOrderID}")
        if not self.IsBacktest:
            msg = self.build_trade_message(verb, direction, code, quantity, price)
            self.dingding(msg)

    def build_trade_message(self, verb, direction, code, quantity, price):
        """Construct the human-readable trade message used for DingDing.
        """
        return f"Name: {self.name}\n{verb.lower()}{direction}: {code}\nquantity: {quantity}\nprice: {price:.1f}\nbase:{self.base_price}"

    def execute_order(self, is_buy, code, quantity, price):    # BaseStrategy
        retEnter = 0
        EnterOrderID = 0
        direction = '开'
        verb = 'Buy' if is_buy else 'Sell'

        self.trade_quantity = quantity
        if self.IsBacktest:
            if is_buy:
                if self.GetSellPosition(code) > 0:
                    self.api.BuyToCover(quantity, price, code)
                else:
                    self.api.Buy(quantity, price, code)
            else:
                if self.GetBuyPosition(code) > 0:
                    self.api.Sell(quantity, price, code)
                else:
                    self.api.SellShort(quantity, price, code)

            return (True, 0)
        else:
            if self.send_order_count > self.max_send_order_count:
                self.print('Error: reach order limit')
                return (False, 0)

            orderQty = self.params.get('orderQty', 1)
            if is_buy:
                if self.consecutive_buy_count >= self.max_consecutive_count:
                    self.print('Error: reach consecutive buy limit')
                    return (False, 0)

                # Only enforce the "too frequently" cooldown for SpreadGridStrategy
                if isinstance(self, SpreadGridStrategy) \
                    and self.consecutive_buy_count > 0 \
                    and self.logical_holding >= orderQty * 2 \
                    and self.last_buy_time is not None \
                    and self.api.TimeDiff(self.last_buy_time, self.api.CurrentTime()) < 60 * 30:
                    self.print('Error: buy too frequently')
                    return (False, 0)
            else:
                if self.consecutive_sell_count >= self.max_consecutive_count:
                    self.print('Error: reach consecutive sell limit')
                    return (False, 0)

                if isinstance(self, SpreadGridStrategy) \
                    and self.consecutive_sell_count > 0 \
                    and self.logical_holding <= -orderQty * 2 \
                    and self.last_sell_time is not None \
                    and self.api.TimeDiff(self.last_sell_time, self.api.CurrentTime()) < 60 * 30:
                    self.print('Error: sell too frequently')
                    return (False, 0)

            buy_position, sell_position = self.resolve_positions_for_order()

            if self.position_limit_exceeded(buy_position, sell_position):
                self.print(f'Error: reach {verb.lower()} position limit')
                return (False, 0)

            enum_dir = self.api.Enum_Buy() if is_buy else self.api.Enum_Sell()
            cover_position = sell_position if is_buy else buy_position
            direction, retEnter, EnterOrderID = self.send_live_order(enum_dir, cover_position, quantity, price, code)
            if retEnter == 0:
                if is_buy:
                    self.consecutive_buy_count += 1
                    self.consecutive_sell_count = 0
                    self.last_buy_time = self.api.CurrentTime()
                else:
                    self.consecutive_sell_count += 1
                    self.consecutive_buy_count = 0
                    self.last_sell_time = self.api.CurrentTime()

            self.send_order_count += 1

        self.log_trade(verb, direction, code, quantity, price, retEnter, EnterOrderID)
        return (retEnter == 0, EnterOrderID)

    def Buy(self, code, quantity, price):  # BaseStrategy
        return self.execute_order(True, code, quantity, price)

    def Sell(self, code, quantity, price):  # BaseStrategy
        return self.execute_order(False, code, quantity, price)

    def send_live_order(self, enum_direction, cover_position, quantity, price, code):
        if cover_position > 0:
            direction = '平'
            if cover_position < quantity:
                quantity = cover_position
                self.trade_quantity = cover_position
            retEnter, EnterOrderID = self.api.A_SendOrder(enum_direction, self.api.Enum_Exit(), quantity, price, code)
        else:
            direction = '开'
            retEnter, EnterOrderID = self.api.A_SendOrder(enum_direction, self.api.Enum_Entry(), quantity, price, code)
        return direction, retEnter, EnterOrderID

    def next_clamped_index(self, current_index, levels):
        return min(current_index + 1, len(levels) - 1)

    def tick_floor(self, code, price):
        tick = self.api.PriceTick(code)
        return math.floor(price / tick) * tick

    def tick_ceil(self, code, price):
        tick = self.api.PriceTick(code)
        return math.ceil(price / tick) * tick

    def position_limit_exceeded(self, buy_position, sell_position):
        orderQty = self.params.get('orderQty', 1)
        maxPositionMultiplier = self.params.get('maxPositionMultiplier', 10)
        return abs(buy_position - sell_position) > orderQty * maxPositionMultiplier

    def update_max_holding(self):
        self.max_logical_holding = max(self.max_logical_holding, abs(self.logical_holding))

    def check_in_session(self):
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
        remaining_orders = []
        any_filled = False

        # Cache enum values to avoid repeated remote/bound calls
        Enum_Filled = self.api.Enum_Filled()
        Enum_Canceled = self.api.Enum_Canceled()
        Enum_Buy = self.api.Enum_Buy()
        Enum_Sell = self.api.Enum_Sell()

        for order_id, changes in self.waiting_list:
            status = self.api.A_OrderStatus(order_id)
            if status != Enum_Filled and status != Enum_Canceled:
                remaining_orders.append((order_id, changes))
                self.print(f"Order {order_id} status={status} existing")
            else:
                if status == Enum_Filled:
                    any_filled = True
                    self.handle_filled_order(order_id, changes, Enum_Buy, Enum_Sell)
                self.print(f"Order {order_id} status={status} removed from waiting list")

        if any_filled and remaining_orders:
            for order_id, changes in remaining_orders:
                self.api.A_DeleteOrder(order_id)
                self.print(f"Order {order_id} deleted due to other order filled")
            remaining_orders = []

        self.waiting_list = remaining_orders

        # Determine whether active buy/sell orders remain.
        return self.determine_existing_order_flags(remaining_orders, Enum_Buy, Enum_Sell)

    def determine_existing_order_flags(self, orders, Enum_Buy, Enum_Sell):
        """Return (existing_buy_order, existing_sell_order) for given orders.
        """
        existing_buy_order = False
        existing_sell_order = False
        for order_id, _ in orders:
            kind = self.api.A_OrderBuyOrSell(order_id)
            if kind == Enum_Buy:
                existing_buy_order = True
                if existing_sell_order:
                    break
            elif kind == Enum_Sell:
                existing_sell_order = True
                if existing_buy_order:
                    break

        return (existing_buy_order, existing_sell_order)

    def handle_filled_order(self, order_id, changes, Enum_Buy, Enum_Sell):
        """Apply state changes and send notification for a filled order.

        Extracted to improve readability while preserving existing side-effects
        and call ordering.
        """
        self.apply_changes(changes)
        self.save_strategy_state()
        verb = 'Buy' if self.api.A_OrderBuyOrSell(order_id) == Enum_Buy else 'Sell'
        direction = '开' if self.api.A_OrderEntryOrExit(order_id) == self.api.Enum_Entry() else '平'
        price = self.api.A_OrderFilledPrice(order_id)
        quantity = self.api.A_OrderFilledLot(order_id)
        buy_position, sell_position = self.resolve_positions_for_order()

        msg = f"Name: {self.name}\n{verb.lower()}{direction}成交: price: {price:.1f}\nquantity:{quantity}\nposition:{buy_position - sell_position}"
        self.dingding(msg)

    def get_state_file_name(self): # BaseStrategy
        return os.path.join(self.config_folder, f"{self.name}.json")

    def load_strategy_state_raw(self):
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

        state = self.load_strategy_state_raw()
        if state is None:
            self.save_strategy_state()
        elif not self.IsBacktest:
            for field in self.STATE_FIELDS:
                setattr(self, field, state[field])

    def save_strategy_state(self):
        data = {field: getattr(self, field) for field in self.STATE_FIELDS}
        file = self.get_state_file_name()
        try:
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.print(f"Error: Failed to save strategy state: {e}")

    def commit_changes(self, order_id, changes):
        if self.IsBacktest:
            self.apply_changes(changes)
        else:
            self.waiting_list.append((order_id, changes))

    def reset_price_cache(self):
        self.DailyPricesDate = None
        self.DailyPrices = {}
        self.ATRs = {}
        self.slopes = {}
        self.r_squareds = {}
        self.is_state_loaded = False

    def close_all_positions(self, trade_code, price_code):
        if self.api.BuyPosition(trade_code) > 0:
            self.api.Sell(self.api.BuyPosition(trade_code), self.LastPrices[price_code], trade_code)
        if self.api.SellPosition(trade_code) > 0:
            self.api.BuyToCover(self.api.SellPosition(trade_code), self.LastPrices[price_code], trade_code)

    def exit_callback(self, context):
        self.delete_orders()

    def delete_orders(self):
        # Cache enums to avoid repeated bound calls
        Enum_Filled = self.api.Enum_Filled()
        Enum_Canceled = self.api.Enum_Canceled()

        for order_id, changes in self.waiting_list:
            status = self.api.A_OrderStatus(order_id)
            if status == Enum_Filled:
                self.apply_filled_no_notify(order_id, changes)
            elif status != Enum_Canceled:
                self.api.A_DeleteOrder(order_id)
                self.print(f"Order {order_id} deleted")

        self.waiting_list = []

    def apply_filled_no_notify(self, order_id, changes):
        """Apply changes and persist state for a filled order without sending DingDing.
        """
        self.apply_changes(changes)
        self.save_strategy_state()
        self.print(f"Order {order_id} filled, applied changes")

    def print(self, string, **kwargs):
        self.api.LogInfo(string, **kwargs)


    def dingding(self, msg):
        webhook_url = f"https://oapi.dingtalk.com/robot/send?access_token={self.dingding_token}"
        payload = self.build_dingding_payload(msg)

        try:
            requests.post(webhook_url, json=payload, timeout=5)
        except Exception as e:
            self.print(f"DingDing exception (ignored): {e}")

    def build_dingding_payload(self, msg):
        """Construct the DingDing webhook payload. Extracted for clarity.
        """
        return {
            "msgtype": "text",
            "text": {
                "content": f"{msg}\n{self.dingding_keyword}",
            },
            "at": {
                "isAtAll": False
            }
        }

class PairLevelGridStrategy(BaseStrategy):
    def initialize(self, context, **kwargs):     # PairLevelGridStrategy
        super().initialize(context, **kwargs)
        self.codes = self.params['codes']
        self.name = self.params['name']
        self.buy_levels = list(self.DEFAULT_LEVELS)
        self.sell_levels = list(self.DEFAULT_LEVELS)
        self.buy_index = 0
        self.sell_index = 0

        for code in self.codes:
            self.api.SetBarInterval(code, 'M', 1, 1)
            self.api.SetBarInterval(code, 'D', 1, 100)

        self.api.SetActual()

    def GetPositionCode(self):
        return self.codes[0]

    def handle_data(self, context):     # PairLevelGridStrategy
        if not super().handle_data(context):
            return

        if not self.check_in_session():
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
            order_qty, base_price, _, _, _ = self.compute_base_price_from_ma(code, self.atr, orderQty, limit, current_price)

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

        self.update_max_holding()

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
        trade_price = self.tick_floor(code, price)
        succeed, order_id = self.Buy(code, quantity, trade_price)
        if not succeed:
            return False
        changes = self.build_pair_buy_changes(trade_price)
        self.commit_changes(order_id, changes)
        return True

    def build_pair_buy_changes(self, trade_price):
        """Return the changes dict used after a pair-level buy is accepted.
        """
        return {
            "logical_holding": self.logical_holding + self.trade_quantity,
            "base_price": trade_price,
            "last_buy_date": self.today_str(),
            "buy_index": self.next_clamped_index(self.buy_index, self.buy_levels),
            "sell_index": 0,
        }

    def ExecuteSell(self, code, price, quantity):    # PairLevelGridStrategy
        trade_price = self.tick_ceil(code, price)
        succeed, order_id = self.Sell(code, quantity, trade_price)
        if not succeed:
            return False
        changes = self.build_pair_sell_changes(trade_price)
        self.commit_changes(order_id, changes)
        return True


    def compute_base_price_from_ma(self, code, atr, orderQty, limit, current_price):
        """Compute base price and suggested order quantity from MA/close series.

        Returns (order_qty, base_price, days_above_ma, ma_20_last, close_20)
        """
        close_prices, close_20, ma, ma_20_last, days_above_ma = self.daily_close_ma_and_days(code)
        if days_above_ma >= 6 and (limit is None or current_price < limit):
            base_price = close_20.min() + 2 * atr
            if atr > 0:
                order_qty = int((close_20.max() - close_20.min()) / atr)
                if order_qty < orderQty:
                    order_qty = orderQty
                elif order_qty > orderQty * 5:
                    order_qty = orderQty * 5
            else:
                order_qty = orderQty * 3
        else:
            base_price = close_prices.iloc[-1] / 2
            order_qty = orderQty

        return order_qty, base_price, days_above_ma, ma_20_last, close_20

    def build_pair_sell_changes(self, trade_price):
        """Return the changes dict used after a pair-level sell is accepted.
        """
        return {
            "logical_holding": self.logical_holding - self.trade_quantity,
            "base_price": trade_price,
            "last_sell_date": self.today_str(),
            "sell_index": self.next_clamped_index(self.sell_index, self.sell_levels),
            "buy_index": 0,
        }

    def hisover_callback(self, context):   # PairLevelGridStrategy
        self.reset_price_cache()
        self.close_all_positions(self.codes[0], self.codes[0])
        self.print('max position:' + str(self.max_logical_holding))

class SpreadGridStrategy(BaseStrategy):
    def initialize(self, context, **kwargs):     # SpreadGridStrategy
        super().initialize(context, **kwargs)
        self.codes = self.params['codes']
        self.name = self.params['name']
        self.buy_levels = list(self.DEFAULT_LEVELS)
        self.sell_levels = list(self.DEFAULT_LEVELS)
        self.buy_index = 0
        self.sell_index = 0
        self.ignore_days_above_ma = self.params.get('ignoreDaysAboveMa', False)
        self.double_first_position = self.params.get('doubleFirstPosition', True)
        self.stop_lose = self.params.get('stopLose', True)

        for code in self.codes:
            self.api.SetBarInterval(code, 'M', 1, 5000)
            self.api.SetBarInterval(code, 'D', 1, 100)

        self.api.SetActual()

    def execute_trade(self, trade_func, code, price, quantity, condition_price, is_buy):
        if not self.IsBacktest:
            if is_buy:
                trade_price = self.tick_floor(code, min(price, condition_price))
            else:
                trade_price = self.tick_ceil(code, max(price, condition_price))
            return trade_func(code, trade_price, quantity)
        elif (is_buy and price <= condition_price) or (not is_buy and price >= condition_price):
            if is_buy:
                trade_price = self.tick_floor(code, price)
            else:
                trade_price = self.tick_ceil(code, price)
            return trade_func(code, trade_price, quantity)

        return False

    def compute_order_quantity(self, orderQty, for_sell=True):
        """Compute effective orderQuantity used in RunGridTrading.
        """
        orderQuantity = orderQty
        if orderQty == 1:
            if for_sell and self.logical_holding >= 4:
                orderQuantity = 2
            if (not for_sell) and self.logical_holding <= -4:
                orderQuantity = 2
        if orderQty > 1:
            if for_sell and self.logical_holding > 3 * orderQty:
                increments = orderQty // 3
                orderQuantity = orderQuantity + increments
            if (not for_sell) and self.logical_holding < -3 * orderQty:
                increments = orderQty // 3
                orderQuantity = orderQuantity + increments

        return orderQuantity


    def handle_stop_loss_sell(self, current_price, sell_threshold, orderQty, orderQuantity):
        """Check sell-side stop-loss conditions and execute closure if triggered.

        Returns True if a stop-loss action was performed (and caller should return).
        """
        if not self.stop_lose:
            return False

        cond1 = (self.logical_holding < 0 and abs(self.logical_holding) > orderQty * 5 and self.slope > 0.3)
        cond2 = (current_price >= sell_threshold and self.logical_holding < 0 and (abs(self.logical_holding) + orderQuantity) >= 8 * orderQty)
        cond3 = (current_price >= sell_threshold and self.logical_holding < 0 and (abs(self.logical_holding) + orderQuantity) > 5 * orderQty and self.slope > 0.3)

        if cond1 or cond2 or cond3:
            self.delete_orders()
            self.execute_trade(self.ExecuteBuy, self.codes[1], current_price, abs(self.logical_holding), current_price, is_buy=True)
            self.position_closed = True
            return True
        return False

    def handle_stop_loss_buy(self, current_price, buy_threshold, orderQty, orderQuantity):
        """Check buy-side stop-loss conditions and execute closure if triggered.

        Returns True if a stop-loss action was performed (and caller should return).
        """
        if not self.stop_lose:
            return False

        cond1 = (self.logical_holding > 0 and self.logical_holding > orderQty * 5 and self.slope < -0.3)
        cond2 = (current_price <= buy_threshold and self.logical_holding > 0 and (self.logical_holding + orderQuantity) >= 8 * orderQty)
        cond3 = (current_price <= buy_threshold and self.logical_holding > 0 and (self.logical_holding + orderQuantity) > 5 * orderQty and self.slope < -0.3)

        if cond1 or cond2 or cond3:
            self.delete_orders()
            self.execute_trade(self.ExecuteSell, self.codes[1], current_price, abs(self.logical_holding), current_price, is_buy=False)
            self.position_closed = True
            return True
        return False

    def select_sell_trade_params(self, current_price, base_price, sell_threshold, orderQty, orderQuantity, buy_position, ma_20_last, days_above_ma):
        """Return (quantity, condition_price) for a sell attempt or None.

        Mirrors the original branch logic in `RunGridTrading` for the sell side.
        """
        # Case: initial entry when flat
        if self.logical_holding == 0 and self.slope < 0.3 and current_price <= base_price + self.atr:
            if days_above_ma <= 14 or self.ignore_days_above_ma:
                quantity = orderQuantity * 2 if self.double_first_position else orderQuantity
                return quantity, sell_threshold
            return None  # MA filter not passed: no trade (matches original behaviour)

        # Already short: adjust aggressiveness for deeply negative exposure
        if self.logical_holding < 0:
            if self.logical_holding < -orderQty * 4:
                orderQuantity = 2 if orderQty == 1 else orderQuantity - orderQty // 3
            return orderQuantity, sell_threshold

        # Building or flipping to short when currently non-negative
        if self.double_first_position and self.logical_holding <= orderQty * 2:
            orderQuantity = orderQty * 2

        if self.logical_holding <= orderQuantity and buy_position <= orderQuantity:
            trigger = ma_20_last - self.atr * self.buy_levels[0]
            if current_price >= trigger:
                return orderQuantity, sell_threshold
            return orderQuantity, max(trigger, sell_threshold)
        elif sell_threshold > ma_20_last:
            return self.logical_holding, sell_threshold
        else:
            return orderQuantity, sell_threshold

    def select_buy_trade_params(self, current_price, base_price, buy_threshold, orderQty, orderQuantity, sell_position, ma_20_last, days_above_ma):
        """Return (quantity, condition_price) for a buy attempt or None.

        Mirrors the original branch logic in `RunGridTrading` for the buy side.
        """
        # Case: initial entry when flat
        if self.logical_holding == 0 and self.slope > -0.3 and current_price >= base_price - self.atr:
            if days_above_ma >= 6 or self.ignore_days_above_ma:
                quantity = orderQuantity * 2 if self.double_first_position else orderQuantity
                return quantity, buy_threshold
            return None  # MA filter not passed: no trade (matches original behaviour)

        # Already long: reduce aggressiveness if deeply exposed
        if self.logical_holding > 0:
            if self.logical_holding > orderQty * 4:
                orderQuantity = 2 if orderQty == 1 else orderQuantity - orderQty // 3
            return orderQuantity, buy_threshold

        # Building or flipping to long when currently non-positive
        if self.double_first_position and abs(self.logical_holding) <= orderQty * 2:
            orderQuantity = orderQty * 2

        if abs(self.logical_holding) <= orderQuantity and sell_position <= orderQuantity:
            trigger = ma_20_last + self.atr * self.sell_levels[0]
            if current_price <= trigger:
                return orderQuantity, buy_threshold
            return orderQuantity, min(trigger, buy_threshold)
        elif buy_threshold < ma_20_last:
            return abs(self.logical_holding), buy_threshold
        else:
            return orderQuantity, buy_threshold

    def GetPositionCode(self):
        if self.params.get('firstPosition', True):
            return self.codes[2]
        else:
            return self.codes[3]

    def handle_data(self, context):     # SpreadGridStrategy
        if not super().handle_data(context):
            return

        if not self.check_in_session():
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
        buy_position, sell_position = self.resolve_positions_for_order()

        close_prices, close_20, ma_20, ma_20_last, days_above_ma = self.daily_close_ma_and_days(self.codes[0])

        if self.logical_holding == 0 and buy_position == 0 and sell_position == 0:
            base_price = ma_20_last

        sell_threshold = 0
        buy_threshold = 0
        orderQty = self.params.get('orderQty', 1)
        if self.sell_index < len(self.sell_levels):   # SpreadGridStrategy
            level = self.sell_levels[self.sell_index]
            diff = self.atr * level
            sell_threshold = base_price + diff

            orderQuantity = self.compute_order_quantity(orderQty, for_sell=True)

            if self.handle_stop_loss_sell(current_price, sell_threshold, orderQty, orderQuantity):
                return

            if not existing_sell_order:
                params = self.select_sell_trade_params(current_price, base_price, sell_threshold, orderQty, orderQuantity, buy_position, ma_20_last, days_above_ma)
                if params is not None:
                    quantity, condition_price = params
                    self.execute_trade(self.ExecuteSell, self.codes[1], current_price, quantity, condition_price, is_buy=False)

        else:
            self.print(f'Error: sell_index error')

        if self.buy_index < len(self.buy_levels):   # SpreadGridStrategy
            level = self.buy_levels[self.buy_index]
            diff = self.atr * level
            buy_threshold = base_price - diff

            orderQuantity = self.compute_order_quantity(orderQty, for_sell=False)

            if self.handle_stop_loss_buy(current_price, buy_threshold, orderQty, orderQuantity):
                return

            if not existing_buy_order:
                params = self.select_buy_trade_params(current_price, base_price, buy_threshold, orderQty, orderQuantity, sell_position, ma_20_last, days_above_ma)
                if params is not None:
                    quantity, condition_price = params
                    self.execute_trade(self.ExecuteBuy, self.codes[1], current_price, quantity, condition_price, is_buy=True)
        else:
            self.print(f'Error: buy_index error')

        self.update_max_holding()

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

        new_holding = self.logical_holding + self.trade_quantity
        cross_zero = (self.logical_holding * new_holding < 0) or (new_holding == 0)
        orderQty = self.params.get('orderQty', 1)
        changes = self.build_buy_changes(new_holding, price, cross_zero, orderQty)
        self.commit_changes(order_id, changes)
        return True

    def build_buy_changes(self, new_holding, price, cross_zero, orderQty):
        """Build the `changes` dict used after a buy order is accepted.
        """
        return {
            "logical_holding": new_holding,
            "base_price": price,
            "last_buy_date": self.today_str(),
            "buy_index": 0 if cross_zero else self.next_clamped_index(self.buy_index, self.buy_levels),
            "sell_index": 1 if new_holding < -orderQty * 3 else 0
        }

    def ExecuteSell(self, code, price, quantity, force = False):    # SpreadGridStrategy
        self.print('ExecuteSell')

        if not self.IsBacktest and not force:
            for order_id, _ in self.waiting_list:
                if self.api.A_OrderBuyOrSell(order_id) == self.api.Enum_Sell():
                    return False

        succeed, order_id = self.Sell(code, quantity, price)
        if not succeed:
            return False

        new_holding = self.logical_holding - self.trade_quantity
        cross_zero = (self.logical_holding * new_holding < 0) or (new_holding == 0)
        orderQty = self.params.get('orderQty', 1)
        changes = self.build_sell_changes(new_holding, price, cross_zero, orderQty)
        self.commit_changes(order_id, changes)
        return True

    def build_sell_changes(self, new_holding, price, cross_zero, orderQty):
        """Build the `changes` dict used after a sell order is accepted.
        """
        return {
            "logical_holding": new_holding,
            "base_price": price,
            "last_sell_date": self.today_str(),
            "sell_index": 0 if cross_zero else self.next_clamped_index(self.sell_index, self.sell_levels),
            "buy_index": 1 if new_holding > orderQty * 3 else 0
        }

    def hisover_callback(self, context):   # SpreadGridStrategy
        self.reset_price_cache()
        self.close_all_positions(self.codes[1], self.codes[0])
        self.print('max position:' + str(self.max_logical_holding))
