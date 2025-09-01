import datetime
import time
import pandas as pd
import numpy as np
import talib
import json
import os

class BaseStrategy():
    def __init__(self, stocks, stockNames, strategyPrefix, strategyId, get_trade_detail_data_func):
        self.Stocks = stocks
        self.StockNames = stockNames
        self.StrategyPrefix = strategyPrefix
        self.StrategyId = strategyId
        self.Account = "testS"
        self.AccountType = "STOCK"
        self.TradingAmount = 1000
        self.WaitingList = []
        self.GetTradeDetailData = get_trade_detail_data_func
        self.State = None
        self.PriceDate = None
        self.Prices = None

    def GetUniqueStrategyName(self, stock):
        return f"{self.StrategyPrefix}_{stock.replace('.', '')}_a"

    def GetStateFileName(self, stock, stockName):
        name = self.GetUniqueStrategyName(stock)
        return f"{name}_{stockName}.json"

    def SetAccount(self, account, accountType):
        self.Account = account
        self.AccountType = accountType

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
        strategyName = a.GetUniqueStrategyName(a.Stocks[0])
        for order in orders:
            if order.m_nOrderStatus in [49, 50, 51, 52, 55] and strategyName in order.m_strRemark:  # 待报, 已报, 已报待撤, 部成待撤, 部成
                self.WaitingList.append(order.m_strRemark)

    def GetTicketPrices(self, stocks, C):
        prices = C.get_full_tick(stocks)

        for stock in stocks:
            if stock not in prices:
                print(f"Failed to get real-time price for {stock}")

        return prices


    def GetDailyPrices(self, stocks, count, endDate, C):
        if self.PriceDate is None or self.PriceDate != endDate:
            self.Prices = C.get_market_data_ex(['high','low','close'],stocks, period = "1d",count=count,end_time = endDate)
            self.PriceDate = endDate

        return self.Prices

    def RefreshWaitingList(self):
        if self.WaitingList:
            foundList = []
            orders = get_trade_detail_data(self.Account, self.AccountType, 'order')
            for order in orders:
                if order.m_strRemark in self.WaitingList:
                    if order.m_nOrderStatus in {54, 56, 57}:  # 已撤, 已成, 废单
                        foundList.append(order.m_strRemark)

            self.WaitingList = [i for i in self.WaitingList if i not in foundList]

class SimpleGridStrategy(BaseStrategy):
    def __init__(self, **kwargs):
        super().__init__(strategyPrefix='grid', strategyId='a', **kwargs)

    def init(self, C):
        self.IsBacktest = C.do_back_test

        if not self.IsBacktest:
            self.SetAccount(account, accountType)

        self.TradingAmount = 30000
        self.prices = None
        self.prices_date = None
        self.base_price = None
        self.logical_holding = 0
        self.atr = 0
        self.rsi = 50
        self.grid_unit = 0
        self.max_price = 0
        self.yesterday_price = 0


        self.RebuildWaitingListFromOpenOrders()

        self.LoadStrategyState(a.Stocks, a.StockNames)

        state = self.State
        if state and state['base_price'] is not None:
            self.base_price = state['base_price']
            self.logical_holding = state['logical_holding']
            print(f"Loaded state from file: base_price={self.base_price}, position={self.logical_holding}")
        elif self.IsBacktest:
            print("No historical state found, will initialize base_price using first average")


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

                    State = {
                        'base_price': state.get('base_price'),
                        'logical_holding': state.get('logical_holding', 0)
                    }
        except Exception as e:
            print(f"Failed to load strategy state: {e}")


    def SaveStrategyState(self, stock, stockName, basePrice, logicalHolding):
        """Load strategy state from file"""

        if self.IsBacktest:
            return

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
            'base_price': base_price,
            'logical_holding': logical_holding
        }

        try:
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Failed to save strategy state: {e}")

