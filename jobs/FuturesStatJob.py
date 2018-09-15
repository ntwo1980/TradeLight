import datetime
import os
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import unittest
import jobs.JobBase as j
import jobs.BlogPostGenerateJobBase as b
import HexoGenerator

class FuturesStatJob(b.BlogPostGenerateJobBase):
    def __init__(self, post_path, future_list_file_path, futures_file_path):
        b.BlogPostGenerateJobBase.__init__(self, post_path)
        self.future_list_file_path = future_list_file_path
        self.futures_file_path = futures_file_path

    def run(self):
        blog_generator = HexoGenerator.HexoGenerator(self.post_path, '期货 - {}'.format(j.JobBase.get_today_str()), tags=['数据统计'])
        df_future_list = pd.read_csv(
            self.future_list_file_path,
            infer_datetime_format=True)
        df_futures = pd.read_csv(
            self.futures_file_path,
            index_col='date',
            infer_datetime_format=True)

        df_futures = df_futures.unstack().reset_index()
        df_futures.columns = ['code', 'date', 'close']
        df_futures.dropna(inplace=True)
        df_futures_stat = df_futures.groupby('code')['close'].agg(
                            {
                                'count': 'count',
                                'close': 'last',
                                'return': lambda closes: closes.iloc[-1] / closes.iloc[-2 - 1,
                                'close1': lambda closes: stats.percentileofscore(closes[-240:], closes.iloc[-1]),
                                'close3': lambda closes: stats.percentileofscore(closes[-720:], closes.iloc[-1]),
                                'close5': lambda closes: stats.percentileofscore(closes[-1200:], closes.iloc[-1]),
                                'close10': lambda closes: stats.percentileofscore(closes[-2400:], closes.iloc[-1])
                            }).reset_index()
        df_futures_stat = df_futures_stat[df_futures_stat['count']>240]
        df_futures_stat = pd.merge(df_futures_stat, df_future_list, how='left')
        df_futures_stat['display_name'] = df_futures_stat['display_name'].str.replace('主力合约', '')

        blog_generator.h3('汇总')
        blog_generator.data_frame(df_futures_stat[['display_name', 'count', 'close', 'return', 'close1', 'close3', 'close5', 'close10']],
            headers=[
                '名称', '样本数量', '收盘价', '涨幅', '1年分位数', '3年分位数', '5年分位数', '10年分位数'
            ])

        for _, row in df_futures_stat.iterrows():
            code = row['code']
            blog_generator.h3(row['display_name'])
            df_future = df_futures[df_futures['code']==code]
            dates = pd.to_datetime(df_future['date'])
            closes = df_future['close']
            last_close = closes.iloc[-1]

            if not pd.isnull(last_close):
                for year in [1, 10]:
                    days = 240 * year
                    figure_name = 'r_future_{}_{}.png'.format(code, str(year))

                    fig, axes = plt.subplots(1, 1, figsize=(16, 6))
                    ax1 = axes
                    ax1.plot(dates.iloc[-days:], pd.to_numeric(closes.iloc[-days:], 'coerce', 'float'), label='close')
                    ax1.plot(dates.iloc[-days:], pd.to_numeric(closes.iloc[-days:].rolling(42).mean(), 'coerce', 'float'), label='close 42 MA')
                    ax1.legend(loc='upper left')

                    figure_path = os.path.join(os.path.dirname(self.post_path), figure_name)

                    plt.savefig(figure_path, bbox_inches='tight')
                    plt.close()

                    blog_generator.line('收盘: {:.2f}, 1年分位数: {:.2f}, 3年分位数: {:.2f}, 5年分位数: {:.2f}, 10年分位数: {:.2f}'.format(
                        row['close'], row['close1'], row['close3'], row['close5'], row['close10']
                    ))
                    blog_generator.img(figure_name)

        blog_generator.write()
