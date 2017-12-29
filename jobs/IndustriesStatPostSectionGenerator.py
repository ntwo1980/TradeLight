import os
import pandas as pd
import matplotlib.pyplot as plt
import jobs.PostSectionGenerator as p
from scipy import stats

class IndustriesStatPostSectionGenerator(p.PostSectionGenerator):
    def __init__(self, data_file_path, blog_upload_relative_path, blog_upload_absolute_path):
        self.data_file_path = data_file_path
        self.blog_upload_relative_path = blog_upload_relative_path
        self.blog_upload_absolute_path = blog_upload_absolute_path
        self.all_csv_files = [
            ('证监会行业', 'zjh'),
            ('中证行业', 'zz')
        ]

    def generate(self, blog_generator):
        self.generate_summary(
            blog_generator,
            self.all_csv_files
        )

    def generate_summary(self, blog_generator, csv_files):
        names = [n for (n, _) in csv_files]
        files = [f for (_, f) in csv_files]

        dfs = [self.load_csv(f) for f in files]

        for factor in ['pb', 'pe', 'roe']:
            blog_generator.h3(factor)

            stat = []
            for (index, df) in enumerate(dfs):
                blog_generator.h3(names[index])
                last_factor_value = df[factor].iloc[-1]
                stat.append((
                    df['Name'].iloc[-1],
                    float(last_factor_value),
                    float(stats.percentileofscore(df[factor].iloc[-240:], last_factor_value)),
                    float(stats.percentileofscore(df[factor].iloc[-720:], last_factor_value)),
                    float(stats.percentileofscore(df[factor].iloc[-1200:], last_factor_value)),
                    float(stats.percentileofscore(df[factor].iloc[-2400:], last_factor_value))
                ))

            df_stat = pd.DataFrame(stat, columns=['Name', 'Factor', 'Factor1', 'Factor3', 'Factor5', 'Factor10'])
            df_stat.sort_values('Factor3', inplace=True)

            blog_generator.data_frame(df_stat,
                headers=[
                    '名称', '{}当前值'.format(factor), '1年分位数', '3年分位数', '5年分位数', '10年分位数'
                ])


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
        plt.close()


    def load_csv(self, csv_file):
        columns =['code', 'name', 'date', 'total_count', 'lose_count', 'pe', 'rolling_pe', 'pb', 'payout']
        df = pd.read_csv(
            os.path.join(self.data_file_path, 'r_industry_{}.csv'.format(csv_file)),
            header=None, names=columns, parse_dates=['date'],
            infer_datetime_format=True)

        df = df[(df['pb']!='None')&(df['pe']!='None')]
        df['roe'] = df['pb'][df['pb']!='None'].astype('float') / df ['pe'][df['pe']!='None'].astype('float')

        return df
