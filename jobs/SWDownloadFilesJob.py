import jobs.JobBase as j
from bs4 import BeautifulSoup

class SWDownloadFilesJob(j.JobBase):
    def __init__(self, sw, download_files):
        self.sw = sw
        self.download_files = download_files

    def run(self):
        for f in self.download_files:
            content = self.sw.fetch_file(f)
            html = BeautifulSoup(open(content, encoding='utf8'), "lxml")
            items = []

            for tr in html.find_all("tr")[1:]:
                children = list(tr.children)
                d = dt.datetime.strptime(children[2].string, "%Y/%m/%d %H:%M:%S")
                dict = {'Code': children[0].string,
                    'Name': children[1].string,
                    'Date': d,
                    'Close': children[3].string,
                    'Volumn': children[4].string,
                    'Change': children[5].string,
                    'Turnover': children[6].string,
                    'PE': children[7].string,
                    'PB': children[8].string,
                    'Average': children[9].string,
                    'AmountPercentage': children[10].string,
                    'HQLTSZ': children[11].string.replace(',', ''),
                    'AHQLTSZ': children[12].string.replace(',', ''),
                    'Payout': children[13].string}
                # Code,Name,Date,Open,High,Low,Close,Volumn,Amount,Change,Turnover,PE,PB,Average,AmountPercentage,HQLTSZ,AHQLTSZ,Payout
                item_str = '{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}'.format(
                            dict["Code"], dict["Name"], dict["Date"].strftime("%m/%d/%Y"), '', '', '',
                            dict["Close"], dict["Volumn"], '',
                            dict["Change"], dict["Turnover"], dict["PE"], dict["PB"],
                            dict["Average"], dict["AmountPercentage"],
                            dict["HQLTSZ"], dict["AHQLTSZ"], dict["Payout"])
                items.append(item_str)

            with open('r_sw_{}.csv'.format(f), 'w', encoding="utf-8") as file:
                    for i in reversed(items):
                        file.write(i + "\n")
