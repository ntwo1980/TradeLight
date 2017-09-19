import os
import datetime
import json
import re
import requests
import unittest
import pandas as pd
from structures import *

class XueQiu:
    LOGIN_PAGE = 'https://www.xueqiu.com'
    LOGIN_API = 'https://xueqiu.com/snowman/login'
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
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.100 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': self.WEB_ORIGIN,
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        }
        self.s.headers.update(headers)

        # init cookie
        self.s.get(self.LOGIN_PAGE)

        # post for login
        account_config = self.config['account']
        params = self.create_login_params(
            account_config['user'],
            account_config['password'])

        rep = self.s.post(self.LOGIN_API, data=params)

        self.check_login_success(rep)
        print('login succeed')

    def fetch_all_portfolios(self):
        r = self.s.get(self.ALL_PORTFOLIOS_URL)

        portfolios = json.loads(r.text)['stocks']
        portfolio_codes = [p['code'] for p in portfolios]
        portfolio_names = [p['stockName'] for p in portfolios]

        portfolios = pd.DataFrame({"code": portfolio_codes, "name": portfolio_names})
        portfolios.set_index('code', inplace=True)
        exclude_portfolios = self.config['exclude_portfolios']

        return portfolios[~portfolios.index.isin(exclude_portfolios)]

    def get_all_portfolio(self):
        portfolio_config = self.config['portfolio']
        all_portfolio_info = {}

        for p in portfolio_config:
            yield p, self.get_portfolio(p)

    def get_portfolio(self, portfolio_id):
        r = self.s.get(self.PORTFOLIO_URL + portfolio_id)

        match_info = re.search(r'(?<=SNB.cubeInfo = ).*(?=;\n)', r.text)
        if match_info is None:
            raise Exception('cant get portfolio info, portfolio url : {}'.format(id))
        try:
            portfolio_info = json.loads(match_info.group())
        except Exception as e:
            raise Exception('get portfolio info error: {}'.format(e))

        holdings_info = portfolio_info['view_rebalancing']['holdings']
        holdings = [Holding(code=s['stock_symbol'], name=s['stock_name'], industry=s['segment_name'], weight=s['weight']) for s in holdings_info]

        return holdings

    def create_login_params(self, user, password):
        params = {
            'username': user,
            'password': password
        }
        return params

    def check_login_success(self, login_status):
        if 'error_description' in login_status:
            raise NotLoginError(login_status['error_description'])


class XueQiuTest(unittest.TestCase):
    def setUp(self):
        now = datetime.datetime.now()
        today_str = now.strftime("%Y%m%d")
        script_dir = os.path.dirname(__file__)
        config_file_path = os.path.join(script_dir, 'config/XueQiu.json')
        with open(config_file_path, 'r') as f:
            config = json.load(f)

        self.xq = XueQiu(config)
        self.xq.login()

    def tearDown(self):
        pass

    def test_get_portfolio(self):
        print(self.xq.get_portfolio('ZH1153957'))

    def test_fetch_all_portfolios(self):
        self.xq.fetch_all_portfolios()

if __name__ == '__main__':
    unittest.main()
