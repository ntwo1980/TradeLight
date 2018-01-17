import os
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
        stat = df_closes.transform(lambda x: x / benchmark)
        dates = df_closes.index

        for index in stat.columns[1:]:
            index_name = df_names.at[index, 'display_name']

            blog_generator.h4(index_name)

            for year in [1, 2]:
                days = 240 * year
                figure_name = 'r_index_compare_{}_{}.png'.format(index, str(year))

                fig, axes = plt.subplots(1, 1, figsize=(16, 6))
                ax1 = axes
                ax1.plot(dates[-days:], df_closes.ix[-days:,index], label='{}'.format(index_name))
                ax1.plot(dates[-days:], df_closes.ix[-days:,index].rolling(20).mean(), label='{} MA20'.format(index_name))
                ax1.legend(loc='upper left')

                figure_path = '{}{}'.format(self.blog_upload_absolute_path, figure_name)

                plt.savefig(figure_path, bbox_inches='tight')
                plt.close()

                blog_generator.img('{}{}'.format(self.blog_upload_relative_path, figure_name))
