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

class UpStocksStatJob(b.BlogPostGenerateJobBase):
    def __init__(self, post_path, stocks_list_file_path, stocks_file_path, index_closes_file_path):
        b.BlogPostGenerateJobBase.__init__(self, post_path)
        self.stocks_list_file_path = stocks_list_file_path
        self.stocks_file_path = stocks_file_path
        self.index_closes_file_path = index_closes_file_path

    def run(self):
        blog_generator = HexoGenerator.HexoGenerator(self.post_path, '个股 - {}'.format(j.JobBase.get_today_str()), tags=['数据统计'])

        df_index_closes = pd.read_csv(
            self.index_closes_file_path,
            header=0, index_col=0,
            parse_dates=['date'], infer_datetime_format=True)

        df_stocks_names = pd.read_csv(
            self.stocks_list_file_path,
            header=0, index_col=0)[['display_name']]

        df_stocks_closes = pd.read_csv(
            self.stocks_file_path,
            header=0, index_col=0,
            parse_dates=['date'], infer_datetime_format=True)

        days = len(df_stocks_closes.index)
        benchmark = df_index_closes.ix[-days:,0]
        stat_df = df_stocks_closes.transform(lambda x: x * 100/ benchmark)
        dates = df_stocks_closes.index
        ma_window = 30
        double_ma_window = 60
        diff_watching_days = 60

        summary_df = pd.DataFrame(columns=['stock', 'slop', 'above_ma'])
        blog_generator.h4('总计')

        for stock in stat_df.columns:
            stock_name = df_stocks_names.at[stock, 'display_name']
            ratios = stat_df.ix[-double_ma_window:,stock]
            ratios_rolling_ma = ratios.rolling(ma_window).mean()
            diff = (ratios - ratios_rolling_ma) / ratios_rolling_ma
            diff_max = max(diff[-diff_watching_days:])
            diff_min = min(diff[-diff_watching_days:])
            diff_range = diff_max - diff_min
            threshold = 0.2
            if diff < dif_min + diff_range * threshold:
                stock_name = stock_name + '<b>+++</b>'
            elif diff > dif_max - diff_range * threshold:
                stock_name = stock_name + '<b>---</b>'

            (slop, _, _, _, _) = self.get_linear(ratios[-ma_window:])
            above_ma = diff[-1]
            summary_df.loc[len(summary_df)] = [stock_name, slop, above_ma]

        blog_generator.data_frame(summary_df,
            headers=[
                '名称', '斜率', '高于30日平均值'
            ])

        for stock in stat_df.columns:
            stock_name = df_stocks_names.at[stock, 'display_name']

            blog_generator.h4(stock_name)

            ratios = stat_df.ix[-days:,stock]
            ratios_rolling_ma = ratios.rolling(ma_window).mean()
            diff = (ratios - ratios_rolling_ma) / ratios_rolling_ma
            figure_name = 'r_stock_compare_{}.png'.format(stock)

            fig, axes = plt.subplots(1, 1, figsize=(16, 6))
            ax1 = axes
            ax1.plot(dates[-days:], ratios, label='ratio')
            ax1.plot(dates[-days:], ratios_rolling_ma, label='ratio MA' + str(ma_window))
            ax1.legend(loc='upper left')
            ax2 = axes.twinx()
            ax2.plot(dates[-days:], diff, label='diff', color='red')

            diff_max = max(diff[-diff_watching_days:])
            diff_min = min(diff[-diff_watching_days:])
            diff_range = diff_max - diff_min
            threshold = 0.2
            ax2.axhspan(diff_max - diff_range * threshold, diff_max, color='red', alpha=0.5)
            ax2.axhspan(diff_min, diff_min + diff_range * threshold, color='green', alpha=0.5)
            ax2.axhline(y=0, linestyle=':')


            figure_path = os.path.join(os.path.dirname(self.post_path), figure_name)

            plt.savefig(figure_path, bbox_inches='tight')
            plt.close()
            blog_generator.img(figure_name)

        blog_generator.write()

    def get_linear(self, prices):
        prices_mean = prices.mean()
        factor = 10000 / prices_mean
        prices = prices * factor

        days = np.arange(1, len(prices) + 1)

        linear = stats.linregress(days, prices)

        return linear
