import datetime
import numpy as np
import pandas as pd
import jobs.XueQiuJobBase as j

class XueQiuFetchPortfoliosJob(j.XueQiuJobBase):
    def __init__(self, xq, data_file_path):
        j.XueQiuJobBase.__init__(self, xq)
        self.data_file_path = data_file_path

    def run(self):
        portfolios = self.xq.fetch_all_portfolios()
        portfolios.to_csv(self.data_file_path, encoding='utf-8')
