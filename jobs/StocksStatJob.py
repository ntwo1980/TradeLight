import datetime
import numpy as np
import pandas as pd
import jobs.JobBase as j
import HexoGenerator

class StocksStatJob(j.JobBase):
    def __init__(self, stocks_file_path):
        self.stocks_file_path = stocks_file_path

    def run(self):
        df = pd.read_csv(self.stocks_file_path)

        if 'above_ma42' not in list(df.columns):
            df['above_ma42'] = (df['close'] / df['ma42'] - 1) * 100
            df['above_min10'] = (df['close'] / df['min10'] - 1) * 100
            df['below_max10'] = (df['max10'] / df['close'] - 1) * 100
            df['below_max10_atr'] = (df['max10'] - df['close']) / df['atr10']
            df['peg'] = df['pe'] / df['iop']
            df['mc_r'] = df['mc'].rank(ascending = True, method = 'max', pct=True)
            df['cmc_r'] = df['cmc'].rank(ascending = True, method = 'max', pct=True)
            df['pe_r'] = df['pe'].where(df['pe'] >=0, 100000).rank(ascending = True, method = 'max', pct=True)
            df['peg_r'] = df['peg'].where(((df['pe'] >=0) & (df['iop'] >=0)), 100000).rank(ascending = True, method = 'max', pct=True)
            df['pe_lyr_r'] = df['pe_lyr'].where(df['pe_lyr'] >=0, 100000).rank(ascending = True, method = 'max', pct=True)
            df['pb_r'] = df['pb'].where(df['pb'] >=0, 100000).rank(ascending = True, method = 'max', pct=True)
            df['ps_r'] = df['ps'].where(df['ps'] >=0, 100000).rank(ascending = True, method = 'max', pct=True)
            df['pcf_r'] = df['pcf'].where(df['pcf'] >=0, 100000).rank(ascending = True, method = 'max', pct=True)
            df['itr_r'] = df['itr'].rank(ascending = True, method = 'max', pct=True)
            df['ir_r'] = df['ir'].rank(ascending = True, method = 'max', pct=True)
            df['inp_r'] = df['inp'].rank(ascending = True, method = 'max', pct=True)
            df['iop_r'] = df['iop'].rank(ascending = True, method = 'max', pct=True)
            df['inps_r'] = df['inps'].rank(ascending = True, method = 'max', pct=True)
            df['score'] = df.apply(self.rate_stock, axis=1)
            df['score_r'] = df['score'].rank(ascending = True, method = 'max', pct=True)

            df.set_index('code', inplace=True)
            df.to_csv(self.stocks_file_path, encoding='utf-8')

    def rate_stock(self, stock):
        score = 0
        if stock['pb_r'] < 0.1:
            score = score + 2
        elif stock['pb_r'] < 0.6:
            score = score + 1

        if stock['ps_r'] < 0.4:
            score = score + 1
        elif stock['ps_r'] > 0.9:
            score = score - 1

        if stock['pcf_r'] > 0.4:
            score = score + 1

        if stock['peg_r'] < 0.4:
            score = score + 1

        if stock['iop_r'] > 0.8:
            score = score + 2
        elif stock['iop_r'] > 0.6:
            score = score + 1

        return score


