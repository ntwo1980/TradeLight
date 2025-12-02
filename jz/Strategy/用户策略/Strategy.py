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
        self.MinutePrices = {}
        self.LastPrices = {}
        self.base_price = 0
        self.last_buy_date = None
        self.last_sell_date = None
        self.send_order_count = 0
        self.max_send_order_count = 100
        self.max_position = 20
        self.deal = False
        self.is_state_loaded = False
        self.print_debug = True

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
        self.api.SetUserNo('Q20702017')

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
            else:
                self.ATRs[code] = None

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
            return self.api.A_BuyPosition(code)

    def Buy(self, code, quantity, price):  # BaseStrategy
        # timestamp = int(time.time())
        # msg = f"{strategy_name}_buy_{quantity}_{timestamp}"
        retEnter = 0
        EnterOrderID = 0
        if self.IsBacktest:
            self.api.Buy(quantity, price, code)
        else:
            if self.send_order_count > self.max_send_order_count:
                self.print('Error: reach order limit')
                return False

            if not self.IsBacktest and self.GetBuyPosition(code) > self.max_position:
                self.print('Error: reach position limit')
                return False

            retEnter, EnterOrderID = self.api.A_SendOrder(self.api.Enum_Buy(), self.api.Enum_Entry(), quantity, price, code)
            self.send_order_count += 1
        # self.WaitingList.append(msg)

        self.print(f"Buy {quantity} {code}, price: {price:.3f}, retEnter: {retEnter}, EnterOrderID: {EnterOrderID}")
        return retEnter == 0

    def Sell(self, code, quantity, price):  # BaseStrategy
        # timestamp = int(time.time())
        # msg = f"{strategy_name}_buy_{quantity}_{timestamp}"
        retEnter = 0
        EnterOrderID = 0
        if self.IsBacktest:
            self.api.Sell(quantity, price, code)
        else:
            if self.send_order_count > self.max_send_order_count:
                self.print('Error: reach order limit')
                return False

            retEnter, EnterOrderID = self.api.A_SendOrder(self.api.Enum_Sell(), self.api.Enum_ExitToday(), quantity, price, code)
            self.send_order_count += 1
        # self.WaitingList.append(msg)

        self.print(f"Sell {quantity} {code}, price: {price:.3f}, retEnter: {retEnter}, EnterOrderID: {EnterOrderID}")
        return retEnter == 0

    def get_state_file_name(self): # BaseStrategy
        return f"D:\\data\\jizhi\\{self.name}.json"

    def load_strategy_state(self):  # BaseStrategy
        if self.IsBacktest:
            return None

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
            self.Print(f"Error: Failed to load strategy state: {e}")
            return None

    def save_strategy_state(self, data):   # BaseStrategy
        if self.IsBacktest:
            pass
            # self.Print(json.dumps(data, ensure_ascii=False, indent=4))
        else:
            file = self.get_state_file_name()

            try:
                with open(file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                self.Print(f"Error: Failed to save strategy state: {e}")

    def print(self, string, **kwargs):
        self.api.LogInfo(string, **kwargs)

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
        self.buy_levels = [0.5, 0.7, 0.8, 0.9, 1, 2, 4, 6, 8, 14, 22]
        self.sell_levels = [0.5, 0.7, 0.8, 0.9, 1, 2, 4, 6, 8, 14, 22]
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

        if len(self.codes) == 2:
            target_code = self.choose_better(self.codes[0], self.codes[1], self.current_held, self.threshold_ratio)
        elif len(self.codes) == 4:
            better1 = self.choose_better(self.codes[0], self.codes[1], None, 0)
            better2 = self.choose_better(self.codes[2], self.codes[3], None, 0)

            best = self.choose_better(better1, better2, None, 0)
            if self.current_held is None or best == self.current_held:
                target_code = best
            else:
                target_code = self.choose_better(self.current_held, best, self.current_held, self.threshold_ratio)
        else:
            self.print('Error: codes lenght should be 2 or 4')
            return

        if self.print_debug:
            self.print('target: ' + target_code)

        if self.IsBacktest and self.api.CurrentBar() == 1:   # PairLevelGridStrategy
            self.Buy(target_code, 15, self.LastPrices[target_code])
            self.current_held = target_code
            self.logical_holding = 15
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
        if self.print_debug:
            self.print('RunGridTrading')
        self.atr = self.ATRs[code]
        current_price = self.LastPrices[code]

        base_price = self.base_price
        if base_price == 0:
            base_price = self.DailyPrices[code]['Close'].iloc[-1]

        if self.print_debug:
            self.print({
                'current_date': self.api.TradeDate(),
                'current_time': self.api.CurrentTime(),
                'code': code,
                'yesterday_price': self.DailyPrices[code]['Close'].iloc[-1],
                'atr': self.atr,
                'current_held': self.current_held,
                'logical_holding': self.logical_holding,
                'real_position': self.GetBuyPosition(self.current_held),
                'buy_index': self.buy_index,
                'sell_index': self.sell_index,
                'base_price': base_price,
                'current_price': current_price,
            })

        executed = False

        if self.sell_index < len(self.sell_levels) and self.GetBuyPosition(code) > 0:
            level = self.sell_levels[self.sell_index]
            diff = self.atr * level

            sell_threshold = base_price + diff

            if current_price >= sell_threshold:
                executed = self.ExecuteSell(code, current_price, self.params['orderQty'])

        if self.buy_index < len(self.buy_levels):
            level = self.buy_levels[self.buy_index]
            diff = self.atr * level
            buy_threshold = base_price - diff

            if current_price <= buy_threshold:
                executed = self.ExecuteBuy(code, current_price, self.params['orderQty'])

        if executed:
            self.save_strategy_state()
        #
        #     if self.base_price is not None:
        #         self.Print(f"State saved: base_price={self.base_price:.3f}, position={self.logical_holding}, buy_index={self.buy_index}, sell_index={self.sell_index}")
        #     else:
        #         self.Print(f"State saved: base_price=None, position={self.logical_holding}, buy_index={self.buy_index}, sell_index={self.sell_index}")
        # if self.IsBacktest:
        #     self.g(C)

    def SwitchPosition_Buy(self):    # PairLevelGridStrategy
        if not self.IsBacktest and self.api.ExchangeStatus(self.api.ExchangeName(self.pending_switch_to)) != '3':
            self.print(f'Error: Exchange status error')
            return

        unit_to_buy = self.params['orderQty']


        price = self.LastPrices[self.pending_switch_to] if self.IsBacktest else min(self.api.Q_AskPrice(self.pending_switch_to) + self.api.PriceTick(self.pending_switch_to), self.api.Q_UpperLimit(self.pending_switch_to))

        if self.ExecuteBuy(self.pending_switch_to, price, self.pending_switch_quantity, is_switch = True):
            self.base_price = self.new_base_price
            self.pending_switch_to = None
            self.pending_switch_quantity = 0
            self.new_base_price = None

            self.save_strategy_state()

    def SwitchPosition_Sell(self, target_code, new_base_price):    # PairLevelGridStrategy
        if not self.IsBacktest and self.api.ExchangeStatus(self.api.ExchangeName(target_code)) != '3':
            self.print(f'Error: Exchange status error')
            return

        self.pending_switch_quantity = self.api.BuyPosition(self.current_held)
        price = self.LastPrices[self.current_held] if self.IsBacktest else max(self.api.Q_BidPrice(self.current_held) - self.api.PriceTick(self.current_held), self.api.Q_LowLimit(self.current_held))
        if not self.Sell(self.current_held, self.pending_switch_quantity, price):
            return
        self.pending_switch_to = target_code
        self.current_held = None
        self.base_price = None
        self.new_base_price = new_base_price

        self.save_strategy_state()

    def ExecuteBuy(self, code, price, quantity, is_switch = False):    # PairLevelGridStrategy
        if not self.IsBacktest and self.api.ExchangeStatus(self.api.ExchangeName(code)) != '3':
            self.print(f'Error: Exchange status error')
            return False

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
            self.sell_index = 0

        return True

    def ExecuteSell(self, code, price, quantity):    # PairLevelGridStrategy
        if not self.IsBacktest and self.api.ExchangeStatus(self.api.ExchangeName(code)) != '3':
            self.print(f'Error: Exchange status error')
            return False

        if not self.Sell(code, quantity, price):
            return False
        self.logical_holding -= quantity
        self.base_price = price
        self.sell_index += 1
        self.buy_index = 0
        self.last_sell_date = datetime.today().strftime('%Y%m%d')

        return True

    def load_strategy_state(self):  # PairLevelGridStrategy
        if self.IsBacktest:
            return

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

        if self.current_held is not None:
            if self.api.BuyPosition(self.current_held) > 0:
                self.api.Sell(self.api.BuyPosition(self.current_held), self.LastPrices[self.current_held], self.current_held)
            if self.api.SellPosition(self.current_held) > 0:
                self.api.BuyToCover(self.api.SellPosition(self.current_held), self.LastPrices[self.current_held], self.current_held)
