import datetime
import numpy as np
import pandas as pd
import jobs.XueQiuJobBase as j

class XueQiuFetchHoldingsJob(j.XueQiuJobBase):
    def __init__(self, xq, data_file_path, portfolios):
        j.XueQiuJobBase.__init__(self, xq)
        self.data_file_path = data_file_path
        self.portfolios = portfolios

    def run(self):
        holdings = self.xq.fetch_portfolios_holdings(self.portfolios)

        holdings.to_csv(self.data_file_path, encoding='utf-8')
