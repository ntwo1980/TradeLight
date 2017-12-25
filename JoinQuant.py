import os
import datetime
import json
import re
import requests
import unittest
import pandas as pd

class JoinQuant:
    WEB_ROOT = 'https://www.joinquant.net'
    LOGIN_PAGE = WEB_ROOT
    LOGIN_API =  '{}/user/login/doLogin?ajax=1'.format(WEB_ROOT)
    TRANSACTION_API = '{}/algorithm/live/transactionDetail'.format(WEB_ROOT)
    WEB_REFERER = '{}/user/login/index'.format(WEB_ROOT)
    WEB_ORIGIN = WEB_ROOT
    JUPTER_PAGE = '{}/hub/login?next='.format(WEB_ROOT)
    DOWNLOAD_FILES = WEB_ROOT + '/user/{}/files/data/{}?download=1'

    def __init__(self, config):
        self.s = requests.Session()
        self.config = config

        self.script_dir = os.path.dirname(__file__)
        self.data_path = os.path.join(self.script_dir, 'data/')

    def login(self):
        # mock headers
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': self.WEB_ORIGIN,
            'Referer': self.WEB_REFERER,
            'Pragma': 'no-cache',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.100 Safari/537.36', 'X-Requested-With': 'XMLHttpRequest',
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
        set_cookie = rep.headers['Set-Cookie']
        if len(set_cookie) < 100:
            return False, 'Login failed'

        # self.s.headers.update({
            # 'cookie': set_cookie
        # })

        # init jupter cookie
        params = {
            'username': account_config['userid'],
            'token': self.s.cookies['PHPSESSID']
        }
        rep = self.s.post(self.JUPTER_PAGE, data=params)

        return True, "succeed"

    def create_login_params(self, user, password):
        params = {
            'CyLoginForm[username]': user,
            'CyLoginForm[pwd]': password,
            'ajax': 1
        }
        return params

    def fetch_file(self, file_name, new_file_name):
        account_config = self.config['account']
        rep = self.s.get(DOWNLOAD_FILES.format(account_config['userid'], file_name))

        if not new_file_name is None:
            file_path = os.path.join(self.data_path, new_file_name)
            with open(file_path, 'wb') as f:
                f.write(rep.content)
        else:
            return rep.content

class JoinQuantTest(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        script_dir = os.path.dirname(__file__)
        config_file_path = os.path.join(script_dir, 'config/JoinQuant.json')
        with open(config_file_path, 'r') as f:
            config = json.load(f)

        self.jq = JoinQuant(config)
        succeed, reason = self.jq.login()
        if not succeed:
            raise Exception("login failed: " + reason)

    @classmethod
    def tearDownClass(self):
        pass

    def test_downlad_file(self):
        self.jq.fetch_file('up_down.csv', 'r_up_down.csv')

if __name__ == '__main__':
    unittest.main()
