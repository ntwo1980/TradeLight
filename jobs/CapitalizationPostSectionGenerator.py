import os
import pandas as pd
import matplotlib.pyplot as plt
import jobs.PostSectionGenerator as p

class CapitalizationPostSectionGenerator(p.PostSectionGenerator):
    def __init__(self, data_file_path, blog_upload_relative_path, blog_upload_absolute_path):
        self.data_file_path = data_file_path
        self.blog_upload_relative_path = blog_upload_relative_path
        self.blog_upload_absolute_path = blog_upload_absolute_path

    def generate(self, blog_generator):
        csv_files = ['801811', '801812', '801813']
        blog_generator.h3('按市值')

        dfs = [pd.read_csv(
            os.path.join(self.data_file_path, 'r_sw_{}.csv'.format(f)),
            index_col='date', parse_dates=True
        ) for f in csv_files]

        columns =  ['Code', 'Name', 'Date', 'Open', 'High', 'Low', 'Close', 'Volumn', 'Amount', 'Change', 'Turnover', 'PE', 'PB', 'Payout']
        df = pd.read_csv(self.data_file_path, header=None, names=columns, parse_dates=True)
        '''
        if len(df.index) > 2 and df.ix[-1, 'index'] == df.ix[-2, 'index']:
            df = df.ix[:-1,:]

        blog_generator.line('收盘价高于42日均线比例{:.2f}%。'.format(df['above_ma'][-1]))

        fig, axes = plt.subplots(1, 1, figsize=(16, 6))

        ax1 = axes
        ax1.plot(df.index, df['above_ma'], label='above 42 MA pct')
        ax1.legend(loc='upper left')
        ax1.set_ylabel('above 42 MA pct')
        ax2= ax1.twinx()
        ax2.plot(df.index, df['index'], 'y', label='399001')

        figure_name = ('r_above_ma.png')
        figure_path = '{}{}'.format(self.blog_upload_absolute_path, figure_name)

        plt.savefig(figure_path, bbox_inches='tight')

        blog_generator.img('{}{}'.format(self.blog_upload_relative_path, figure_name))
        '''
