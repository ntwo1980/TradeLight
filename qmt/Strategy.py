import datetime
import time
import pandas as pd
import numpy as np
import talib
import json
import os
import math

class BaseStrategy():
    def __init__(self, stocks, stockNames, strategyPrefix, strategyId,  get_trade_detail_data_func, pass_order_func, timetag_to_datetime_func, TradingAmount = 30000, MaxAmount = None):
        self.Stocks = stocks
        self.StockNames = stockNames
        self.StrategyPrefix = strategyPrefix
        self.StrategyId = strategyId
        self.IsBacktest = True
        self.Account = "testS"
        self.AccountType = "STOCK"
        self.TradingAmount = TradingAmount
        if MaxAmount is None:
            self.MaxAmount = self.TradingAmount * 3.5
        else:
            self.MaxAmount = MaxAmount
        self.WaitingList = []
        self.GetTradeDetailData = get_trade_detail_data_func
        self.PassOrder = pass_order_func
        self.TimetagToDatetime = timetag_to_datetime_func
        self.State = None
        self.PriceDate = None
        self.Prices = None

    def init(self, C):
        self.IsBacktest = C.do_back_test

        self.RebuildWaitingListFromOpenOrders()

    def GetUniqueStrategyName(self, stock):
        return f"{self.StrategyPrefix}_{stock.replace('.', '')}_{self.StrategyId}"

    def GetStateFileName(self, stock, stockName):
        name = self.GetUniqueStrategyName(stock)
        return f"{name}_{stockName}.json"

    def SetAccount(self, account, accountType):
        self.Account = account
        self.AccountType = accountType

    def IsTradingTime(self):
        now = datetime.datetime.now()
        now_time = now.strftime('%H%M%S')

        return '093000' <= now_time <= '113000' or '130000' <= now_time <= '150000'

    def GetAvailableCash(self):
        account = self.GetTradeDetailData(self.Account, self.AccountType, 'account')
        if len(account) == 0:
            print(f'Account {self.Account} is not logged in, please check')
            return 0

        account = account[0]
        return int(account.m_dAvailable)


    def GetPositions(self):
        positions = self.GetTradeDetailData(self.Account, self.AccountType, 'position')
        holdings = {}
        for pos in positions:
            key = pos.m_strInstrumentID + '.' + pos.m_strExchangeID
            holdings[key] = pos.m_nCanUseVolume  # Available quantity for selling

        return holdings

    def RebuildWaitingListFromOpenOrders(self):
        if self.IsBacktest:
            return []

        self.WaitingList = []
        orders = self.GetTradeDetailData(self.Account, self.AccountType, 'order')
        strategyName = self.GetUniqueStrategyName(self.Stocks[0])
        for order in orders:
            if order.m_nOrderStatus in [49, 50, 51, 52, 55] and strategyName in order.m_strRemark:  # 待报, 已报, 已报待撤, 部成待撤, 部成
                self.WaitingList.append(order.m_strRemark)

    def CheckWaitingList(self):
        if not self.IsBacktest:
            self.RefreshWaitingList()
            if self.WaitingList:
                print(f"There are pending orders not confirmed: {self.WaitingList},暂停后续报单")
                return False

        return True

    def GetTicketPrices(self, stocks, C):
        prices = C.get_full_tick(stocks)

        for stock in stocks:
            if stock not in prices:
                print(f"Failed to get real-time price for {stock}")

        return prices

    def GetYesterday(self, C):
        if self.IsBacktest:
            yesterday = self.TimetagToDatetime(C.get_bar_timetag(C.barpos - 1), '%Y%m%d')
        else:
            now = datetime.datetime.now()
            yesterday = (now - datetime.timedelta(days=1)).strftime('%Y%m%d')

        return yesterday

    def GetHistoricalPrices(self, C, stocks, fields=['high', 'low', 'close'], period='1d', count=30):
        yesterday = self.GetYesterday(C)

        prices = C.get_market_data_ex(fields, stocks, period=period, count=count, end_time=yesterday)

        for stock in stocks:
            if stock not in prices:
                print(f"Failed to get historical prices for {stock}")
                return None

        return prices

    def GetCurrentPrice(self, stocks, C):
        prices_dict = {}

        if self.IsBacktest:
            prices = self.GetHistoricalPrices(C, stocks=stocks, fields=['close'], period='1d', count=1)

            for stock in stocks:
                prices_dict[stock] = prices[stock]['close'][-1]
        else:
            prices = self.GetTicketPrices(stocks, C)
            for stock in stocks:
                prices_dict[stock] = prices[stock]['lastPrice']

        return prices_dict

    def RefreshWaitingList(self):
        if self.WaitingList:
            foundList = []
            orders = self.GetTradeDetailData(self.Account, self.AccountType, 'order')
            for order in orders:
                if order.m_strRemark in self.WaitingList:
                    if order.m_nOrderStatus in {54, 56, 57}:  # 已撤, 已成, 废单
                        foundList.append(order.m_strRemark)

            self.WaitingList = [i for i in self.WaitingList if i not in foundList]

    def Buy(self, C, stock, quantity, price, strategy_name, order_type=2):
        timestamp = int(time.time())
        msg = f"{strategy_name}_buy_{quantity}_{timestamp}"
        self.PassOrder(23, 1101, self.Account, stock, 14, -1, quantity, strategy_name, order_type, msg, C)
        self.WaitingList.append(msg)

        if price > 0:
            print(f"Buy {quantity} shares, price: {price:.3f}, total amount: {quantity * price:.2f}")
        else:
            print(f"Buy {quantity} shares")
        return msg

    def Sell(self, C, stock, quantity, price, strategy_name, order_type=2):
        timestamp = int(time.time())
        msg = f"{strategy_name}_sell_{quantity}_{timestamp}"
        self.PassOrder(24, 1101, self.Account, stock, 14, -1, quantity, strategy_name, order_type, msg, C)
        self.WaitingList.append(msg)
        if price > 0:
            print(f"Sell {quantity} shares, price: {price:.3f}, total amount: {quantity * price:.2f}")
        else:
            print(f"Sell {quantity} shares")
        return msg

class SimpleGridStrategy(BaseStrategy):
    def __init__(self, **kwargs):
        super().__init__(strategyPrefix='grid', strategyId='a', **kwargs)

    def init(self, C):
        super().init(C)

        self.prices = None
        self.prices_date = None
        self.base_price = None
        self.logical_holding = 0
        self.atr = 0
        self.rsi = 50
        self.grid_unit = 0
        self.max_price = 0
        self.yesterday_price = 0

        C.set_universe(self.Stocks)

        self.LoadStrategyState(self.Stocks, self.StockNames)

        state = self.State
        if state and state['base_price'] is not None:
            self.base_price = state['base_price']
            self.logical_holding = state['logical_holding']
            print(f"Loaded state from file: base_price={self.base_price}, position={self.logical_holding}")
        elif self.IsBacktest:
            print("No historical state found, will initialize base_price using first average")
        '''
        else:
            self.SaveStrategyState(self.Stocks, self.StockNames, 0, 0)
        '''

    def UpdateMarketData(self, C, stocks):
        yesterday = self.GetYesterday(C)
        if self.prices_date is None or self.prices_date != yesterday:
            stock = stocks[0]
            prices = self.GetHistoricalPrices(C, self.Stocks, fields=['high', 'low', 'close'], period='1d', count=30)
            self.prices_date = yesterday
            self.prices = prices[stock]
            prices = self.prices
            self.yesterday_price = prices['close'][-1]
            self.current_price = self.yesterday_price
            self.max_price = prices['close'][-10:].max()

            self.rsi = talib.RSI(prices['close'], timeperiod=6)[-1]
            self.atr = talib.ATR(prices['high'].values, prices['low'].values, prices['close'].values, timeperiod=4)[-1]
            self.grid_unit = self.GetGridUnit(stock, self.yesterday_price, self.atr)

    def f(self, C):
        if not self.IsBacktest and not self.IsTradingTime():
            return

        yesterday = self.GetYesterday(C)
        available_cash = self.GetAvailableCash()

        if not self.CheckWaitingList():
            return

        # Get position
        holdings = self.GetPositions()

        current_holding = holdings.get(self.Stocks[0], 0)

        # === Core logic ===
        executed = False

        # Get current market price
        self.UpdateMarketData(C, self.Stocks)

        if self.grid_unit == 0 or self.max_price == 0:
            print("grid_unit or self.max_price is 0")
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
            'rsi': self.rsi,
            'atr': self.atr,
            'grid_unit': self.grid_unit})


        if self.current_price >= base_price + self.grid_unit:
            executed = self.ExecuteSell(C, self.Stocks[0], self.current_price, current_holding)
        # Price drops below grid: buy one unit (based on amount)
        elif self.current_price <= base_price - self.grid_unit:
            executed = self.ExecuteBuy(C, self.Stocks[0], self.current_price, available_cash)

        if executed:
            self.SaveStrategyState(self.Stocks, self.StockNames, self.base_price, self.logical_holding)

            if self.base_price is not None:
                print(f"State saved: base_price={self.base_price:.3f}, position={self.logical_holding}")
            else:
                print(f"State saved: base_price=None, position={self.logical_holding}")
        elif self.IsBacktest:
            self.g(C)

    def ExecuteBuy(self, C, stock, current_price, available_cash):
        buy_amount = self.TradingAmount

        unit_to_buy = int(buy_amount / current_price)
        unit_to_buy = (unit_to_buy // 100) * 100  # 取整到100的倍数

        if available_cash >= current_price * unit_to_buy and unit_to_buy > 0 and current_price * (unit_to_buy + self.logical_holding) <= self.MaxAmount:
            strategy_name = self.GetUniqueStrategyName(stock)
            self.Buy(C, stock, unit_to_buy, current_price, strategy_name)
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
            strategy_name = self.GetUniqueStrategyName(stock)
            self.Sell(C, stock, unit_to_sell, current_price, strategy_name)
            self.logical_holding -= unit_to_sell
            if self.logical_holding > 0:
                self.base_price = current_price
            else:
                self.base_price = None
            print(f"Updated base price to: {self.base_price if self.base_price is not None else 'None'}")
            return True
        return False

    def g(self, C):
        self.LoadStrategyState(self.Stocks, self.StockNames)
        state = self.State

        if not self.IsBacktest and state and state['base_price'] is not None:
            self.base_price = state['base_price']
            self.logical_holding = state['logical_holding']

        stock = self.Stocks[0]

        if self.logical_holding > 0 and self.base_price is not None and abs(self.base_price - self.current_price) > self.atr * 4:
            original_base_price = self.base_price
            beta = 0.1  # Tracking speed: 0.1~0.3 (larger = faster)
            self.base_price = self.base_price + beta * (self.current_price - self.base_price)

            self.SaveStrategyState(self.Stocks, self.StockNames, self.base_price, self.logical_holding)
            print(f"Dynamic adjustment of base_price: original={original_base_price:.3f}, new={self.base_price:.3f}, current price={self.current_price:.3f}")


    def GetGridUnit(self, stock, price, atr):
        if stock == "159985.SZ":
            return max(atr, price * 0.01)

        return atr

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
                    'base_price': state.get('base_price'),
                    'logical_holding': state.get('logical_holding', 0)
                }
        except Exception as e:
            print(f"Failed to load strategy state: {e}")


    def SaveStrategyState(self, stocks, stockNames, basePrice, logicalHolding):
        stock = stocks[0]
        stockName = stockNames[0]
        file = self.GetStateFileName(stock, stockName)

        data = {
            'base_price': basePrice,
            'logical_holding': logicalHolding
        }

        if self.IsBacktest:
            print(json.dumps(data, ensure_ascii=False, indent=4))
        else:
            try:
                with open(file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"Failed to save strategy state: {e}")

class LevelGridStrategy(BaseStrategy):
    def __init__(self, **kwargs):
        super().__init__(strategyPrefix='levelgrid', strategyId='a', **kwargs)

    def init(self, C):
        super().init(C)

        self.prices = None
        self.prices_date = None
        self.base_price = None
        self.logical_holding = 0
        self.levels = [1, 2, 4, 8, 12, 22]
        self.min_trade = 0.02
        self.buy_index = 0
        self.sell_index = 0
        self.atr = 0
        self.slope = 0
        self.sma10 = 0
        self.above_sma10_count = 0
        self.below_sma10_count = 0
        self.grid_unit = 0
        self.max_price = 0
        self.yesterday_price = 0

        C.set_universe(self.Stocks)

        self.LoadStrategyState(self.Stocks, self.StockNames)

        state = self.State
        if state and state['base_price'] is not None:
            self.base_price = state['base_price']
            self.logical_holding = state['logical_holding']
            self.buy_index = state['buy_index']
            self.sell_index = state['sell_index']
            print(f"Loaded state from file: base_price={self.base_price}, position={self.logical_holding}, buy_index={self.buy_index}, sell_index={self.sell_index}")
        elif self.IsBacktest:
            print("No historical state found, will initialize base_price using first average")
        else:
            self.SaveStrategyState(self.Stocks, self.StockNames, None, 0, 0, 0)

    def UpdateMarketData(self, C, stocks):
        yesterday = self.GetYesterday(C)
        if self.prices_date is None or self.prices_date != yesterday:
            stock = stocks[0]
            prices = self.GetHistoricalPrices(C, self.Stocks, fields=['high', 'low', 'close'], period='1d', count=30)
            self.prices_date = yesterday
            self.prices = prices[stock]
            prices = self.prices
            self.yesterday_price = prices['close'][-1]
            self.current_price = self.yesterday_price
            self.max_price = prices['close'][-10:].max()

            self.atr = talib.ATR(prices['high'].values, prices['low'].values, prices['close'].values, timeperiod=4)[-1]
            x = np.arange(len(prices['close'].values))
            log_prices = np.log(np.array(prices['close'].values))
            self.slope, _ = np.polyfit(x, log_prices, 1)

            self.sma10 = talib.SMA(prices['close'].values, timeperiod=10)[-1]
            close_prices = prices['close'].values[-10:]
            sma10_series = talib.MA(prices['close'].values, timeperiod=10)[-10:]
            self.above_sma10_count = sum(1 for c, s in zip(close_prices, sma10_series) if c > s)
            self.below_sma10_count = sum(1 for c, s in zip(close_prices, sma10_series) if c < s)

    def f(self, C):
        if not self.IsBacktest and not self.IsTradingTime():
            return

        yesterday = self.GetYesterday(C)
        available_cash = self.GetAvailableCash()

        if not self.CheckWaitingList():
            return

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

        '''
        if base_price is not None and not np.isnan(self.sma10):
            if (self.above_sma10_count >= 7 and self.slope > 0 and self.current_price > base_price) or \
               (self.below_sma10_count >= 7 and self.slope < 0 and self.current_price < base_price):
                print(f"Detected strong trend: above_sma10_count={self.above_sma10_count}, "
                      f"below_sma10_count={self.below_sma10_count}, sma10={self.sma10:.2f}, "
                      f"slope={self.slope:.4f}, current_price={self.current_price:.2f}, "
                      f"base_price={base_price:.2f}. Skipping trade.")
                return
        '''

        print({
            'stock': self.Stocks[0],
            'stock_name': self.StockNames[0],
            'yesterday': self.prices['close'].index[-1],
            'yesterday_price': self.yesterday_price,
            'current_price': self.current_price,
            'base_price': base_price,
            'atr': self.atr,
            'slope': self.slope,
            'sma10': self.sma10,
            'above_sma10_count': self.above_sma10_count,
            'below_sma10_count': self.below_sma10_count,
            'buy_index': self.buy_index,
            'sell_index': self.sell_index
        })

        min_trade = base_price * self.min_trade
        if self.sell_index < len(self.levels):
            # diff = self.levels[self.sell_index] * self.atr * 0.8
            diff = self.current_price * self.levels[self.sell_index] / 100
            if diff < min_trade:
                diff = min_trade

            sell_threshold = base_price + diff
            if self.current_price >= sell_threshold:
                executed = self.ExecuteSell(C, self.Stocks[0], self.current_price, current_holding)

        if self.buy_index < len(self.levels) and self.slope > 0:
            # diff = self.levels[self.buy_index] * self.atr  * 0.8
            diff = self.current_price * self.levels[self.buy_index] / 100
            if diff < min_trade:
                diff = min_trade

            buy_threshold = base_price - diff
            if self.current_price <= buy_threshold:
                executed = self.ExecuteBuy(C, self.Stocks[0], self.current_price, available_cash)

        if executed:
            self.SaveStrategyState(self.Stocks, self.StockNames, self.base_price, self.logical_holding, self.buy_index, self.sell_index)

            if self.base_price is not None:
                print(f"State saved: base_price={self.base_price:.3f}, position={self.logical_holding}, buy_index={self.buy_index}, sell_index={self.sell_index}")
            else:
                print(f"State saved: base_price=None, position={self.logical_holding}, buy_index={self.buy_index}, sell_index={self.sell_index}")
        elif self.IsBacktest:
            self.g(C)

    def ExecuteBuy(self, C, stock, current_price, available_cash):
        buy_amount = self.TradingAmount

        unit_to_buy = int(buy_amount / current_price)
        unit_to_buy = (unit_to_buy // 100) * 100  # 取整到100的倍数

        if available_cash >= current_price * unit_to_buy and unit_to_buy > 0 and current_price * (unit_to_buy + self.logical_holding) <= self.MaxAmount:
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

    def g(self, C):
        self.LoadStrategyState(self.Stocks, self.StockNames)
        state = self.State

        if not self.IsBacktest and state and state['base_price'] is not None:
            self.base_price = state['base_price']
            self.logical_holding = state['logical_holding']
            self.buy_index = state['buy_index']
            self.sell_index = state['sell_index']

        stock = self.Stocks[0]

        if self.logical_holding > 0 and self.base_price is not None and abs(self.base_price - self.current_price) > self.atr * 4:
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
                state = json.load(f)
                # Check if state for current stock exists

                self.State = {
                    'base_price': state.get('base_price'),
                    'logical_holding': state.get('logical_holding', 0),
                    'buy_index': state.get('buy_index', 0),
                    'sell_index': state.get('sell_index', 0)
                }
        except Exception as e:
            print(f"Failed to load strategy state: {e}")


    def SaveStrategyState(self, stocks, stockNames, basePrice, logicalHolding, buyIndex, sellIndex):
        stock = stocks[0]
        stockName = stockNames[0]
        file = self.GetStateFileName(stock, stockName)

        data = {
            'base_price': basePrice,
            'logical_holding': logicalHolding,
            'buy_index': buyIndex,
            'sell_index': sellIndex
        }

        if self.IsBacktest:
            print(json.dumps(data, ensure_ascii=False, indent=4))
        else:
            try:
                with open(file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"Failed to save strategy state: {e}")

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
        else:
            self.SaveStrategyState(self.Stocks, self.StockNames, None, 0, 0)

    def UpdateMarketData(self, C, stocks):
        yesterday = self.GetYesterday(C)
        if self.prices_date is None or self.prices_date != yesterday:
            self.prices = self.GetHistoricalPrices(C, self.Stocks, fields=['high', 'low', 'close'], period='1d', count=30)
            self.prices_date = yesterday

    def SwitchPosition(self, C, old_stock, current_holding, new_stock, current_prices, new_base_price):
        print(f'SwitchPosition holding is {current_holding}')

        """执行等值换仓：平掉旧股票，用所得资金买入新股票"""
        strategy_name = self.GetUniqueStrategyName(self.Stocks[0])
        price_old = current_prices[old_stock]
        self.Sell(C, old_stock, current_holding, price_old, strategy_name)
        self.logical_holding = 0
        print(f"平仓 {current_holding} 股 {old_stock} @ {price_old:.3f}")

        cash_from_sale = current_holding * price_old

        price_new = current_prices[new_stock]

        unit_to_buy = int(cash_from_sale / price_new)
        unit_to_buy = (unit_to_buy // 100) * 100  # A股100股整数倍

        if unit_to_buy == 0:
            print(f"换仓金额不足100股，跳过")
            return

        # 检查可用资金
        available_cash = self.GetAvailableCash()

        if self.ExecuteBuy(C, new_stock, price_new, available_cash, trading_amount = cash_from_sale):
            self.base_price = new_base_price
            self.SaveStrategyState(self.Stocks, self.StockNames, self.current_held, self.base_price, self.logical_holding)

    def RunGridTrading(self, C, stock):
        prices = self.prices[stock]
        current_price = prices['close'][-1]
        high = prices['high'].values
        low = prices['low'].values
        close = prices['close'].values

        rsi = talib.RSI(close, timeperiod=6)[-1]
        self.atr = talib.ATR(high, low, close, timeperiod=4)[-1]
        grid_unit = self.atr

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
            'current_price': self.current_price,
            'base_price': base_price,
            'rsi': rsi,
            'atr': self.atr,
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

        current_prices = self.GetCurrentPrice(self.Stocks, C)
        price_A =  current_prices[self.stock_A]
        price_B =  current_prices[self.stock_B]

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

            current_prices = self.GetCurrentPrice([self.current_held, target_stock], C)

            old_stock = self.current_held
            new_stock = target_stock
            price_old = current_prices[old_stock]
            price_new = current_prices[target_stock]
            old_base_price = self.base_price

            new_base_price = old_base_price * price_new / price_old
            self.SwitchPosition(C, self.current_held, current_holding, target_stock, current_prices, new_base_price)

        elif self.current_held:
            self.RunGridTrading(C, self.current_held)
        else:
            old_holding = self.logical_holding
            self.RunGridTrading(C, self.stock_A)

            if old_holding <=0 and self.logical_holding <= 0:
                self.RunGridTrading(C, self.stock_B)

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
            else:
                self.current_held = None
                self.base_price = None
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

        if self.logical_holding > 0 and self.base_price is not None and abs(self.base_price - self.current_price) > self.atr * 4:
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
        stock = stocks[0]
        stockName = stockNames[0]
        file = self.GetStateFileName(stock, stockName)

        data = {
            'current_held': currentHeld,
            'base_price': basePrice,
            'logical_holding': logicalHolding,
        }

        if self.IsBacktest:
            print(json.dumps(data, ensure_ascii=False, indent=4))
        else:
            try:
                with open(file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"Failed to save strategy state: {e}")

class PairLevelGridStrategy(BaseStrategy):
    def __init__(self, strategyId='a', threshold_ratio = 0.01, **kwargs):
        super().__init__(strategyPrefix='pairlevelgrid', strategyId=strategyId, **kwargs)
        self.stock_A = self.Stocks[0]
        self.stock_B = self.Stocks[1]
        self.threshold_ratio = threshold_ratio

    def init(self, C):
        super().init(C)

        self.prices = None
        self.prices_date = None
        self.base_price = None
        self.logical_holding = 0
        self.levels = [1, 2, 4, 8, 12, 22]
        self.buy_index = 0
        self.sell_index = 0
        self.min_trade = 0.02
        self.max_price = 0
        self.yesterday_price = 0
        self.current_held = None

        C.set_universe(self.Stocks)

        self.LoadStrategyState(self.Stocks, self.StockNames)

        state = self.State
        if state and state['base_price'] is not None:
            self.current_held = state['current_held']
            self.base_price = state['base_price']
            self.logical_holding = state['logical_holding']
            self.buy_index = state['buy_index']
            self.sell_index = state['sell_index']
            print(f"Loaded state from file: base_price={self.base_price}, position={self.logical_holding}, current_held={self.current_held}, buy_index={self.buy_index}, sell_index={self.sell_index}")
        elif self.IsBacktest:
            print("No historical state found, will initialize base_price using first average")
        else:
            self.SaveStrategyState(self.Stocks, self.StockNames, None, 0, 0, 0, 0)

    def UpdateMarketData(self, C, stocks):
        yesterday = self.GetYesterday(C)
        if self.prices_date is None or self.prices_date != yesterday:
            self.prices = self.GetHistoricalPrices(C, self.Stocks, fields=['high', 'low', 'close'], period='1d', count=30)
            self.prices_date = yesterday

    def SwitchPosition(self, C, old_stock, current_holding, new_stock, current_prices, new_base_price):
        print(f'SwitchPosition holding is {current_holding}')

        """执行等值换仓：平掉旧股票，用所得资金买入新股票"""
        strategy_name = self.GetUniqueStrategyName(self.Stocks[0])
        price_old = current_prices[old_stock]
        self.Sell(C, old_stock, current_holding, price_old, strategy_name)
        self.logical_holding = 0
        print(f"平仓 {current_holding} 股 {old_stock} @ {price_old:.3f}")

        cash_from_sale = current_holding * price_old

        price_new = current_prices[new_stock]

        unit_to_buy = int(cash_from_sale / price_new)
        unit_to_buy = (unit_to_buy // 100) * 100  # A股100股整数倍

        if unit_to_buy == 0:
            print(f"换仓金额不足100股，跳过")
            return

        # 检查可用资金
        available_cash = self.GetAvailableCash()

        if self.ExecuteBuy(C, new_stock, price_new, available_cash, trading_amount = cash_from_sale, isSwitch = True):
            self.base_price = new_base_price
            self.SaveStrategyState(self.Stocks, self.StockNames, self.current_held, self.base_price, self.logical_holding, self.buy_index, self.sell_index)

    def RunGridTrading(self, C, stock):
        prices = self.prices[stock]
        current_price = prices['close'][-1]
        high = prices['high'].values
        low = prices['low'].values
        close = prices['close'].values

        rsi = talib.RSI(close, timeperiod=6)[-1]
        self.atr = talib.ATR(high, low, close, timeperiod=4)[-1]
        x = np.arange(len(prices['close'].values))
        log_prices = np.log(np.array(prices['close'].values))
        slope, _ = np.polyfit(x, log_prices, 1)

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
            'current_price': self.current_price,
            'base_price': base_price,
            'rsi': rsi,
            'atr': self.atr,
            'slope': slope
        })

        available_cash = self.GetAvailableCash()
        holdings = self.GetPositions()
        current_holding = holdings.get(stock, 0)

        executed = False

        min_trade = base_price * self.min_trade
        if self.sell_index < len(self.levels):
            diff = self.current_price * self.levels[self.sell_index] / 100
            # diff = self.levels[self.sell_index] * self.atr * 0.8
            if diff < min_trade:
                diff = min_trade

            sell_threshold = base_price + diff
            if self.current_price >= sell_threshold:
                executed = self.ExecuteSell(C, stock, self.current_price, current_holding)

        if self.buy_index < len(self.levels) and slope > 0:
            diff = self.current_price * self.levels[self.buy_index] / 100
            # diff = self.levels[self.buy_index] * self.atr * 0.8
            if diff < min_trade:
                diff = min_trade

            buy_threshold = base_price - diff
            if self.current_price <= buy_threshold:
                executed = self.ExecuteBuy(C, stock, self.current_price, available_cash)

        if executed:
            self.SaveStrategyState(self.Stocks, self.StockNames, stock, self.base_price, self.logical_holding, self.buy_index, self.sell_index)

            if self.base_price is not None:
                print(f"State saved: base_price={self.base_price:.3f}, position={self.logical_holding}, buy_index={self.buy_index}, sell_index={self.sell_index}")
            else:
                print(f"State saved: base_price=None, position={self.logical_holding}, buy_index={self.buy_index}, sell_index={self.sell_index}")
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

        current_prices = self.GetCurrentPrice(self.Stocks, C)
        price_A =  current_prices[self.stock_A]
        price_B =  current_prices[self.stock_B]

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

            old_stock = self.current_held
            new_stock = target_stock
            price_old = current_prices[old_stock]
            price_new = current_prices[target_stock]
            old_base_price = self.base_price

            new_base_price = old_base_price * price_new / price_old
            self.SwitchPosition(C, self.current_held, current_holding, target_stock, current_prices, new_base_price)
        elif self.current_held:
            self.RunGridTrading(C, self.current_held)
        else:
            old_holding = self.logical_holding
            self.RunGridTrading(C, self.stock_A)

            if old_holding <=0 and self.logical_holding <= 0:
                self.RunGridTrading(C, self.stock_B)

    def ExecuteBuy(self, C, stock, current_price, available_cash, trading_amount = None, isSwitch = False):
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
            if not isSwitch:
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
            strategy_name = self.GetUniqueStrategyName(self.Stocks[0])
            self.Sell(C, stock, unit_to_sell, current_price, strategy_name)
            self.logical_holding -= unit_to_sell
            if self.logical_holding > 0:
                self.base_price = current_price
                self.sell_index += 1
                self.buy_index = 0
            else:
                self.current_held = None
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
            self.buy_index = state['buy_index']
            self.sell_index = state['sell_index']

        stock = self.Stocks[0]

        if self.logical_holding > 0 and self.base_price is not None and abs(self.base_price - self.current_price) > self.atr * 4:
            original_base_price = self.base_price
            beta = 0.1  # Tracking speed: 0.1~0.3 (larger = faster)
            self.base_price = self.base_price + beta * (self.current_price - self.base_price)

            self.SaveStrategyState(self.Stocks, self.StockNames, self.current_held, self.base_price, self.logical_holding, self.buy_index, self.sell_index)
            print(f"Dynamic adjustment of base_price: original={original_base_price:.3f}, new={self.base_price:.3f}, current price={self.current_price:.3f}")

    def LoadStrategyState(self, stocks, stockNames):
        """Load strategy state from file"""

        stock = stocks[0]
        stockName = stockNames[0]
        file = self.GetStateFileName(stock, stockName)

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
                    'buy_index': state.get('buy_index', 0),
                    'sell_index': state.get('sell_index', 0)
                }
        except Exception as e:
            print(f"Failed to load strategy state: {e}")


    def SaveStrategyState(self, stocks, stockNames, currentHeld, basePrice, logicalHolding, buyIndex, sellIndex):
        stock = stocks[0]
        stockName = stockNames[0]
        file = self.GetStateFileName(stock, stockName)

        data = {
            'current_held': currentHeld,
            'base_price': basePrice,
            'logical_holding': logicalHolding,
            'buy_index': buyIndex,
            'sell_index': sellIndex
        }

        if self.IsBacktest:
            print(json.dumps(data, ensure_ascii=False, indent=4))
        else:
            try:
                with open(file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"Failed to save strategy state: {e}")

class MomentumRotationStrategy(BaseStrategy):
    def __init__(self, **kwargs):
        super().__init__(strategyPrefix='momrot', strategyId='a', **kwargs)

    def init(self, C):
        super().init(C)

        self.prices = None
        self.days = 25
        self.base_price = None
        self.logical_holding = 0
        self.current_held = None

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
        else:
            self.SaveStrategyState(self.Stocks, self.StockNames, None, 0, 0)

    def UpdateMarketData(self, C, stocks):
        yesterday = self.GetYesterday(C)
        self.prices = self.GetHistoricalPrices(C, self.Stocks, fields=['close'], period='1d', count=self.days+1)

    def GetRank(self):
        rank_list = []

        for stock in self.Stocks:
            df = self.prices[stock]
            y = df['log'] = np.log(df.close)
            x = df['num'] = np.arange(df.log.size)
            slope, intercept = np.polyfit(x, y, 1)
            annualized_returns = math.pow(math.exp(slope), 250) - 1
            r_squared = 1 - (sum((y - (slope * x + intercept))**2) / ((len(y) - 1) * np.var(y, ddof=1)))
            score = annualized_returns * r_squared
            score=round(score, 2)
            rank_list.append((stock, score))

        rank_list = sorted(rank_list, key=lambda x: x[1], reverse=True)

        return rank_list


    def SwitchPosition(self, C, old_stock, current_holding, new_stock, current_prices):
        print(f'SwitchPosition holding is {current_holding}')

        """执行等值换仓：平掉旧股票，用所得资金买入新股票"""
        strategy_name = self.GetUniqueStrategyName(self.Stocks[0])
        price_old = current_prices[old_stock]
        self.Sell(C, old_stock, current_holding, price_old, strategy_name)
        self.logical_holding = 0
        print(f"平仓 {current_holding} 股 {old_stock} @ {price_old:.3f}")

        cash_from_sale = current_holding * price_old

        price_new = current_prices[new_stock]

        unit_to_buy = int(cash_from_sale / price_new)
        unit_to_buy = (unit_to_buy // 100) * 100  # A股100股整数倍

        if unit_to_buy == 0:
            print(f"换仓金额不足100股，跳过")
            return

        # 检查可用资金
        available_cash = self.GetAvailableCash()

        if self.ExecuteBuy(C, new_stock, price_new, available_cash, trading_amount = cash_from_sale):
            self.base_price = price_new
            self.SaveStrategyState(self.Stocks, self.StockNames, self.current_held, self.base_price, self.logical_holding)

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

        ranks = self.GetRank()
        if not self.IsBacktest:
            print(self.prices)
            print(ranks)
        else:
            print(yesterday)

        current_prices = self.GetCurrentPrice(self.Stocks, C)

        target = ranks[0][0]
        # target = self.current_held if self.current_held is not None else self.Stocks[0]

        # print(ranks[0][1] - ranks[1][1] )
        # if ranks[0][1] - ranks[1][1] > 1:
        #     target = ranks[0][0]

        if self.current_held is None:
            self.ExecuteBuy(C, target, current_prices[target], available_cash)
        elif self.current_held != target:
            self.SwitchPosition(C, self.current_held, current_holding, target, current_prices)


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
            else:
                self.base_price = None
            print(f"Updated base price to: {self.base_price if self.base_price is not None else 'None'}")
            return True

        return False

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
        stock = stocks[0]
        stockName = stockNames[0]
        file = self.GetStateFileName(stock, stockName)

        data = {
            'current_held': currentHeld,
            'base_price': basePrice,
            'logical_holding': logicalHolding,
        }

        if self.IsBacktest:
            print(json.dumps(data, ensure_ascii=False, indent=4))
        else:
            try:
                with open(file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"Failed to save strategy state: {e}")

class JointquantEmailStrategy(BaseStrategy):
    def __init__(self, **kwargs):
        super().__init__(strategyPrefix='jointquantemail', strategyId='a', **kwargs)
        # self.JointquantStrategyId = jointquantStrategyId
        # self.JointquantStrategyName = jointquantStrategyName

    def init(self, C):
        super().init(C)

        self.last_time = None
        self.held = []
        self.logical_holding = 0
        self.LoadStrategyState()

        state = self.State
        if state and state['last_time'] is not None:
            self.last_time = state['last_time']
            self.held = state['held']
            # print(f"Loaded state from file: last_time={self.last_time}, position={self.logical_holding}, current_held={self.current_held}")
            print(f"Loaded state from file: last_time={self.last_time}")
        elif self.IsBacktest:
            print("No historical state found")
        else:
            self.SaveStrategyState(self, None, [])

    def f(self, C):
        if not self.IsBacktest and not self.IsTradingTime():
            return

        yesterday = self.GetYesterday(C)
        available_cash = self.GetAvailableCash()

        if not self.CheckWaitingList():
            return

        # Get position
        holdings = self.GetPositions()

        file = f'D:/software/君弘君智交易系统/bin.x64/joinquant_{self.Stocks[0]}.json'
        if not os.path.exists(file):
            return
        try:
            with open(file, 'r', encoding='utf-8') as f:
                state = json.load(f)

                self.last_time = state['current_time']
                held_stocks = state['held_stocks']
        except Exception as e:
            print(f"Failed to load strategy state: {e}")

        held_stocks = [s.replace('XSHE', 'SZ') for s in held_stocks]
        held_stocks = [s.replace('XSHG', 'SH') for s in held_stocks]

        executed = False
        to_hold = []
        for hold in self.held:
            stock = hold['stock']
            logical_holding = hold['logical_holding']
            if stock not in held_stocks:
                if self.ExecuteSell(C, stock, int(logical_holding)):
                    executed = True
            else:
                to_hold.append(hold)

        to_buy = [s for s in held_stocks if s not in self.held]
        if to_buy:
            if not self.IsBacktest:
                self.SellYHRL(C, self.TradingAmount * len(to_buy), holdings)
            current_prices = self.GetCurrentPrice(to_buy, C)
            for to_hold in to_buy:
                if self.ExecuteBuy(C, to_hold, current_prices[to_hold]):
                    executed = True
                    to_hold.append({'stock': to_hold, 'logical_holding': self.logical_holding})

        self.held = held

        if executed:
            self.SaveStrategyState(self.last_time, self.held)

    def ExecuteBuy(self, C, stock, current_price, trading_amount = None):
        if trading_amount is None:
            buy_amount = self.TradingAmount
        else:
            buy_amount = trading_amount

        unit_to_buy = int(buy_amount / current_price)
        unit_to_buy = (unit_to_buy // 100) * 100  # 取整到100的倍数

        if  unit_to_buy > 0:
            strategy_name = self.GetUniqueStrategyName(self.Stocks[0])
            # self.Buy(C, stock, unit_to_buy, current_price, strategy_name)
            # print({'stock': stock, 'unit_to_buy': unit_to_buy, 'current_price': current_price, 'strategy_name': strategy_name})
            self.logical_holding += unit_to_buy
            return True

    def SellYHRL(self, C, target_cash, holdings):
        stock = '511880.SH'
        current_holding = holdings.get(stock, 0)

        if current_holding <= 0:
            print(f"无511880.SH持仓")
            return

        current_price = 100

        # 计算每100股价值（511880.SH通常100股起卖）
        value_per_100 = current_price * 100

        units_needed = int((target_cash + value_per_100 - 1) / value_per_100)  # 向上取整
        sell_units = min(units_needed, current_holding // 100)
        sell_volume = sell_units * 100

        if sell_volume <=0 :
            print(f"资金缺口小，不足卖出100股，暂不操作")
            return

        if sell_volume > 0:
            self.PassOrder(24, 1101, self.Account, stock, 14, -1, sell_volume, '', 2, '', C)

    def ExecuteSell(self, C, stock, current_holding):
        sell_amount = self.TradingAmount

        unit_to_sell = current_holding

        if unit_to_sell > 0:    # Ensure at least 100 shares
            strategy_name = self.GetUniqueStrategyName(self.Stocks[0])
            # self.Sell(C, stock, unit_to_sell, current_price, strategy_name)

            return True

        return False

    def LoadStrategyState(self):
        """Load strategy state from file"""

        if self.IsBacktest:
            self.State = None
            return

        stock = self.Stocks[0]
        file = self.GetStateFileName(stock, stock)

        if not os.path.exists(file):
            self.State = None
            return
        try:
            with open(file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                # Check if state for current stock exists
                self.State = {
                    'last_time': state.get('last_time'),
                }
        except Exception as e:
            print(f"Failed to load strategy state: {e}")


    def SaveStrategyState(self, last_time, held):
        file = self.GetStateFileName(self.Stocks[0], self.StockNames[0])

        data = {
            'last_time': last_time,
            'held': held
        }

        if self.IsBacktest:
            print(json.dumps(data, ensure_ascii=False, indent=4))
        else:
            try:
                with open(file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"Failed to save strategy state: {e}")

