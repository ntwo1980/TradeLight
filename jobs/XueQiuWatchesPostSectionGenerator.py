import datetime
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import jobs.PostSectionGenerator as p

class XueQiuWatchesPostSectionGenerator(p.PostSectionGenerator):
    def __init__(self, watches_data_files, stocks_file_path):
        self.watches_data_files = watches_data_files
        self.stocks_file_path = stocks_file_path

    def generate(self, blog_generator):
        df_stocks = pd.read_csv(self.stocks_file_path)
        df_stocks.loc[:,'code'] = df_stocks['code'].str.slice(0, 6)

        blog_generator.h3('关注')

        for data_file in self.watches_data_files:
            blog_generator.h4(data_file[0])
            df = pd.read_csv(data_file[1])

            stock_codes = df['code'].str.slice(2, 8)
            df = df_stocks[df_stocks['code'].isin(stock_codes)]

            df.loc[(df['l_pvalue'] > 0.001) | (df['l_stderror'] > 7), 'l_slop'] = np.nan
            df.loc[:,'code'] = df['code'].map(lambda x: blog_generator.get_url_str(x, '/stocks/?code=' + x))
            df['above_ma42'] = (df['close'] / df['ma42'] - 1) * 100
            df['above_min10'] = (df['close'] / df['min10'] - 1) * 100
            df['below_max10'] = (df['max10'] / df['close'] - 1) * 100
            df['below_max10_atr'] = (df['max10'] - df['close']) / df['atr10']

            blog_generator.data_frame(df[['code', 'name', 'l_slop', 'above_ma42', 'above_min10', 'below_max10', 'below_max10_atr']],
                headers=[
                    '代码', '名称', '斜率', '高于42日均线', '高于10日低价', '低于10日高价', '低于10日高价ATR'
                ])
