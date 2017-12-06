import datetime
import os
from os.path import basename
import glob
import json
import numpy as np
import pandas as pd
import jobs.JobBase as j
import matplotlib.pyplot as plt
from scipy import stats

class StocksPBPEStatJob(j.JobBase):
    def __init__(self, data_path, stat_output_path):
        self.data_path = data_path
        self.stat_output_path = stat_output_path

    def run(self):
        files = glob.glob(os.path.join(self.data_path, 'r_zz_*.csv'))
        columns =  ['code', 'name', 'date', 'category_code', 'category_name,', 'subcategory_code', 'subcategory_name', 'pe', 'rolling_pe', 'pb', 'payout']

        for f in files:
            df = pd.read_csv(f, header=None, names=columns, parse_dates=['date'], infer_datetime_format=True)
            stat = {'name': df['name'].iloc[-1]}

            for factor in ['pb', 'rolling_pe']:
                last_factor_value = df[factor].iloc[-1]
                stat[factor + '1'] = stats.percentileofscore(df[factor].iloc[-240:], last_factor_value)
                stat[factor + '3'] = stats.percentileofscore(df[factor].iloc[-720:], last_factor_value)
                stat[factor + '5'] = stats.percentileofscore(df[factor].iloc[-1200:], last_factor_value)
                stat[factor + '10'] = stats.percentileofscore(df[factor].iloc[-2400:], last_factor_value)

            with open(os.path.join(self.stat_output_path, basename(f).replace('r_zz_', '').replace('.csv', '_PBPE.json')), 'w', encoding='utf-8') as fp:
                json.dump(stat, fp)

