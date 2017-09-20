import os
import datetime
import json
import re
import requests
import unittest
import pandas as pd

class XueQiu:
    LOGIN_PAGE = 'https://www.xueqiu.com'
    LOGIN_API = 'https://xueqiu.com/user/login'
    TRANSACTION_API = 'https://xueqiu.com/cubes/rebalancing/history.json'
    PORTFOLIO_URL = 'https://xueqiu.com/p/'
    ALL_PORTFOLIOS_URL= 'https://xueqiu.com/v4/stock/portfolio/stocks.json?size=1000&category=1&type=1'
    WEB_REFERER = 'https://www.xueqiu.com'
    WEB_ORIGIN = 'https://xueqiu.com'

    def __init__(self, config):
        self.s = requests.Session()
        self.config = config

    def login(self):
        # mock headers
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Host': 'xueqiu.com',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.100 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'Pragma': 'no-cache',
        }
        self.s.headers.update(headers)

        # init cookie
        #self.s.get(self.LOGIN_PAGE)

        # post for login
        account_config = self.config['account']
        params = self.create_login_params(
            account_config['email'],
            account_config['telephone'],
            account_config['password'],
            account_config['portfolio'])

        rep = self.s.post(self.LOGIN_API, data=params)
        login_status = rep.json()
        if 'error_description' in login_status:
            return False, login_status['error_description']
        return True, "succeed"

    def fetch_all_portfolios(self):
        r = self.s.get(self.ALL_PORTFOLIOS_URL)

        portfolios = json.loads(r.text)['stocks']
        portfolio_codes = [p['code'] for p in portfolios]
        portfolio_names = [p['stockName'] for p in portfolios]

        portfolios = pd.DataFrame({"code": portfolio_codes, "name": portfolio_names})
        portfolios.set_index('code', inplace=True)
        exclude_portfolios = self.config['exclude_portfolios']

        return portfolios[~portfolios.index.isin(exclude_portfolios)]

    def fetch_all_portfolio_positions(self):
        portfolios = self.fetch_all_portfolios()
        holdings = self.fetch_portfolios_holdings(portfolios.index)

        return holdings

    def fetch_portfolios_holdings(self, portfolios):
        holdings = [self.fetch_single_portfolio_holdings(p) for p in portfolios]

        return pd.concat(holdings)

    def get_all_portfolio(self):
        portfolio_config = self.config['portfolio']
        all_portfolio_info = {}

        for p in portfolio_config:
            yield p, self.fetch_single_portfolio_holdings(p)

    def fetch_single_portfolio_holdings(self, portfolio):
        r = self.s.get(self.PORTFOLIO_URL + portfolio)

        match_info = re.search(r'(?<=SNB.cubeInfo = ).*(?=;\n)', r.text)
        if match_info is None:
            raise Exception('cant get portfolio info, portfolio url : {}'.format(id))
        try:
            portfolio_info = json.loads(match_info.group())
        except Exception as e:
            raise Exception('get portfolio info error: {}'.format(e))

        holdings_info = portfolio_info['view_rebalancing']['holdings']
        codes = [s['stock_symbol'] for s in holdings_info]
        names = [s['stock_name'] for s in holdings_info]
        industries = [s['segment_name'] for s in holdings_info]
        weights = [s['weight'] for s in holdings_info]

        holdings = pd.DataFrame(
            {
                "code": codes,
                "name": names,
                "industry": industries,
                "weight": weights
            })

        holdings.set_index('code', inplace=True)
        return holdings

    def create_login_params(self, email, telphone, password, portfolio):
        params = {
            'username': email,
            'account': telphone,
            'password': password,
            'portfolio_code': portfolio
        }
        return params


class XueQiuTest(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        script_dir = os.path.dirname(__file__)
        config_file_path = os.path.join(script_dir, 'config/XueQiu.json')
        with open(config_file_path, 'r') as f:
            config = json.load(f)

        self.xq = XueQiu(config)
        succeed, reason = self.xq.login()
        if not succeed:
            raise Exception("login failed: " + reason)

    @classmethod
    def tearDownClass(self):
        pass

    def test_get_portfolio_holdings(self):
        holdings = self.xq.fetch_single_portfolio_holdings('ZH1153957')

    def test_fetch_all_portfolios(self):
        self.xq.fetch_all_portfolios()

    def test_fetch_all_portfolio_positions(self):
        print(self.xq.fetch_all_portfolio_positions())

if __name__ == '__main__':
    unittest.main()
