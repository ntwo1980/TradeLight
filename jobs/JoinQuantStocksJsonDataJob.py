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
        df_stocks['code'] = df_stocks['code'].str.slice(0, 6)

        df_stocks['peg'] = df_stocks['pe'] / df_stocks['iop']
        df_stocks['mc_r'] = df_stocks['mc'].rank(ascending = True, method = 'max', pct=True)
        df_stocks['cmc_r'] = df_stocks['cmc'].rank(ascending = True, method = 'max', pct=True)
        df_stocks['pe_r'] = df_stocks['pe'].where(df_stocks['pe'] >=0, 100000).rank(ascending = True, method = 'max', pct=True)
        df_stocks['peg_r'] = df_stocks['peg'].where(((df_stocks['pe'] >=0) & (df_stocks['iop'] >=0)), 100000).rank(ascending = True, method = 'max', pct=True)
        df_stocks['pe_lyr_r'] = df_stocks['pe_lyr'].where(df_stocks['pe_lyr'] >=0, 100000).rank(ascending = True, method = 'max', pct=True)
        df_stocks['pb_r'] = df_stocks['pb'].where(df_stocks['pb'] >=0, 100000).rank(ascending = True, method = 'max', pct=True)
        df_stocks['ps_r'] = df_stocks['ps'].where(df_stocks['ps'] >=0, 100000).rank(ascending = True, method = 'max', pct=True)
        df_stocks['pcf_r'] = df_stocks['pcf'].where(df_stocks['pcf'] >=0, 100000).rank(ascending = True, method = 'max', pct=True)
        df_stocks['itr_r'] = df_stocks['itr'].rank(ascending = True, method = 'max', pct=True)
        df_stocks['ir_r'] = df_stocks['ir'].rank(ascending = True, method = 'max', pct=True)
        df_stocks['inp_r'] = df_stocks['inp'].rank(ascending = True, method = 'max', pct=True)
        df_stocks['iop_r'] = df_stocks['iop'].rank(ascending = True, method = 'max', pct=True)
        df_stocks['inps_r'] = df_stocks['inps'].rank(ascending = True, method = 'max', pct=True)

        for _, s in df_stocks.iterrows():
            json_file = os.path.join(self.json_dir, '{}.json'.format(s['code']))
            with open(json_file, 'w', encoding='utf-8') as f:
                s.to_json(f, force_ascii=False)
