import os
import datetime
import numpy as np
import pandas as pd
import jobs.JobBase as j
import HexoGenerator

class JoinQuantStocksJsonDataJob(j.JobBase):
    def __init__(self, json_dir, data_file_path):
        self.json_dir = json_dir
        self.data_file_path = data_file_path

    def run(self):
        df_stocks = pd.read_csv(self.data_file_path)
        df_stocks.loc[:,'code'] = df_stocks['code'].str.slice(0, 6)

        for _, s in df_stocks.iterrows():
            json_file = os.path.join(self.json_dir, '{}.json'.format(s['code']))
            with open(json_file, 'w', encoding='utf-8') as f:
                s.to_json(f, force_ascii=False)

        json_file = os.path.join(self.json_dir, 'stocks.json')
        df_stocks.to_json(json_file, encoding='utf-8')
