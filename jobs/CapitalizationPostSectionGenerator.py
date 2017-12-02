import os
import pandas as pd
import matplotlib.pyplot as plt
import jobs.PostSectionGenerator as p
from scipy import stats

class CapitalizationPostSectionGenerator(p.PostSectionGenerator):
    def __init__(self, data_file_path, blog_upload_relative_path, blog_upload_absolute_path):
        self.data_file_path = data_file_path
        self.blog_upload_relative_path = blog_upload_relative_path
        self.blog_upload_absolute_path = blog_upload_absolute_path

    def generate(self, blog_generator):
        csv_files = ['801811', '801812', '801813']
        capitalization_group_names = ['大盘', '中盘', '小盘']
        blog_generator.h3('按市值')

        columns =  ['Code', 'Name', 'Date', 'Open', 'High', 'Low', 'Close', 'Volumn', 'Amount', 'Change', 'Turnover', 'PE', 'PB', 'Payout']
        dfs = [pd.read_csv(
            os.path.join(self.data_file_path, 'r_sw_{}.csv'.format(f)),
            header=None, names=columns, parse_dates=['Date'],
            infer_datetime_format=True)
        for f in csv_files]

        for factor in ['PB', 'PE']:
            blog_generator.h4(factor)
            for i in range(0, 3):
                df = dfs[i]
                capitalization_group_name = capitalization_group_names[i]

                last_factor_value = df[factor].iloc[-1]
                blog_generator.line('{}{}统计. 当前值: {:.2f}, 1年分位数: {:.2f}, 3年分位数: {:.2f}, 5年分位数: {:.2f}, 10年分位数: {:.2f}'.format(
                    capitalization_group_name,
                    factor,
                    float(last_factor_value),
                    float(stats.percentileofscore(df[factor].iloc[-240:], last_factor_value)),
                    float(stats.percentileofscore(df[factor].iloc[-720:], last_factor_value)),
                    float(stats.percentileofscore(df[factor].iloc[-1200:], last_factor_value)),
                    float(stats.percentileofscore(df[factor].iloc[-2400:], last_factor_value))))

                for year in [1, 10]:
                    days = 240 * year
                    figure_name = 'r_{}_{}_{}.png'.format(df['Code'].iloc[0], factor, str(year))
                    self.generate_factor_figure(
                        figure_name,
                        df['Date'].iloc[-days:],
                        df[factor].iloc[-days:],
                        factor,
                        df['Close'].iloc[-days:],
                        'Close'
                    )
                    blog_generator.img('{}{}'.format(self.blog_upload_relative_path, figure_name))

    def generate_factor_figure(self, figure_name, data_x, data_y1, label_y1, data_y2 = None, label_y2=None):
        fig, axes = plt.subplots(1, 1, figsize=(16, 6))

        ax1 = axes
        ax1.plot(data_x, pd.to_numeric(data_y1, 'coerce', 'float'), label=label_y1)
        ax1.legend(loc='upper left')
        ax1.set_ylabel(label_y1)

        if data_y2 is not None:
            ax2= ax1.twinx()
            ax2.plot(data_x, pd.to_numeric(data_y2, 'coerce', 'float'), label='Close', color='orange')

        figure_path = '{}{}'.format(self.blog_upload_absolute_path, figure_name)

        plt.savefig(figure_path, bbox_inches='tight')
