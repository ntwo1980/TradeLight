import pandas as pd
import matplotlib.pyplot as plt
import jobs.PostSectionGenerator as p

class AboveMaPostSectionGenerator(p.PostSectionGenerator):
    def __init__(self, data_file_path, blog_upload_relative_path, blog_upload_absolute_path):
        self.data_file_path = data_file_path
        self.blog_upload_relative_path = blog_upload_relative_path
        self.blog_upload_absolute_path = blog_upload_absolute_path

    def generate(self, blog_generator):
        blog_generator.h3('高于均线')
        # data_path = os.path.join(script_dir, 'data/r_up_down.csv')

        df = pd.read_csv(self.data_file_path, index_col='date', parse_dates=True)

        blog_generator.line('收盘价高于42日均线比例{:.2f}%。'.format(df['above_ma'][-1]))

        fig, axes = plt.subplots(1, 1, figsize=(16, 6))

        ax1 = axes
        ax1.plot(df.index, df['above_ma'], label='above 42 MA pct')
        ax1.plot(df.index, df['above_ma']. rolling(20).mean(), label='above 42 MA pct 20 MA')
        ax1.legend(loc='upper left')
        ax1.set_ylabel('above 42 MA pct')
        ax2= ax1.twinx()
        ax2.plot(df.index, df['index'], 'y', label='399001')

        figure_name = ('r_above_ma.png')
        figure_path = '{}{}'.format(self.blog_upload_absolute_path, figure_name)

        plt.savefig(figure_path, bbox_inches='tight')

        blog_generator.img('{}{}'.format(self.blog_upload_relative_path, figure_name))
