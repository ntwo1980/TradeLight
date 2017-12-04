import os
import datetime as dt
import jobs.JobBase as j
import requests
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

        for stock in self.stocks:
            start_date = '2017-11-30'

            csv_file = os.path.join(self.data_file_path, '{}.csv'.format(stock))
            date = start_date

            rep = self.s.get(self.STOCK_QUERY.format(date, stock))
            content = rep.content
            html = BeautifulSoup(content, "lxml")

            tds = html.find_all("td")
            code = tds[1].string
            name = tds[2].string
            category_code = tds[3].string
            category_name = tds[4].string
            subcategory_code = tds[5].string
            subcategory_name = tds[6].string
            pe = tds[7].string
            rolling_pe = tds[8].string
            pb = tds[9].string
            payout = tds[10].string

            print((code, name, category_code, category_name, subcategory_code,
                  subcategory_name, pe, rolling_pe, pb, payout))

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

    def removeComma(self, s):
        if isinstance(s, str):
            return s.replace(',', '')

        return s
