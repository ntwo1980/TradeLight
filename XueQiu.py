import json
import re
import requests
from structures import *

class XueQiu:
    LOGIN_PAGE = 'https://www.xueqiu.com'
    LOGIN_API = 'https://xueqiu.com/user/login'
    TRANSACTION_API = 'https://xueqiu.com/cubes/rebalancing/history.json'
    PORTFOLIO_URL = 'https://xueqiu.com/p/'
    WEB_REFERER = 'https://www.xueqiu.com'
    WEB_ORIGIN = ''

    def __init__(self, config):
        self.s = requests.Session()
        self.config = config

    def login(self):
        # mock headers
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.8',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.100 Safari/537.36',
            'Referer': self.WEB_REFERER,
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
            account_config['password'],
            account_config['account'])

        rep = self.s.post(self.LOGIN_API, data=params)

        self.check_login_success(rep)
        print('login succeed')

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

    def create_login_params(self, user, password, account):
        params = {
            'username': user,
            'areacode': '86',
            'telephone': account,
            'remember_me': '0',
            'password': password
        }
        return params

    def check_login_success(self, login_status):
        if 'error_description' in login_status:
            raise NotLoginError(login_status['error_description'])
