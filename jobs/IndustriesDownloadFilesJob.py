import os
import datetime as dt
import jobs.JobBase as j
import unittest
import requests
import pandas as pd
from bs4 import BeautifulSoup

class IndustriesDownloadFilesJob(j.JobBase):
    def __init__(self, data_file_path):
        self.s = requests.Session()
        self.stocks = stocks
        self.data_file_path = data_file_path
        self.WEB_INDEX = 'http://www.csindex.com.cn/zh-CN/downloads/industry-price-earnings-ratio'
        self.INDUSTRY_QUERY = 'http://www.csindex.com.cn/zh-CN/downloads/industry-price-earnings-ratio?type={}{}&date={}'

    def run(self):
        self.s.get(self.WEB_INDEX)
        today = dt.date.today()
        date_format = '%Y-%m-%d'

    def fetch_file(data_source, data_type, data_date):
        rep = self.s.get(self.STOCK_QUERY.format(data_source, data_type, data_date))
        content = rep.content
        print(content)
        html = BeautifulSoup(content, "lxml")

    def clearStr(self, s):
        if isinstance(s, str):
            return s.replace(' ', '').replace('--', '')

        return s

class IndustriesDownloadFilesJob(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.job = IndustriesDownloadFilesJob(None)
        self.job.init()

    @classmethod
    def tearDownClass(self):
        pass

    def test_downlad_file(self):
        self.job.fetch_file('zjh', 1, '2011-05-03')

if __name__ == '__main__':
    unittest.main()
