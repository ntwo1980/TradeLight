import collections
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
        self.data_file_path = data_file_path
        self.WEB_INDEX = 'http://www.csindex.com.cn/zh-CN/downloads/industry-price-earnings-ratio'
        self.INDUSTRY_QUERY = 'http://www.csindex.com.cn/zh-CN/downloads/industry-price-earnings-ratio?type={}{}&date={}'
        self.data_sources = ['zjh', 'zz']
        self.data_types = [1, 2, 3, 4]
        self.data_types_name = ['pe', 'rolling_pe', 'pb', 'payout']
        self.date_format = '%Y-%m-%d'

    def run(self):
        self.s.get(self.WEB_INDEX)
        today = dt.date.today() - dt.timedelta(days=1)

        for ds in self.data_sources:
            date = dt.date(2011, 5, 3)

            csv_file = os.path.join(self.data_file_path, 'r_industry_{}.csv'.format(ds))
            if os.path.exists(csv_file):
                df = pd.read_csv(csv_file, parse_dates=False, header=None,
                                 names=[
                                    'code', 'name', 'date', 'total_count', 'lose_count', 'pe', 'rolling_pe', 'pb', 'payout']
                                )

                if len(df['date']):
                    date = dt.datetime.strptime(df['date'].iloc[-1], date_format).date() + dt.timedelta(days=1)

            while date < today:
                if date.weekday() > 4:
                    date = date + dt.timedelta(days=1)
                    continue

                dfs = [ self.fetch_data(ds, dt, date) for dt in self.data_types ]
                df_industry = dfs[0]

                for index, df in enumerate(dfs):
                    df_industry[self.data_types_name[index]] = df['value']

                df_industry['date'] = date.strftime(self.date_format)
                df_industry.drop(columns=['value'])

                with open(csv_file, 'a') as f:
                    df_industry.to_csv(f, header=False)

    def fetch_data(self, data_source, data_type, data_date):
        rep = self.s.get(
            self.INDUSTRY_QUERY.format(data_source, data_type, data_date.strftime(self.date_format)))

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
        self.job.fetch_data('zjh', 1, dt.date.today())

if __name__ == '__main__':
    unittest.main()
