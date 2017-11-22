import os
import datetime
import json
import re
import requests
import unittest
import pandas as pd

class SW:
    WEB_REFERER = 'http://www.swsindex.com/idx0510.aspx'
    WEB_INDEX = 'http://www.swsindex.com/idx0510.aspx'

    def __init__(self):
        self.s = requests.Session()

        self.script_dir = os.path.dirname(__file__)
        self.data_path = os.path.join(self.script_dir, 'data/')

    def login(self):
        # mock headers
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Host': 'www.swsindex.com',
            'Referer': self.WEB_REFERER,
            'Proxy-Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'
        }
        self.s.headers.update(headers)
        # init cookie
        self.s.get(self.WEB_INDEX)


        return True, "succeed"

    def fetch_file(self, file_name, new_file_name):
        rep = self.s.get("http://www.swsindex.com/downloadfiles.aspx?swindexcode={}&type=510&columnid=8890".format(file_name))

        if not new_file_name is None:
            file_path = os.path.join(self.data_path, new_file_name)
            with open(file_path, 'wb') as f:
                f.write(rep.content)
        else:
            return rep.content

class JoinQuantTest(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.sw = SW()
        succeed, reason = self.sw.login()
        if not succeed:
            raise Exception("login failed: " + reason)

    @classmethod
    def tearDownClass(self):
        pass

    def test_downlad_file(self):
        self.jq.fetch_file('801001')

if __name__ == '__main__':
    unittest.main()
