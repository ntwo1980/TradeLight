import datetime
import time
import pandas as pd
import numpy as np
import talib
import json
import os

class PairLevelGridStrategy(BaseStrategy):
    def __init__(self, **kwargs):
        super().__init__(strategyPrefix='pairlevelgrid', strategyId='a', **kwargs)

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

        self.window = 20
        self.current_held = None
        self.last_ratio_mean = None

        C.set_universe(self.Stocks)

        self.LoadStrategyState(self.Stocks, self.StockNames)

        state = self.State
        if state and state['base_price'] is not None:
            self.current_held = state['current_held']
            self.last_ratio_mean = state['last_ratio_mean']
            self.base_price = state['base_price']
            self.logical_holding = state['logical_holding']
            self.buy_index = state['buy_index']
            self.sell_index = state['sell_index']
            print(f"Loaded state from file: base_price={self.base_price}, position={self.logical_holding}, buy_index={self.buy_index}, sell_index={self.sell_index}")
        elif self.IsBacktest:
            print("No historical state found, will initialize base_price using first average")

    def UpdateMarketData(self, C, stocks):
        yesterday = self.GetYesterday(C)
        if self.prices_date is None or self.prices_date != yesterday:
            prices = self.GetHistoricalPrices(C, self.Stocks, fields=['high', 'low', 'close'], period='1d', count=30)
            self.prices_date = yesterday
            self.prices = prices[stock]
            prices = self.prices
            self.yesterday_price = prices['close'][-1]
            self.current_price = self.yesterday_price
            self.max_price = prices['close'][-10:].max()

            self.atr = talib.ATR(prices['high'].values, prices['low'].values, prices['close'].values, timeperiod=4)[-1]

    def f(self, C):
        if not self.IsBacktest and not self.IsTradingTime():
            return

        yesterday = self.GetYesterday(C)
        available_cash = self.GetAvailableCash()

        if not self.CheckWaitingList():
            return

        stock_A = self.Stocks[0]
        stock_B = self.Stocks[1]
        prices = self.GetHistoricalPrices(C, self.Stocks, fields=['close'], period='1d', count=self.window)

        price_A = prices[stock_A]['close'][-1]
        price_B = prices[stock_B]['close'][-1]

        # --- 1. 配对逻辑：直接使用比值偏离 ---
        close_A = np.array(prices[stock_A]['close'])
        close_B = np.array(prices[stock_B]['close'])

        ratio_series = close_A / close_B
        mean_ratio = np.mean(ratio_series)
        current_ratio = price_A / price_B

        print(f"配对分析: A/B={current_ratio:.4f}, 历史均值={mean_ratio:.4f}, 阈值=[{mean_ratio*(1-THRESHOLD_RATIO):.4f}, {mean_ratio*(1+THRESHOLD_RATIO):.4f}]")

        target_stock = None
        if current_ratio > mean_ratio * (1 + THRESHOLD_RATIO):
            print('switch to A')
            target_stock = stock_A  # A相对贵，持有A
        elif current_ratio < mean_ratio * (1 - THRESHOLD_RATIO):
            target_stock = stock_B  # B相对贵，持有B
            print('switch to B')
        else:
            target_stock = self.current_held  # 维持现状

        # 默认持有A
        if target_stock is None:
            target_stock = stock_A

        # --- 2. 换仓逻辑 + 基准价继承 ---
        if self.current_held and self.current_held != target_stock:
            print(f"切换持仓: {self.current_held} → {target_stock}")

            old_stock = self.current_held
            new_stock = target_stock
            old_base = self.base_price
            price_old = prices[old_stock]['close'][-1]
            price_new = prices[new_stock]['close'][-1]

            # 平仓
            _close_position(C, old_stock, bar_date)
            C.current_held = None

            # === 继承新持仓的 base_price（价值等价）===
            if old_base is not None:
                if new_stock == C.stock_A:
                    conversion_ratio = mean_ratio  # A/B 均值
                else:
                    conversion_ratio = 1.0 / mean_ratio  # B/A

                new_base_price = old_base * conversion_ratio * (price_new / price_old)
                C.grid_state[new_stock]['base_price'] = new_base_price
                C.grid_state[new_stock]['buy_index'] = 0
                C.grid_state[new_stock]['sell_index'] = 0
                print(f"继承基准价: {old_stock}@{old_base:.4f} → {new_stock}@{new_base_price:.4f} "
                    f"(转换比率={conversion_ratio:.4f})")
            else:
                # 初始化新 base_price
                C.grid_state[new_stock]['base_price'] = price_new * 1.05
                C.grid_state[new_stock]['buy_index'] = 0
                C.grid_state[new_stock]['sell_index'] = 0

            C.last_ratio_mean = mean_ratio

        # 设置新持仓
        if C.current_held != target_stock:
            C.current_held = target_stock
            print(f"新持仓目标: {C.current_held}")
            save_strategy_state(C)

        # --- 3. 多级网格交易 ---
        if C.current_held:
            _run_grid_trading(C, C.current_held, bar_date)

        # Get position
        holdings = self.GetPositions()

        current_holding = holdings.get(self.Stocks[0], 0)





        # === Core logic ===
        executed = False

        # Get current market price
        self.UpdateMarketData(C, self.Stocks)

        if self.max_price == 0:
            print("max_price is 0")
            return

        if not self.IsBacktest:
            current_prices = self.GetCurrentPrice(self.Stocks, C)
            self.current_price = current_prices[self.Stocks[0]]

        base_price = self.base_price  # copy a local base_price

        if base_price is None:
            base_price = self.max_price

        print({
            'stock': self.Stocks[0],
            'stock_name': self.StockNames[0],
            'yesterday': self.prices['close'].index[-1],
            'yesterday_price': self.yesterday_price,
            'current_price': self.current_price,
            'base_price': base_price,
            'atr': self.atr,
            'buy_index': self.buy_index,
            'sell_index': self.sell_index
        })

        if self.sell_index < len(self.levels):
            sell_threshold = base_price + self.levels[self.sell_index] * self.atr
            if current_price >= sell_threshold:
                executed = self.ExecuteSell(C, self.Stocks[0], self.current_price, current_holding)

        if self.buy_index < len(self.levels):
            buy_threshold = base_price - self.levels[self.buy_index] * self.atr
            if current_price <= buy_threshold:
                executed = self.ExecuteBuy(C, self.Stocks[0], self.current_price, available_cash)

        if executed:
            self.SaveStrategyState(self.Stocks, self.StockNames, self.base_price, self.logical_holding, self.buy_index, self.sell_index)

            if self.base_price is not None:
                print(f"State saved: base_price={self.base_price:.3f}, position={self.logical_holding}, buy_index={self.buy_index}, sell_index={self.sell_index}")
            else:
                print(f"State saved: base_price=None, position={self.logical_holding}, buy_index={self.buy_index}, sell_index={self.sell_index}")
        elif self.IsBacktest:
            g(C)

    def ExecuteBuy(self, C, stock, current_price, available_cash):
        buy_amount = self.TradingAmount

        unit_to_buy = int(buy_amount / current_price)
        unit_to_buy = (unit_to_buy // 100) * 100  # 取整到100的倍数

        if available_cash >= current_price * unit_to_buy and unit_to_buy > 0:
            strategy_name = self.GetUniqueStrategyName(stock)
            self.Buy(C, stock, unit_to_buy, current_price, strategy_name)
            self.logical_holding += unit_to_buy
            self.base_price = current_price
            self.buy_index += 1
            self.sell_index = 0
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
            strategy_name = self.GetUniqueStrategyName(stock)
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

    def ClosePostition(self, C, stock, current_price, current_holding):
        unit_to_sell = current_holding

        if unit_to_sell > 0:    # Ensure at least 100 shares
            strategy_name = self.GetUniqueStrategyName(stock)
            self.Sell(C, stock, unit_to_sell, current_price, strategy_name)
            self.current_held = None
            self.last_ratio_mean = None
            self.base_price = None
            self.sell_index = 0
            self.buy_index = 0
            print(f"Close position: {stock}")

            return True

        return False

    def g(self, C):
        self.LoadStrategyState(self.Stocks, self.StockNames)
        state = self.State

        if not self.IsBacktest and state and state['base_price'] is not None:
            self.current_held = state['current_held']
            self.last_ratio_mean = state['last_ratio_mean']
            self.base_price = state['base_price']
            self.logical_holding = state['logical_holding']
            self.buy_index = state['buy_index']
            self.sell_index = state['sell_index']

        stock = self.Stocks[0]

        if self.logical_holding > 0 and self.base_price is not None and abs(self.base_price / self.current_price - 1) > 0.04:
            original_base_price = self.base_price
            beta = 0.1  # Tracking speed: 0.1~0.3 (larger = faster)
            self.base_price = self.base_price + beta * (self.current_price - self.base_price)

            self.SaveStrategyState(self.Stocks, self.StockNames, self.base_price, self.logical_holding, self.buy_index, self.sell_index)
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
                data = json.load(f)
                # Check if state for current stock exists
                if stock in data:
                    state = data[stock]

                    self.State = {
                        'current_held': state.get('current_held'),
                        'last_ratio_mean': state.get('last_ratio_mean'),
                        'base_price': state.get('base_price'),
                        'logical_holding': state.get('logical_holding', 0)
                        'buy_index': state.get('buy_index', 0),
                        'sell_index': state.get('sell_index', 0)
                    }
        except Exception as e:
            print(f"Failed to load strategy state: {e}")


    def SaveStrategyState(self, stocks, stockNames, current_held, last_ratio_mean, basePrice, logicalHolding, buy_index, sell_index):
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

        data = {}

        # Update state for current stock
        data[stock] = {
            'current_held': current_held,
            'last_ratio_mean': last_ratio_mean,
            'base_price': base_price,
            'logical_holding': logical_holding
            'buy_index': buy_index,
            'sell_index': sell_index
        }

        try:
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Failed to save strategy state: {e}")


