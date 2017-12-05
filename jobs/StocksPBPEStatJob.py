import datetime
import os
from os.path import basename
import glob
import json
import numpy as np
import pandas as pd
import jobs.JobBase as j
import matplotlib.pyplot as plt
import jobs.PostSectionGenerator as p

class StocksPBPEStatJob(j.JobBase):
    def __init__(self, data_path, stat_output_path):
        self.data_path = data_path
        self.stat_output_path = stat_output_path

    def run(self):
        files = glob.glob(os.path.join(self.data_path, 'r_zz_*.csv'))
        columns =  ['Code', 'Name', 'Date', 'Open', 'High', 'Low', 'Close', 'Volumn', 'Amount', 'Change', 'Turnover', 'PE', 'PB', 'Payout']

        for f in files:
            df = pd.read_csv(f, header=None, names=columns, parse_dates=['Date'], infer_datetime_format=True)
            stat = {'name': df['Name'].iloc[-1]}

            for factor in ['PB', 'PE']:
                last_factor_value = df[factor].iloc[-1]
                stat[factor + '1'] = stats.percentileofscore(df[factor].iloc[-240:], last_factor_value)
                stat[factor + '3'] = stats.percentileofscore(df[factor].iloc[-720:], last_factor_value)
                stat[factor + '5'] = stats.percentileofscore(df[factor].iloc[-1200:], last_factor_value)
                stat[factor + '10'] = stats.percentileofscore(df[factor].iloc[-2400:], last_factor_value)

            with open(os.path.join(self.stat_output_path, basename(f) + '_PBPE.json'), 'w', encoding='utf-8') as fp:
                json.dump(stat, fp)

