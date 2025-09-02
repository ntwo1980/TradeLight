import datetime
import time
import pandas as pd
import numpy as np
import talib
import json
import os


class PairGridStrategy(BaseStrategy):
    def __init__(self, **kwargs):
        super().__init__(strategyPrefix='pairgrid', strategyId='a', **kwargs)
        self.stock_A = self.Stocks[0]
        self.stock_B = self.Stocks[1]

    def init(self, C):
        super().init(C)

        self.prices = None
        self.prices_date = None
        self.base_price = None
        self.logical_holding = 0
        self.levels = [2, 4, 8, 12, 22]
        self.buy_index = 0
        self.sell_index = 0
        self.atr = 0
        self.grid_unit = 0
        self.max_price = 0
        self.yesterday_price = 0
        self.current_held = None
        self.threshold_ratio = 0.01

        C.set_universe(self.Stocks)

        self.LoadStrategyState(self.Stocks, self.StockNames)

        state = self.State
        if state and state['base_price'] is not None:
            self.current_held = state['current_held']
            self.base_price = state['base_price']
            self.logical_holding = state['logical_holding']
            print(f"Loaded state from file: base_price={self.base_price}, position={self.logical_holding}, current_held={self.current_held}")
        elif self.IsBacktest:
            print("No historical state found, will initialize base_price using first average")

    def UpdateMarketData(self, C, stocks):
        yesterday = self.GetYesterday(C)
        if self.prices_date is None or self.prices_date != yesterday:
            self.prices = self.GetHistoricalPrices(C, self.Stocks, fields=['high', 'low', 'close'], period='1d', count=30)
            self.prices_date = yesterday


    def SwitchPosition(self, C, old_stock, current_holding, new_stock):
        print(f'SwitchPosition holding is {current_holding}')

        """执行等值换仓：平掉旧股票，用所得资金买入新股票"""
        strategy_name = self.GetUniqueStrategyName(self.Stocks[0])
        prices = self.GetCurrentPrice([old_stock, new_stock], C)
        price_old = prices[old_stock]
        self.Sell(C, old_stock, current_holding, price_old, strategy_name)
        self.logical_holding = 0
        print(f"平仓 {current_holding} 股 {old_stock} @ {price_old:.3f}")

        cash_from_sale = current_holding * price_old

        price_new = prices[new_stock]

        unit_to_buy = int(cash_from_sale / price_new)
        unit_to_buy = (unit_to_buy // 100) * 100  # A股100股整数倍

        if unit_to_buy == 0:
            print(f"换仓金额不足100股，跳过")
            return

        # 检查可用资金
        available_cash = self.GetAvailableCash()

        if self.ExecuteBuy(C, new_stock, price_new, available_cash, trading_amount = cash_from_sale):
            self.SaveStrategyState(self.Stocks, self.StockNames, self.current_held, self.base_price, self.logical_holding)


    def RunGridTrading(self, C, stock):
        prices = self.prices[stock]
        current_price = prices['close'][-1]
        high = prices['high'].values
        low = prices['low'].values
        close = prices['close'].values

        rsi = talib.RSI(close, timeperiod=6)[-1]
        atr = talib.ATR(high, low, close, timeperiod=4)[-1]
        grid_unit = atr

        if not self.IsBacktest:
            current_prices = self.GetCurrentPrice([stock], C)
            self.current_price = current_prices[stock]
        else:
            self.current_price = current_price


        base_price = self.base_price
        if base_price is None:
            base_price = prices['close'][-10:].max()

        print({
            'stock': stock,
            'yesterday': prices['close'].index[-1],
            'yesterday_price': current_price,
            'current_price': current_price,
            'base_price': base_price,
            'atr': atr,
        })

        available_cash = self.GetAvailableCash()
        holdings = self.GetPositions()
        current_holding = holdings.get(stock, 0)

        executed = False
        if self.current_price >= base_price + grid_unit:
            executed = self.ExecuteSell(C, stock, self.current_price, current_holding)
        # Price drops below grid: buy one unit (based on amount)
        elif self.current_price <= base_price - grid_unit:
            executed = self.ExecuteBuy(C, stock, self.current_price, available_cash)

        if executed:
            self.SaveStrategyState(self.Stocks, self.StockNames, stock, self.base_price, self.logical_holding)

            if self.base_price is not None:
                print(f"State saved: base_price={self.base_price:.3f}, position={self.logical_holding}")
            else:
                print(f"State saved: base_price=None, position={self.logical_holding}")
        elif self.IsBacktest:
            self.g(C)

    def f(self, C):
        if not self.IsBacktest and not self.IsTradingTime():
            return

        yesterday = self.GetYesterday(C)
        available_cash = self.GetAvailableCash()

        if not self.CheckWaitingList():
            return

        # Get position
        holdings = self.GetPositions()

        current_holding = holdings.get(self.current_held, 0)

        # === Core logic ===
        executed = False

        # Get current market price
        self.UpdateMarketData(C, self.Stocks)

        if len(self.prices) < 2:
            print("数据不足，跳过")
            return

        price_A = self.prices[self.stock_A]['close'][-1]
        price_B = self.prices[self.stock_B]['close'][-1]

            # --- 1. 配对逻辑：选择被低估的资产（便宜的那个）---
        close_A = np.array(self.prices[self.stock_A]['close'][-20:])
        close_B = np.array(self.prices[self.stock_B]['close'][-20:])
        ratio_series = close_A / close_B
        mean_ratio = np.mean(ratio_series)

        current_ratio = price_A / price_B

        # print(f"配对分析: A/B={current_ratio:.4f}, 历史均值={mean_ratio:.4f}, 阈值=[{mean_ratio*(1-self.threshold_ratio):.4f}, {mean_ratio*(1+self.threshold_ratio):.4f}]")

        target_stock = None
        if current_ratio > mean_ratio * (1 + self.threshold_ratio):
            # A/B 太高 → A 贵，B 便宜 → 押注 B 回归 → 持有 B
            target_stock = self.stock_B
            print('切换至 B（B 被低估）')
        elif current_ratio < mean_ratio * (1 - self.threshold_ratio):
            # A/B 太低 → A 便宜，B 贵 → 押注 A 回归 → 持有 A
            target_stock = self.stock_A
            print('切换至 A（A 被低估）')
        else:
            target_stock = self.current_held  # 维持现状

        # 默认持有A（首次启动）
        if target_stock is None:
            target_stock = self.stock_A

        # --- 2. 换仓逻辑：等值转移 ---
        if self.current_held and self.current_held != target_stock:
            print(f"执行换仓: {self.current_held} → {target_stock}")
            self.SwitchPosition(C, self.current_held, current_holding, target_stock)
        elif self.current_held:
            self.RunGridTrading(C, self.current_held)
        else:
            self.RunGridTrading(C, self.stock_A)

        return

    def ExecuteBuy(self, C, stock, current_price, available_cash, trading_amount = None):
        if trading_amount is None:
            buy_amount = self.TradingAmount
        else:
            buy_amount = trading_amount

        unit_to_buy = int(buy_amount / current_price)
        unit_to_buy = (unit_to_buy // 100) * 100  # 取整到100的倍数

        if available_cash >= current_price * unit_to_buy and unit_to_buy > 0 and current_price * (unit_to_buy + self.logical_holding) <= self.MaxAmount:
            strategy_name = self.GetUniqueStrategyName(self.Stocks[0])
            self.Buy(C, stock, unit_to_buy, current_price, strategy_name)
            self.current_held = stock
            self.logical_holding += unit_to_buy
            self.base_price = current_price
            print(f"Updated base price to: {self.base_price:.3f}")
            return True
        else:
            print("Insufficient cash or calculated shares is zero, cannot buy")
            return False

    def ExecuteSell(self, C, stock, current_price, current_holding):
        sell_amount = self.TradingAmount

        unit_to_sell = int(sell_amount / current_price)
        unit_to_sell = (unit_to_sell // 100) * 100
        unit_to_sell = min(unit_to_sell, current_holding)

        if unit_to_sell > 0:    # Ensure at least 100 shares
            strategy_name = self.GetUniqueStrategyName(self.Stocks[0])
            self.Sell(C, stock, unit_to_sell, current_price, strategy_name)
            self.logical_holding -= unit_to_sell
            if self.logical_holding > 0:
                self.base_price = current_price
                self.sell_index += 1
                self.buy_index = 0
            else:
                self.base_price = None
                self.sell_index = 0
                self.buy_index = 0
            print(f"Updated base price to: {self.base_price if self.base_price is not None else 'None'}")
            return True

        return False

    def g(self, C):
        self.LoadStrategyState(self.Stocks, self.StockNames)
        state = self.State

        if not self.IsBacktest and state and state['base_price'] is not None:
            self.current_held = state['current_held']
            self.base_price = state['base_price']
            self.logical_holding = state['logical_holding']

        stock = self.Stocks[0]

        if self.logical_holding > 0 and self.base_price is not None and abs(self.base_price / self.current_price - 1) > 0.06:
            original_base_price = self.base_price
            beta = 0.1  # Tracking speed: 0.1~0.3 (larger = faster)
            self.base_price = self.base_price + beta * (self.current_price - self.base_price)

            self.SaveStrategyState(self.Stocks, self.StockNames, self.current_held, self.base_price, self.logical_holding)
            print(f"Dynamic adjustment of base_price: original={original_base_price:.3f}, new={self.base_price:.3f}, current price={self.current_price:.3f}")

    def LoadStrategyState(self, stocks, stockNames):
        """Load strategy state from file"""

        if self.IsBacktest:
            self.State = None
            return

        stock = stocks[0]
        stockName = stockNames[0]
        file = self.GetStateFileName(stock, stockName)

        if not os.path.exists(file):
            self.State = None
            return
        try:
            with open(file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                # Check if state for current stock exists
                self.State = {
                    'current_held': state.get('current_held'),
                    'base_price': state.get('base_price'),
                    'logical_holding': state.get('logical_holding', 0),
                }
        except Exception as e:
            print(f"Failed to load strategy state: {e}")


    def SaveStrategyState(self, stocks, stockNames, currentHeld, basePrice, logicalHolding):
        """Load strategy state from file"""

        if self.IsBacktest:
            return

        stock = stocks[0]
        stockName = stockNames[0]
        file = self.GetStateFileName(stock, stockName)

        if os.path.exists(file):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                print(f"Error reading state file, will create new: {e}")

        # Update state for current stock
        data = {
            'current_held': currentHeld,
            'base_price': basePrice,
            'logical_holding': logicalHolding,
        }

        try:
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Failed to save strategy state: {e}")


