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

    '''
    def run(self):
        for f in self.download_files:
            content = self.sw.fetch_file(f)
            html = BeautifulSoup(content, "lxml")

            items = []

            for tr in html.find_all("tr")[1:]:
                children = list(tr.children)
                d = dt.datetime.strptime(children[2].string, "%Y/%m/%d %H:%M:%S")
                dict = {'Code': children[0].string,
                    'Name': children[1].string,
                    'Date': d,
                    'Open': self.removeComma(children[3].string),
                    'High': self.removeComma(children[4].string),
                    'Low': self.removeComma(children[5].string),
                    'Close': self.removeComma(children[6].string),
                    'Volumn': self.removeComma(children[7].string),
                    'Amount': self.removeComma(children[8].string),
                    'Change': self.removeComma(children[9].string),
                    'Turnover': self.removeComma(children[10].string),
                    'PE': self.removeComma(children[11].string),
                    'PB': self.removeComma(children[12].string),
                    'Payout': self.removeComma(children[13].string)}
                # Code,Name,Date,Open,High,Low,Close,Volumn,Amount,Change,Turnover,PE,PB,Payout
                item_str = '{},{},{},{},{},{},{},{},{},{},{},{},{},{}'.format(
                            dict["Code"], dict["Name"], dict["Date"].strftime("%m/%d/%Y"), dict['Open'],
                            dict['High'], dict['Low'], dict["Close"], dict["Volumn"], dict["Amount"],
                            dict["Change"], dict["Turnover"], dict["PE"], dict["PB"], dict["Payout"])
                items.append(item_str)

            file_path = os.path.join(self.data_file_path, 'r_sw_{}.csv'.format(f))
            with open(file_path, 'w', encoding="utf-8") as file:
                for i in reversed(items):
                    file.write(i + "\n")
    '''

    def clearStr(self, s):
        if isinstance(s, str):
            return s.replace(' ', '').replace('--', '')

        return s
