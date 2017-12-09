import os
import datetime as dt
import jobs.JobBase as j
import requests
import pandas as pd
from bs4 import BeautifulSoup

class StocksDownloadFilesJob(j.JobBase):
    def __init__(self, stocks, data_file_path):
        self.s = requests.Session()
        self.stocks = stocks
        self.data_file_path = data_file_path
        self.WEB_INDEX = 'http://www.csindex.com.cn/zh-CN/downloads/industry-price-earnings-ratio'
        self.STOCK_QUERY = 'http://www.csindex.com.cn/zh-CN/downloads/industry-price-earnings-ratio-detail?date={}&class=1&search=1&csrc_code={}'

    def run(self):
        self.s.get(self.WEB_INDEX)
        today = dt.date.today()
        date_format = '%Y-%m-%d'

        for stock in self.stocks:
            date = dt.date(2011, 11, 30)

            csv_file = os.path.join(self.data_file_path, 'r_zz_{}.csv'.format(stock))
            if os.path.exists(csv_file):
                df = pd.read_csv(csv_file, parse_dates=False, header=None,
                                 names=[
                                            'code', 'name', 'date', 'category_code',
                                            'category_name,', 'subcategory_code',
                                            'subcategory_name', 'pe', 'rolling_pe', 'pb', 'payout']
                                )
                if len(df['date']):
                    date = dt.datetime.strptime(df['date'].iloc[-1], date_format).date() + dt.timedelta(days=1)

            if 'ST' in df['name'].iloc[-1] and (today - date).days > 60:
                continue

            items = []

            while date < today:
                if date.weekday() > 4:
                    date = date + dt.timedelta(days=1)
                    continue

                date_str = date.strftime(date_format)
                rep = self.s.get(self.STOCK_QUERY.format(date_str, stock))
                content = rep.content
                html = BeautifulSoup(content, "lxml")

                tds = html.find_all("td")
                if not len(tds):
                    date = date + dt.timedelta(days=1)
                    continue

                code = self.clearStr(tds[1].string)
                name = self.clearStr(tds[2].string)
                category_code = self.clearStr(tds[3].string)
                category_name = self.clearStr(tds[4].string)
                subcategory_code = self.clearStr(tds[5].string)
                subcategory_name = self.clearStr(tds[6].string)
                pe = self.clearStr(tds[7].string)
                rolling_pe = self.clearStr(tds[8].string)
                pb = self.clearStr(tds[9].string)
                payout = self.clearStr(tds[10].string)

                items.append((code, name, date_str, category_code, category_name, subcategory_code,
                    subcategory_name, pe, rolling_pe, pb, payout))

                date = date + dt.timedelta(days=1)

            if len(items):
                df = pd.DataFrame(items)
                df.to_csv(csv_file, index=False, header=None, encoding='utf-8', mode='a+')

    def clearStr(self, s):
        if isinstance(s, str):
            return s.replace(' ', '').replace('--', '')

        return s
