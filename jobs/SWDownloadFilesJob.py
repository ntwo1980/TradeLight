import os
import datetime as dt
import jobs.JobBase as j
from bs4 import BeautifulSoup

class SWDownloadFilesJob(j.JobBase):
    def __init__(self, sw, download_files, data_file_path):
        self.sw = sw
        self.download_files = download_files
        self.data_file_path = data_file_path

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

    def removeComma(self, s):
        if isinstance(s, str):
            return s.replace(',', '')

        return s
