import collections
import os
import datetime as dt
# import jobs.JobBase as j
import unittest
import requests
import pandas as pd
from bs4 import BeautifulSoup

# class IndustriesDownloadFilesJob(j.JobBase):
class IndustriesDownloadFilesJob:
    def __init__(self, data_file_path):
        self.s = requests.Session()
        self.data_file_path = data_file_path
        self.WEB_INDEX = 'http://www.csindex.com.cn/zh-CN/downloads/industry-price-earnings-ratio'
        self.INDUSTRY_QUERY = 'http://www.csindex.com.cn/zh-CN/downloads/industry-price-earnings-ratio?type={}{}&date={}'

    def run(self):
        self.s.get(self.WEB_INDEX)
        today = dt.date.today()
        date_format = '%Y-%m-%d'

    def fetch_data(self, data_source, data_type, data_date):
        rep = self.s.get(self.INDUSTRY_QUERY.format(data_source, data_type, data_date))
        content = rep.content
        html = BeautifulSoup(content, "lxml")
        tables = html.find_all('table', class_='list-div-table')
        df = pd.DataFrame(columns=['code', 'name', 'value', 'total_count', 'lose_count'])

        for table in tables:
            divs = table.find_all('div')
            df = df.append({
                'code': self.clearStr(divs[0].text),
                'name': self.clearStr(divs[1].text),
                'value': self.clearStr(divs[2].text),
                'total_count': self.clearStr(divs[3].text),
                'lose_count': self.clearStr(divs[4].text)
            }, ignore_index=True)

        return df

    def clearStr(self, s):
        if isinstance(s, str):
            return s.replace(' ', '').replace('--', '').replace('\r', '').replace('\n', '')

        return s

class IndustriesDownloadFilesJobTest(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.job = IndustriesDownloadFilesJob(None)
        self.job.run()

    @classmethod
    def tearDownClass(self):
        pass

    def test_downlad_file(self):
        self.job.fetch_data('zjh', 1, '2011-05-03')

if __name__ == '__main__':
    unittest.main()
