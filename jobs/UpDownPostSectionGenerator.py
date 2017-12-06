import pandas as pd
import matplotlib.pyplot as plt
import jobs.PostSectionGenerator as p

class UpDownPostSectionGenerator(p.PostSectionGenerator):
    def __init__(self, data_file_path, blog_upload_relative_path, blog_upload_absolute_path):
        self.data_file_path = data_file_path
        self.blog_upload_relative_path = blog_upload_relative_path
        self.blog_upload_absolute_path = blog_upload_absolute_path

    def generate(self, blog_generator):
        blog_generator.h3('新低新高')
        # data_path = os.path.join(script_dir, 'data/r_up_down.csv')

        df = pd.read_csv(self.data_file_path, index_col='date', parse_dates=True)
        if len(df.index) > 2 and df.ix[-1, 'index'] == df.ix[-2, 'index']:
            df = df.ix[:-1,:]

        blog_generator.line('五日内创一个月新低比例{:.2f}%, 五日内创一个月新高比例{:.2f}%。股价低于一个月前股价95%比例{:.2f}%，股价高于一个前股价95%比例{:.2f}%。'
                    .format(df['low'][-1], df['high'][-1], df['down'][-1], df['up'][-1]))

        fig, axes = plt.subplots(2, 1, figsize=(16, 12))

        ax1 = axes[0]
        ax1.plot(df.index, df['low'], label='low pct')
        ax1.plot(df.index, df['high'], label='high pct')
        ax1.legend(loc='upper left')
        ax1.set_ylabel('low/high pct')
        ax3= ax1.twinx()
        ax3.plot(df.index, df['index'], 'y', label='399001')

        ax2 = axes[1]
        ax2.plot(df.index, df['down'], label='down pct')
        ax2.plot(df.index, df['up'], label='up pct')
        ax2.legend(loc='upper left')
        ax2.set_ylabel('down/up pct')
        ax4= ax2.twinx()
        ax4.plot(df.index, df['index'], 'y', label='399001' )

        figure_name = ('r_up_down.png')
        figure_path = '{}{}'.format(self.blog_upload_absolute_path, figure_name)

        plt.savefig(figure_path, bbox_inches='tight')

        blog_generator.img('{}{}'.format(self.blog_upload_relative_path, figure_name))
