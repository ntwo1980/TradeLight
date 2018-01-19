import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import jobs.PostSectionGenerator as p
from scipy import stats

class IndexesCompareJob(p.PostSectionGenerator):
    def __init__(self, index_closes_file_path, index_names_file_path, blog_upload_relative_path, blog_upload_absolute_path):
        self.index_closes_file_path = index_closes_file_path
        self.index_names_file_path = index_names_file_path
        self.blog_upload_relative_path = blog_upload_relative_path
        self.blog_upload_absolute_path = blog_upload_absolute_path

    def generate(self, blog_generator):
        blog_generator.h3('指数对比')

        df_names = pd.read_csv(
            self.index_names_file_path,
            header=0, index_col=0)

        df_closes = pd.read_csv(
            self.index_closes_file_path,
            header=0, index_col=0,
            parse_dates=['date'], infer_datetime_format=True)

        benchmark = df_closes.ix[:,0]
        stat_df = df_closes.transform(lambda x: x / benchmark)
        dates = df_closes.index
        ma_window = 30
        double_ma_window = 60

        summary_df = pd.DataFrame(columns=['index', 'slop', 'above_ma'])
        blog_generator.h4('总计')

        for index in stat_df.columns[1:]:
            index_name = df_names.at[index, 'display_name']
            ratios = stat_df.ix[-double_ma_window:,index]
            ratios_rolling_ma = ratios.rolling(ma_window).mean()
            diff = (ratios - ratios_rolling_ma) / ratios_rolling_ma

            (slop, _, _, _, _) = self.get_linear(ratios[-ma_window:])
            above_ma = diff[-1]
            summary_df.loc[len(summary_df)] = [index_name, slop, above_ma]


        blog_generator.data_frame(summary_df,
            headers=[
                '指数', '斜率', '高于30日平均值'
            ])

        for index in stat_df.columns[1:]:
            index_name = df_names.at[index, 'display_name']

            blog_generator.h4(index_name)

            for year in [1, 3]:
                days = 240 * year
                diff_watching_days = 60  * year
                ratios = stat_df.ix[-days:,index]
                ratios_rolling_ma = ratios.rolling(ma_window).mean()
                diff = (ratios - ratios_rolling_ma) / ratios_rolling_ma
                figure_name = 'r_index_compare_{}_{}.png'.format(index, str(year))

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
                ax2.axhline(y=[diff_max - diff_range * threshold, 0, diff_min + diff_range * 0.2], linestyle=':')
                ax2.axhspan(diff_max - diff_range * threshold, diff_max, color='red', alpha=0.5])
                ax2.axhspan(diff_min, diff_min + diff_range * threshold, color='green', alpha=0.5])
                ax2.axhline(y=0, linestyle=':')

                figure_path = '{}{}'.format(self.blog_upload_absolute_path, figure_name)

                plt.savefig(figure_path, bbox_inches='tight')
                plt.close()

                blog_generator.img('{}{}'.format(self.blog_upload_relative_path, figure_name))

    def get_linear(self, prices):
        prices_mean = prices.mean()
        factor = 10000 / prices_mean
        prices = prices * factor

        days = np.arange(1, len(prices) + 1)

        linear = stats.linregress(days, prices)

        return linear
