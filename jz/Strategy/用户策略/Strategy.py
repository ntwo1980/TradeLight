import pandas as pd
import numpy as np
import talib

class BaseStrategy():
    def __init__(self, **kwargs):   # BaseStrategy
        self.DailyPricesDate = None
        self.DailyPrices = {}
        self.ATRs = {}
        self.MinutePrices = {}
        self.LastPrices = {}

    def initialize(self, context, **kwargs):   # BaseStrategy
        self.params = kwargs['params']
        self.api = kwargs['api']
        self.IsBacktest = context.strategyStatus() != 'C'
        self.api.SetOrderWay(1)

    def LastTradeDate(self):
        return str(self.api.TradeDate()) if self.IsBacktest else str(self.api.Q_LastDate())

    def CurrentTime(self):
        return str(self.api.Time()) if self.IsBacktest else str(self.api.CurrentTime())

    def GetDailyPrices(self, context, codes):  # BaseStrategy
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

            self.DailyPrices[code] = df
            self.DailyPricesDate = self.api.TradeDate()

    def GetMinutePrices(self, context, codes):  # BaseStrategy
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

    def GetLastPrices(self, context, codes):  # BaseStrategy
        mintue_prices = self.GetMinutePrices(context, codes)
        last_prices = {}
        for code in codes:
            if self.IsBacktest:
                last_prices[code] = mintue_prices[code].iloc[-1]['Close']
            else:
                last_prices[code] = self.api.Q_Last(code)

        return last_prices

    def handle_data(self, context):   # BaseStrategy
        pass
        # self.print(self.LastTradeDate() + self.CurrentTime())

    def print(self, string, **kwargs):
        self.api.LogInfo(string, **kwargs)

class PairLevelGridStrategy(BaseStrategy):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def initialize(self, context, **kwargs):     # PairLevelGridStrategy
        super().initialize(context, **kwargs)
        self.threshold_ratio = 0.01
        self.pending_switch_to = None
        self.current_held = None
        self.codes = self.params['codes']

        for code in self.codes:
            self.api.SetBarInterval(code, 'M', 1, 2000)
            self.api.SetBarInterval(code, 'D', 1, 500)

    def handle_data(self, context):     # PairLevelGridStrategy
        super().handle_data(context)

        self.GetDailyPrices(context, self.codes)
        self.GetLastPrices(context, self.codes)

        n = len(self.codes)
        undervalued_score = {code: 0 for code in self.codes}
        for i in range(n):
            for j in range(i+1, n):
                code_i = self.codes[i]
                code_j = self.codes[j]

                code_i_daily = self.DailyPrices[code_i]['Close']
                code_j_daily = self.DailyPrices[code_j]['Close']

                # self.print({'code_i': code_i, 'code_i_len': len(code_i_daily), 'code_j': code_j, 'code_j_len': len(code_j_daily)})

                if len(code_i_daily) < 20 or len(code_j_daily) < 20:
                    continue

                code_i_daily = code_i_daily[-20:]
                code_j_daily = code_j_daily[-20:]

                ratio_series = code_i_daily / code_j_daily
                mean_ratio = np.mean(ratio_series)

                code_i_last = self.LastPrices[code_i]
                code_j_last = self.LastPrices[code_j]
                current_ratio = code_i_last / code_j_last

                if current_ratio > mean_ratio * (1 + self.threshold_ratio):
                    undervalued_score[code_j] += 1
                elif current_ratio < mean_ratio * (1 - self.threshold_ratio):
                    undervalued_score[code_i] += 1

        target_code = max(undervalued_score, key=undervalued_score.get)
        self.print(target_code)

        if self.pending_switch_to is not None:
            self.SwitchPosition_Buy(context)
        elif self.current_held and self.current_held != target_stock:
            self.Print(f"Executing portfolio rebalancing: {self.current_held} → {target_stock}")

            old_stock = self.current_held
            new_stock = target_stock
            price_old = self.LastPrices[old_stock]
            price_new = self.LastPrices[target_stock]
            old_base_price = self.base_price

            new_base_price = old_base_price * price_new / price_old
            self.SwitchPosition_Sell(context, self.current_held, current_holding, target_stock, new_base_price)
            if self.IsBacktest:
                self.f(C)
        elif self.current_held:
            self.RunGridTrading(C, self.current_held)
        elif target_stock:
            self.RunGridTrading(C, target_stock)
        # self.print(self.ATRs[target_code])

    def SwitchPosition_Buy(self, context):    # PairLevelGridStrategy
        unit_to_buy = self.params['orderQty']

        if self.ExecuteBuy(context, self.pending_switch_to, self.LastPrices[self.pending_switch_to], self.params['orderQty'], isSwitch = True):
            # self.base_price = self.LastPrices[self.pending_switch_to]
            self.pending_switch_to = None
            # self.SaveStrategyState()

    def SwitchPosition_Sell(self, context, current_holding, new_stock, new_base_price):    # PairLevelGridStrategy
        self.Print(f'SwitchPosition holding is {current_holding}')

        """执行等值换仓：平掉旧股票，用所得资金买入新股票"""
        strategy_name = self.GetUniqueStrategyName(self.Stocks[0])
        price_old = self.LastPrices[self.current_held]
        self.Sell(context, self.current_held, current_holding, price_old, strategy_name)
        self.logical_holding = 0
        self.pending_switch_to = new_stock
        self.pending_switch_cash = current_holding * price_old
        self.current_held = None
        self.base_price = None
        self.new_base_price = new_base_price
        self.SaveStrategyState()
        self.Print(f"Closed position: {current_holding} shares of {self.current_held} @ {price_old:.3f}")

