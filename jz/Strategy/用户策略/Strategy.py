import pandas as pd
import numpy as np
from datetime import datetime
import talib

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

    def initialize(self, context, **kwargs):   # BaseStrategy
        self.context = context
        self.params = kwargs['params']
        self.api = kwargs['api']
        self.IsBacktest = context.strategyStatus() != 'C'

        self.api.SetTriggerType(5)  # ToDo
        self.api.SetTriggerType(6) #连接状态触发
        self.api.SetOrderWay(1)

    def LastTradeDate(self):
        return str(self.api.TradeDate()) if self.IsBacktest else str(self.api.Q_LastDate())

    def CurrentTime(self):
        return str(self.api.Time()) if self.IsBacktest else str(self.api.CurrentTime())

    def GetDailyPrices(self, codes):  # BaseStrategy
        if self.DailyPricesDate == self.LastTradeDate():
            return self.DailyPrices

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
            self.DailyPricesDate = self.api.TradeDate()

    def GetMinutePrices(self, codes):  # BaseStrategy
        mintue_prices = {}

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

            mintue_prices[code] = df

        return mintue_prices

    def GetLastPrices(self, codes):  # BaseStrategy
        mintue_prices = self.GetMinutePrices(codes)
        last_prices = {}
        for code in codes:
            if self.IsBacktest:
                last_prices[code] = mintue_prices[code].iloc[-1]['Close']
            else:
                last_prices[code] = self.api.Q_Last(code)

        self.LastPrices = last_prices

    def handle_data(self, context):   # BaseStrategy
        self.context = context
        self.IsBacktest = context.strategyStatus() == 'H'
        self.print(self.LastTradeDate() + self.CurrentTime())

        if context.triggerType() == 'N': 
            if context.triggerData()['ServerType'] == 'T':# 交易
                if context.triggerData()['EventType'] == 1:# 交易连接
                    # 盘中重新启动实盘交易
                    self.api.StartTrade()
                    self.print('StartTrade')
                else: # 交易断开
                    # 盘中暂时停止实盘交易
                    self.api.StopTrade()
                    self.print('StopTrade')

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
        if self.IsBacktest:
            self.api.Buy(quantity, code)
        else:
            self.api.A_SendOrder(self.api.Enum_Buy(), self.api.Enum_Entry(), quantity, price)
        # self.WaitingList.append(msg)

        self.print(f"Buy {quantity} {code}, price: {price:.3f}")

    def Sell(self, code, quantity, price):  # BaseStrategy
        # timestamp = int(time.time())
        # msg = f"{strategy_name}_buy_{quantity}_{timestamp}"
        if self.IsBacktest:
            self.api.Sell(quantity, code)
        else:
            self.api.A_SendOrder(self.api.Enum_Sell(), self.api.Enum_ExitToday(), quantity, price)
        # self.WaitingList.append(msg)

        self.print(f"Sell {quantity} {code}, price: {price:.3f}")

    def print(self, string, **kwargs):
        self.api.LogInfo(string, **kwargs)

class PairLevelGridStrategy(BaseStrategy):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def initialize(self, context, **kwargs):     # PairLevelGridStrategy
        super().initialize(context, **kwargs)
        self.threshold_ratio = 0.01
        self.pending_switch_to = None
        self.new_base_price = None
        self.current_held = None
        self.logical_holding = 0
        self.codes = self.params['codes']
        self.buy_levels = [0.7, 0.8, 0.9, 1, 2, 4, 6, 8, 14, 22]
        self.sell_levels = [0.8, 0.9, 1, 1, 2, 4, 6, 8, 14, 22]
        self.buy_index = 0
        self.sell_index = 0

        for code in self.codes:
            self.api.SetBarInterval(code, 'M', 1, 2000)
            self.api.SetBarInterval(code, 'D', 1, 30)

        self.api.SetActual()

    def handle_data(self, context):     # PairLevelGridStrategy
        if not super().handle_data(context):
            return

        self.GetDailyPrices(self.codes)
        self.GetLastPrices(self.codes)

        # === 仅处理两个股票的配对逻辑 ===
        code_A, code_B = self.codes[0], self.codes[1]
        price_A = self.LastPrices[code_A]
        price_B = self.LastPrices[code_B]

        close_A = self.DailyPrices[code_A]['Close']
        close_B = self.DailyPrices[code_B]['Close']

        if len(close_A) < 20 or len(close_B) < 20:
            # 数据不足，维持现状或默认持有 A
            target_code = self.current_held if self.current_held else code_A
        else:
            ratio_series = close_A[-20:] / close_B[-20:]
            mean_ratio = np.mean(ratio_series)
            current_ratio = price_A / price_B

            if current_ratio > mean_ratio * (1 + self.threshold_ratio):
                target_code = code_B
                self.print('Switching to B (B is undervalued)')
            elif current_ratio < mean_ratio * (1 - self.threshold_ratio):
                target_code = code_A
                self.print('Switching to A (A is undervalued)')
            else:
                # 无显著偏离，维持当前持仓
                target_code = self.current_held if self.current_held else code_A

        self.print('target: ' + target_code)

        # === 原有换仓/交易逻辑（完全不变）===
        if self.pending_switch_to is not None:
            self.SwitchPosition_Buy(context)
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
            # if self.IsBacktest:
            #     self.f(context)
        elif target_code:
            self.RunGridTradingtarget_code)
        elif self.current_held:
            self.RunGridTrading(self.current_held)

    def RunGridTrading(self, code):    # PairLevelGridStrategy
        self.print('RunGridTrading')
        self.atr = self.ATRs[code]
        current_price = self.LastPrices[code]

        base_price = self.base_price
        if base_price == 0:
            base_price = self.DailyPrices[code]['Close'].iloc[-1]

        self.print({
            'current_date': self.api.TradeDate(),
            'current_time': self.api.CurrentTime(),
            'code': code,
            'yesterday_price': self.DailyPrices[code]['Close'].iloc[-1],
            'atr': self.atr,
            'buy_index': self.buy_index,
            'sell_index': self.sell_index,
            'base_price': base_price,
            'current_price': current_price,
            'buy_price': base_price - self.atr * self.buy_levels[self.buy_index],
            'sell_price': base_price + self.atr * self.sell_levels[self.sell_index],
        })

        executed = False

        if self.sell_index < len(self.sell_levels) and self.api.GetBuyPosition(code) > 0:
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
                executed = self.ExecuteBuy(ccode, current_price, self.params['orderQty'])

        # if executed:
        #     self.SaveStrategyState()
        #
        #     if self.base_price is not None:
        #         self.Print(f"State saved: base_price={self.base_price:.3f}, position={self.logical_holding}, buy_index={self.buy_index}, sell_index={self.sell_index}")
        #     else:
        #         self.Print(f"State saved: base_price=None, position={self.logical_holding}, buy_index={self.buy_index}, sell_index={self.sell_index}")
        # if self.IsBacktest:
        #     self.g(C)

    def SwitchPosition_Buy(self):    # PairLevelGridStrategy
        if not self.IsBacktest and self.api.ExchangeStatus(self.api.ExchangeName(self.pending_switch_to)) != '3':
            return

        unit_to_buy = self.params['orderQty']

        if self.ExecuteBuy(self.pending_switch_to, self.LastPrices[self.pending_switch_to], self.params['orderQty'], is_switch = True):

            self.base_price = self.new_base_price
            self.pending_switch_to = None
            self.new_base_price = None

            # self.SaveStrategyState()

    def SwitchPosition_Sell(self, target_code, new_base_price):    # PairLevelGridStrategy
        if not self.IsBacktest and self.api.ExchangeStatus(self.api.ExchangeName(target_code)) != '3':
            return

        # strategy_name = self.GetUniqueStrategyName(self.Stocks[0])
        self.Sell(self.current_held, self.api.BuyPosition(self.current_held), self.LastPrices[self.current_held])
        # self.logical_holding = 0
        self.pending_switch_to = target_code
        self.current_held = None
        self.base_price = None
        self.new_base_price = new_base_price
        # self.SaveStrategyState()
        # self.Print(f"Closed position: {current_holding} shares of {old_stock} @ {price_old:.3f}")

    def ExecuteBuy(self, code, price, quantity, is_switch = False):    # PairLevelGridStrategy
        self.print('buy')
        if not self.IsBacktest and self.api.ExchangeStatus(self.api.ExchangeName(code)) != '3':
            return False

        self.api.Buy(quantity, price, code)
        self.current_held = code
        self.logical_holding += quantity
        self.base_price = price
        # self.LastBuyDate = self.Today   # ToDo
        self.last_buy_date = datetime.today().strftime('%Y%m%d')
        if not is_switch:
            self.buy_index += 1
            self.sell_index = 0

        return True

    def ExecuteSell(self, code, price, quantity):    # PairLevelGridStrategy
        self.print('sell')
        if not self.IsBacktest and self.api.ExchangeStatus(self.api.ExchangeName(code)) != '3':
            return False

        self.api.Sell(quantity, price, code)
        # self.logical_holding -= unit_to_sell
        self.base_price = price
        self.sell_index += 1
        self.buy_index = 0
        self.last_sell_date = datetime.today().strftime('%Y%m%d')

        return True
