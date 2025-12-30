import requests
import pandas as pd
import numpy as np
from datetime import datetime
import talib
import json
import os

class BaseStrategy():
    def __init__(self, **kwargs):   # BaseStrategy
        self.context = None
        self.DailyPricesDate = None
        self.DailyPrices = {}
        self.ATRs = {}
        self.slopes = {}
        self.MinutePrices = {}
        self.LastPrices = {}
        self.base_price = 0
        self.last_buy_date = None
        self.last_sell_date = None
        self.send_order_count = 0
        self.max_send_order_count = 6
        self.max_position = 30
        self.deal = False
        self.is_state_loaded = False
        self.print_debug = True
        self.config_folder = f"D:\\data\\jizhi"
        self.dingding_token = None
        self.dingding_keyword = None
        self.waiting_list = []

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

    def CurrentTime(self):
        return str(self.api.Time()) if self.IsBacktest else str(self.api.CurrentTime())

    def GetDailyPrices(self, codes):  # BaseStrategy
        if self.DailyPricesDate == self.LastTradeDate():
            return

        for code in codes:
            close_prices = self.api.Close(code, 'D', 1)
            open_prices = self.api.Open(code, 'D', 1)
            high_prices = self.api.High(code, 'D', 1)
            low_prices = self.api.Low(code, 'D', 1)
            vol_prices = self.api.Vol(code, 'D', 1)

            df = pd.DataFrame({
                'Open': open_prices,
                'High': high_prices,
                'Low': low_prices,
                'Close': close_prices,
                'Vol': vol_prices
            })

            if len(df) >= 4:
                atr_values = talib.ATR(df['High'].values, df['Low'].values, df['Close'].values, timeperiod=10)
                self.ATRs[code] = atr_values[-1]
                x = np.arange(len(df['Close'].values[-20:]))
                vals = df['Close'].values[-20:]
                shift = vals.min() - 1e-6
                y = np.log(vals - shift)
                slope, intercept = np.polyfit(x, y, 1)
                self.slopes[code] = slope
            else:
                self.ATRs[code] = None
                self.slopes[code] = None

            self.DailyPrices[code] = df.iloc[:-1] if self.IsBacktest else df
            self.DailyPricesDate = self.LastTradeDate()

    def GetMinutePrices(self, codes):  # BaseStrategy
        minute_prices = {}

        for code in codes:
            close_prices = self.api.Close(code, 'M', 1)
            open_prices = self.api.Open(code, 'M', 1)
            high_prices = self.api.High(code, 'M', 1)
            low_prices = self.api.Low(code, 'M', 1)
            vol_prices = self.api.Vol(code, 'M', 1)

            df = pd.DataFrame({
                'Open': open_prices,
                'High': high_prices,
                'Low': low_prices,
                'Close': close_prices,
                'Vol': vol_prices
            })

            minute_prices[code] = df

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
        self.print(self.LastTradeDate() + self.CurrentTime())

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

    def Buy(self, code, quantity, price):  # BaseStrategy
        # timestamp = int(time.time())
        # msg = f"{strategy_name}_buy_{quantity}_{timestamp}"
        retEnter = 0
        EnterOrderID = 0
        if self.IsBacktest:
            sell_position = self.GetSellPosition(code)
            if sell_position > 0:
                self.api.BuyToCover(quantity, price, code)
            else:
                self.api.Buy(quantity, price, code)
        else:
            if self.send_order_count > self.max_send_order_count:
                self.print('Error: reach order limit')
                return False

            if self.is_spread_code(code):
                buy_position = self.GetBuyPosition(self.codes[2])
                sell_position = self.GetSellPosition(self.codes[2])

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

            if abs(buy_position - sell_position) > self.max_position:
                self.print('Error: reach buy position limit')
                return False

            if sell_position >= quantity:
                retEnter, EnterOrderID = self.api.A_SendOrder(self.api.Enum_Buy(), self.api.Enum_Exit(), quantity, price, code)
                if retEnter == 0:
                    self.waiting_list.append(EnterOrderID)
            else:
                if sell_position > 0:
                    retEnter, EnterOrderID = self.api.A_SendOrder(self.api.Enum_Buy(), self.api.Enum_Exit(), sell_position, price, code)
                    if retEnter == 0:
                        self.waiting_list.append(EnterOrderID)
                if retEnter == 0:
                    retEnter, EnterOrderID = self.api.A_SendOrder(self.api.Enum_Buy(), self.api.Enum_Entry(), quantity - sell_position, price, code)
                    if retEnter == 0:
                        self.waiting_list.append(EnterOrderID)
            self.send_order_count += 1

        self.print(f"Buy {quantity} {code}, price: {price:.1f}, base:{self.base_price}, retEnter: {retEnter}, EnterOrderID: {EnterOrderID}")
        if not self.IsBacktest:
            msg = f"Name: {self.name}\nbuy: {code}\nquantity: {quantity}\nprice: {price:.1f}\nbase:{self.base_price}"
            self.dingding(msg)
        return retEnter == 0

    def Sell(self, code, quantity, price):  # BaseStrategy
        # timestamp = int(time.time())
        # msg = f"{strategy_name}_buy_{quantity}_{timestamp}"
        retEnter = 0
        EnterOrderID = 0
        if self.IsBacktest:
            buy_position = self.GetBuyPosition(code)
            if buy_position > 0:
                self.api.Sell(quantity, price, code)
            else:
                self.api.SellShort(quantity, price, code)
        else:
            if self.send_order_count > self.max_send_order_count:
                self.print('Error: reach order limit')
                return False

            if '|M|' in code:
                buy_position = self.GetBuyPosition(self.codes[2])
                sell_position = self.GetSellPosition(self.codes[2])

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

            if abs(sell_position - buy_position) > self.max_position:
                self.print('Error: reach sell position limit')
                return False

            if buy_position >= quantity:
                retEnter, EnterOrderID = self.api.A_SendOrder(self.api.Enum_Sell(), self.api.Enum_Exit(), quantity, price, code)
            else:
                if buy_position > 0:
                    retEnter, EnterOrderID = self.api.A_SendOrder(self.api.Enum_Sell(), self.api.Enum_Exit(), buy_position, price, code)
                    if retEnter == 0:
                        self.waiting_list.append(EnterOrderID)
                if retEnter == 0:
                    retEnter, EnterOrderID = self.api.A_SendOrder(self.api.Enum_Sell(), self.api.Enum_Entry(), quantity - buy_position, price, code)
                    if retEnter == 0:
                        self.waiting_list.append(EnterOrderID)

            self.send_order_count += 1

        self.print(f"Sell {quantity} {code}, price: {price:.1f}, base:{self.base_price}, retEnter: {retEnter}, EnterOrderID: {EnterOrderID}")

        if not self.IsBacktest:
            msg = f"Name: {self.name}\nsell: {code}\nquantity: {quantity}\nprice: {price:.1f}\nbase:{self.base_price}"
            self.dingding(msg)
        return retEnter == 0

    def is_spread_code(self, code):
        return '|M|' in code or '|S|' in code

    def existing_order(self):
        tmp = []
        for o in self.waiting_list:
            status = self.api.A_OrderStatus(o)
            if status != self.api.Enum_Filled() and status != self.api.Enum_Canceled():
                tmp.append(o)
                self.print(f"Order {o} status={status} existing")
            else:
                self.print(f"Order {o} status={status} removed from waiting list")

        self.waiting_list = tmp
        return len(self.waiting_list) > 0

    def get_state_file_name(self): # BaseStrategy
        return f"{self.config_folder}\\{self.name}.json"

    def load_strategy_state(self):  # BaseStrategy
        if self.is_state_loaded:
            raise Exception("state has been loaded")

        file = self.get_state_file_name()

        if not os.path.exists(file):
            return None
        try:
            with open(file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                self.is_state_loaded= True

                return state
        except Exception as e:
            self.print(f"Error: Failed to load strategy state: {e}")
            return None

    def save_strategy_state(self, data):   # BaseStrategy
        file = self.get_state_file_name()

        try:
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self.print(f"Error: Failed to save strategy state: {e}")

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
        self.threshold_ratio = self.params['threshold']
        self.pending_switch_to = None
        self.pending_switch_quantity = 0
        self.new_base_price = None
        self.current_held = None
        self.logical_holding = 0
        self.codes = self.params['codes']
        self.name = self.params['name']
        self.buy_levels = [0.7, 0.7, 0.7, 0.7, 0.8, 0.8, 0.8, 0.9, 1, 1.5, 2, 4, 6, 8, 14, 22]
        self.sell_levels = [0.7, 0.7, 0.7, 0.7, 0.8, 0.8, 0.8, 0.9, 1, 1.5, 2, 4, 6, 8, 14, 22]
        self.buy_index = 0
        self.sell_index = 0

        for code in self.codes:
            self.api.SetBarInterval(code, 'M', 1, 1)
            self.api.SetBarInterval(code, 'D', 1, 100)

        self.api.SetActual()

    def choose_better(self, code_A, code_B, default_code, threshold_ratio):
        if default_code and default_code != code_A and default_code != code_B:
            default_code = None

        price_A = self.LastPrices[code_A]
        price_B = self.LastPrices[code_B]

        close_A = self.DailyPrices[code_A]['Close']
        close_B = self.DailyPrices[code_B]['Close']

        if len(close_A) < 20 or len(close_B) < 20:
            target_code = default_code if default_code else code_A
        else:
            ratio_series = close_A[-20:] / close_B[-20:]
            mean_ratio = np.mean(ratio_series)
            current_ratio = price_A / price_B

            if current_ratio > mean_ratio * (1 + threshold_ratio):
                target_code = code_B
                if self.print_debug:
                    self.print(f'B is undervalued({code_A}, {code_B})')
            elif current_ratio < mean_ratio * (1 - threshold_ratio):
                target_code = code_A
                if self.print_debug:
                    self.print(f'A is undervalued({code_A}, {code_B})')
            else:
                if self.print_debug:
                    self.print(f'None is undervalued({code_A}, {code_B})')
                target_code = default_code if default_code else code_A

        return target_code

    def handle_data(self, context):     # PairLevelGridStrategy
        if not super().handle_data(context):
            return

        if not self.IsBacktest and not self.api.IsInSession(self.codes[0]):
            if self.print_debug:
                self.print(f'Error: Not in session')
            return

        self.load_strategy_state()

        codes = list(self.codes)
        if self.current_held and self.current_held not in codes:
            codes.append(self.current_held)

        self.GetDailyPrices(codes)
        self.GetLastPrices(codes)

        if len(self.codes) == 1:
            target_code = self.codes[0]
        elif len(self.codes) == 2:
            target_code = self.choose_better(self.codes[0], self.codes[1], self.current_held, self.threshold_ratio)
        elif len(self.codes) == 4:
            better1 = self.choose_better(self.codes[0], self.codes[1], None, 0)
            better2 = self.choose_better(self.codes[2], self.codes[3], None, 0)

            best = self.choose_better(better1, better2, None, 0)
            if self.current_held is None or best == self.current_held or self.current_held not in self.codes:
                target_code = best
            else:
                target_code = self.choose_better(self.current_held, best, self.current_held, self.threshold_ratio)
        else:
            self.print('Error: codes length should be 1 or 2 or 4')
            return

        # if self.print_debug:
        #     self.print('target: ' + target_code)

        if self.IsBacktest and self.api.CurrentBar() == 1:   # PairLevelGridStrategy
            # self.Buy(target_code, 15, self.LastPrices[target_code])
            self.current_held = target_code
            # self.logical_holding = 15
            return
        # elif not self.IsBacktest and not self.deal:
        #     self.Buy(target_code, 4, self.LastPrices[target_code])
        #     self.current_held = target_code
        #     self.logical_holding += 4
        #     self.deal = True

        if self.pending_switch_to is not None:
            self.SwitchPosition_Buy()
        elif self.current_held and self.current_held != target_code and self.GetBuyPosition(self.current_held) > 0:
            self.print({
                'current_date': self.api.TradeDate(),
                'current_time': self.api.CurrentTime(),
                'current_held': self.current_held,
                'target_code': target_code,
                'current_held_price': self.LastPrices[self.current_held],
                'target_price': self.LastPrices[target_code],
            })
            self.print(f"Executing portfolio rebalancing: {self.current_held} → {target_code}")

            old_code = self.current_held
            price_old = self.LastPrices[old_code]
            price_new = self.LastPrices[target_code]
            old_base_price = self.base_price

            new_base_price = old_base_price * price_new / price_old
            self.SwitchPosition_Sell(target_code, new_base_price)
        elif target_code:
            self.RunGridTrading(target_code)
        elif self.current_held:
            self.RunGridTrading(self.current_held)

    def RunGridTrading(self, code):    # PairLevelGridStrategy
        # if self.print_debug:
        #     self.print('RunGridTrading')
        self.atr = self.ATRs[code]
        current_price = self.LastPrices[code]
        existing_order = self.existing_order()

        base_price = self.base_price
        order_qty = self.params['orderQty']
        buy_position = self.GetBuyPosition(code)

        if self.logical_holding == 0 and buy_position == 0:
            up_days = (self.DailyPrices[code]['Close'].pct_change().iloc[-10:] > 0).sum()
            if up_days >= 5:
                base_price = self.DailyPrices[code]['Close'].iloc[-20:].min() + self.atr
                if self.atr > 0:
                    order_qty = int((self.DailyPrices[code]['Close'].iloc[-20:].max() / self.DailyPrices[code]['Close'].iloc[-20:].min()) / self.atr)
                    if order_qty < self.params['orderQty']:
                        order_qty = self.params['orderQty']
                    elif order_qty > self.params['orderQty'] * 5:
                        order_qty = self.params['orderQty'] * 5
                else:
                    order_qty = self.params['orderQty'] * 3
            else:
                base_price = self.DailyPrices[code]['Close'].iloc[-1] * 100

        executed = False

        sell_threshold = 0
        buy_threshold = 0
        if self.sell_index < len(self.sell_levels):
            if buy_position > 0:
                level = self.sell_levels[self.sell_index]
                diff = self.atr * level
                sell_threshold = base_price + diff

                if current_price >= sell_threshold and not existing_order:
                    executed = self.ExecuteSell(code, current_price, order_qty if buy_position >= order_qty else buy_position)
        else:
            self.print(f'Error: sell_index error')

        if self.buy_index < len(self.buy_levels):
            level = self.buy_levels[self.buy_index]
            diff = self.atr * level
            buy_threshold = base_price - diff

            if current_price <= buy_threshold and not existing_order:
                executed = self.ExecuteBuy(code, current_price, order_qty)
        else:
            self.print(f'Error: buy_index error')

        if executed and not self.IsBacktest:
            self.save_strategy_state()

        if self.print_debug:
            self.print({
                'b_price': base_price,
                'r_b_position': self.GetBuyPosition(code),
                'r_s_position': self.GetSellPosition(code),
                'b_threshold': buy_threshold,
                's_threshold': sell_threshold,
                'l_holding': self.logical_holding,
                'c_price': current_price,
                'e_order': existing_order,
                'yesterday_price': self.DailyPrices[code]['Close'].iloc[-1],
                'b_index': self.buy_index,
                's_index': self.sell_index,
                'code': code,
                'current_date': self.api.TradeDate(),
                'current_time': self.api.CurrentTime(),
                'atr': self.atr,
                'current_held': self.current_held,
            })

    def SwitchPosition_Buy(self):    # PairLevelGridStrategy
        if self.existing_order():
            return
        unit_to_buy = self.params['orderQty']

        price = self.LastPrices[self.pending_switch_to] if self.IsBacktest else min(self.api.Q_AskPrice(self.pending_switch_to) + self.api.PriceTick(self.pending_switch_to), self.api.Q_UpperLimit(self.pending_switch_to))

        if self.ExecuteBuy(self.pending_switch_to, price, self.pending_switch_quantity, is_switch = True):
            self.base_price = self.new_base_price
            self.pending_switch_to = None
            self.pending_switch_quantity = 0
            self.new_base_price = None

            if not self.IsBacktest:
                self.save_strategy_state()

    def SwitchPosition_Sell(self, target_code, new_base_price):    # PairLevelGridStrategy
        self.pending_switch_quantity = self.api.BuyPosition(self.current_held)
        price = self.LastPrices[self.current_held] if self.IsBacktest else max(self.api.Q_BidPrice(self.current_held) - self.api.PriceTick(self.current_held), self.api.Q_LowLimit(self.current_held))
        if not self.Sell(self.current_held, self.pending_switch_quantity, price):
            return
        self.pending_switch_to = target_code
        self.current_held = None
        self.base_price = None
        self.new_base_price = new_base_price

        if not self.IsBacktest:
            self.save_strategy_state()

    def ExecuteBuy(self, code, price, quantity, is_switch = False):    # PairLevelGridStrategy
        if not self.Buy(code, quantity, price):
            return False

        self.current_held = code
        if not is_switch:
            self.logical_holding += quantity
        self.base_price = price
        # self.LastBuyDate = self.Today   # ToDo
        self.last_buy_date = datetime.today().strftime('%Y%m%d')
        if not is_switch:
            self.buy_index += 1
            if self.buy_index >= len(self.buy_levels):
                self.buy_index = len(self.buy_levels) - 1
            self.sell_index = 0

        return True

    def ExecuteSell(self, code, price, quantity):    # PairLevelGridStrategy
        if not self.Sell(code, quantity, price):
            return False
        self.logical_holding -= quantity
        self.base_price = price
        self.sell_index += 1
        if self.sell_index >= len(self.sell_levels):
            self.sell_index = len(self.sell_levels) - 1
        self.buy_index = 0
        self.last_sell_date = datetime.today().strftime('%Y%m%d')

        return True

    def load_strategy_state(self):  # PairLevelGridStrategy
        if self.is_state_loaded:
            return

        state = super().load_strategy_state()
        if state is None:
            self.save_strategy_state()
        else:
            self.current_held = state['current_held']
            self.base_price = state['base_price']
            self.logical_holding = state['logical_holding']
            self.buy_index = state['buy_index']
            self.sell_index = state['sell_index']

    def save_strategy_state(self):   # PairLevelGridStrategy
        data = {
            'current_held': self.current_held,
            'base_price': self.base_price,
            'logical_holding': self.logical_holding,
            'buy_index': self.buy_index,
            'sell_index': self.sell_index,
        }

        super().save_strategy_state(data)

    def hisover_callback(self, context):
        self.DailyPricesDate = None
        self.DailyPrices = {}
        self.ATRs = {}
        self.slopes = {}
        self.is_state_loaded = False

        if self.current_held is not None:
            if self.api.BuyPosition(self.current_held) > 0:
                self.api.Sell(self.api.BuyPosition(self.current_held), self.LastPrices[self.current_held], self.current_held)
            if self.api.SellPosition(self.current_held) > 0:
                self.api.BuyToCover(self.api.SellPosition(self.current_held), self.LastPrices[self.current_held], self.current_held)

class SpreadGridStrategy(BaseStrategy):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def initialize(self, context, **kwargs):     # SpreadGridStrategy
        super().initialize(context, **kwargs)
        self.pending_switch_to = None
        self.pending_switch_quantity = 0
        self.current_held = None
        self.logical_holding = 0
        self.codes = self.params['codes']
        self.name = self.params['name']
        self.buy_levels = [0.7, 0.7, 0.7, 0.8, 0.8, 0.9, 1, 1.5, 2, 4, 6, 8, 14, 22]
        self.sell_levels = [0.7, 0.7, 0.7, 0.8, 0.8, 0.9, 1, 1.5, 2, 4, 6, 8, 14, 22]
        self.buy_index = 0
        self.sell_index = 0

        for code in self.codes:
            self.api.SetBarInterval(code, 'M', 1, 1)
            self.api.SetBarInterval(code, 'D', 1, 100)

        self.api.SetActual()

    def handle_data(self, context):     # SpreadGridStrategy
        if not super().handle_data(context):
            return

        if not self.IsBacktest and not self.api.IsInSession(self.codes[0]):
            if self.print_debug:
                self.print(f'Error: Not in session')
            return

        self.load_strategy_state()

        codes = list(self.codes)
        if self.current_held and self.current_held not in codes:
            codes.append(self.current_held)

        self.GetDailyPrices([codes[0]])
        self.GetLastPrices([codes[0]])

        if len(self.codes) != 4:
            self.print('Error: codes length should be 4')
            return

        self.RunGridTrading()

    def RunGridTrading(self):    # SpreadGridStrategy
        # if self.print_debug:
        #     self.print('RunGridTrading')
        self.atr = self.ATRs[self.codes[0]]
        self.slope = self.slopes[self.codes[0]]
        current_price = self.LastPrices[self.codes[0]]

        existing_order = self.existing_order()
        base_price = self.base_price
        buy_position = self.GetBuyPosition(self.codes[2])
        sell_position = self.GetSellPosition(self.codes[2])

        if self.logical_holding == 0 and buy_position == 0 and sell_position == 0:
            close_prices = self.DailyPrices[self.codes[0]]['Close']

            base_price = sum(close_prices[-10:]) / 10

        executed = False

        sell_threshold = 0
        buy_threshold = 0
        if self.sell_index < len(self.sell_levels):
            level = self.sell_levels[self.sell_index]
            if self.sell_index > 0:
                if self.logical_holding < -6 * self.params['orderQty']:
                    level = level * 1.2
                elif self.logical_holding < -3 * self.params['orderQty']:
                    level = level * 1.1
            diff = self.atr * level
            sell_threshold = base_price + diff

            if current_price >= sell_threshold and not existing_order:
                sell = True
                if self.logical_holding == self.params['orderQty'] and buy_position == self.params['orderQty']:
                    close_prices = self.DailyPrices[self.codes[0]]['Close']
                    base_price = sum(close_prices[-10:]) / 10
                    if current_price < base_price - self.atr * self.buy_levels[0]:
                        sell = False
                if sell:
                    executed = self.ExecuteSell(self.codes[1], current_price, self.params['orderQty'])
        else:
            self.print(f'Error: sell_index error')

        if self.buy_index < len(self.buy_levels):
            level = self.buy_levels[self.buy_index]
            if self.buy_index > 0:
                if self.logical_holding > 6 * self.params['orderQty']:
                    level = level * 1.2
                elif self.logical_holding > 3 * self.params['orderQty']:
                    level = level * 1.1
            diff = self.atr * level
            buy_threshold = base_price - diff

            if current_price <= buy_threshold and not existing_order:
                buy = True
                if self.logical_holding == -self.params['orderQty'] and sell_position == self.params['orderQty']:
                    close_prices = self.DailyPrices[self.codes[0]]['Close']
                    base_price = sum(close_prices[-10:]) / 10
                    if current_price > base_price + self.atr * self.sell_levels[0]:
                        buy = False

                if buy:
                    executed = self.ExecuteBuy(self.codes[1], current_price, self.params['orderQty'])
        else:
            self.print(f'Error: buy_index error')

        if executed and not self.IsBacktest:
            self.save_strategy_state()

        if self.print_debug:
            self.print({
                'b_price': base_price,
                'r_b_position': self.GetBuyPosition(self.codes[2]),
                'r_s_position': self.GetSellPosition(self.codes[2]),
                'b_threshold': buy_threshold,
                's_threshold': sell_threshold,
                'l_holding': self.logical_holding,
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
                'current_held': self.current_held,
            })

    def SwitchPosition_Buy(self):    # SpreadGridStrategy
        if self.existing_order():
            return
        unit_to_buy = self.params['orderQty']

        price = self.LastPrices[self.pending_switch_to] if self.IsBacktest else min(self.api.Q_AskPrice(self.pending_switch_to) + self.api.PriceTick(self.pending_switch_to), self.api.Q_UpperLimit(self.pending_switch_to))

        if self.ExecuteBuy(self.pending_switch_to, price, self.pending_switch_quantity, is_switch = True):
            self.base_price = self.new_base_price
            self.pending_switch_to = None
            self.pending_switch_quantity = 0
            self.new_base_price = None

            if not self.IsBacktest:
                self.save_strategy_state()

    def SwitchPosition_Sell(self, target_code, new_base_price):    # SpreadGridStrategy
        self.pending_switch_quantity = self.api.BuyPosition(self.current_held)
        price = self.LastPrices[self.current_held] if self.IsBacktest else max(self.api.Q_BidPrice(self.current_held) - self.api.PriceTick(self.current_held), self.api.Q_LowLimit(self.current_held))
        if not self.Sell(self.current_held, self.pending_switch_quantity, price):
            return
        self.pending_switch_to = target_code
        self.current_held = None
        self.base_price = None
        self.new_base_price = new_base_price

        if not self.IsBacktest:
            self.save_strategy_state()

    def ExecuteBuy(self, code, price, quantity, is_switch = False):    # SpreadGridStrategy
        self.print('ExecuteBuy')
        if not self.Buy(code, quantity, price):
            return False

        self.current_held = code
        original_holding = self.logical_holding
        if not is_switch:
            self.logical_holding += quantity
        self.base_price = price
        # self.LastBuyDate = self.Today   # ToDo
        self.last_buy_date = datetime.today().strftime('%Y%m%d')
        if not is_switch:
            if (original_holding * self.logical_holding < 0) or (self.logical_holding == 0):
                self.buy_index = 0
            else:
                self.buy_index += 1
            if self.buy_index >= len(self.buy_levels):
                self.buy_index = len(self.buy_levels) - 1
            self.sell_index = 0

        return True

    def ExecuteSell(self, code, price, quantity):    # SpreadGridStrategy
        self.print('ExecuteSell')
        if not self.Sell(code, quantity, price):
            return False
        original_holding = self.logical_holding
        self.logical_holding -= quantity
        self.base_price = price
        if (original_holding * self.logical_holding < 0) or (self.logical_holding == 0):
            self.sell_index = 0
        else:
            self.sell_index += 1
        if self.sell_index >= len(self.sell_levels):
            self.sell_index = len(self.sell_levels) - 1
        self.buy_index = 0
        self.last_sell_date = datetime.today().strftime('%Y%m%d')

        return True

    def load_strategy_state(self):  # SpreadGridStrategy
        if self.is_state_loaded:
            return

        state = super().load_strategy_state()
        self.print(state)
        if state is None:
            self.save_strategy_state()
        else:
            self.current_held = state['current_held']
            self.base_price = state['base_price']
            self.logical_holding = state['logical_holding']
            self.buy_index = state['buy_index']
            self.sell_index = state['sell_index']

    def save_strategy_state(self):   # SpreadGridStrategy
        data = {
            'current_held': self.current_held,
            'base_price': self.base_price,
            'logical_holding': self.logical_holding,
            'buy_index': self.buy_index,
            'sell_index': self.sell_index,
        }

        super().save_strategy_state(data)

    def hisover_callback(self, context):
        self.DailyPricesDate = None
        self.DailyPrices = {}
        self.ATRs = {}
        self.is_state_loaded = False

        if self.current_held is not None:
            if self.api.BuyPosition(self.codes[1]) > 0:
                self.api.Sell(self.api.BuyPosition(self.codes[1]), self.LastPrices[self.codes[0]], self.codes[1])
            if self.api.SellPosition(self.codes[1]) > 0:
                self.api.BuyToCover(self.api.SellPosition(self.codes[1]), self.LastPrices[self.codes[0]], self.codes[1])
