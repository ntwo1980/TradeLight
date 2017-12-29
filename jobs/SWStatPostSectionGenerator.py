import os
import pandas as pd
import matplotlib.pyplot as plt
import jobs.PostSectionGenerator as p
from scipy import stats

class SWStatPostSectionGenerator(p.PostSectionGenerator):
    def __init__(self, data_file_path, blog_upload_relative_path, blog_upload_absolute_path):
        self.data_file_path = data_file_path
        self.blog_upload_relative_path = blog_upload_relative_path
        self.blog_upload_absolute_path = blog_upload_absolute_path
        self.all_csv_files = [
            '801001', '801002', '801003', '801005', '801010', '801020', '801030', '801040', '801050', '801080',
            '801110', '801120', '801130', '801140', '801150', '801160', '801170', '801180',
            '801200', '801210', '801230', '801250', '801260', '801270', '801280', '801300',
            '801710', '801720', '801730', '801740', '801750', '801760', '801770', '801780', '801790',
            '801811', '801812', '801813', '801821', '801822', '801823', '801831', '801832', '801833', '801853',
            '801880', '801890'
        ]

    def generate(self, blog_generator):
        self.generate_summary(
            blog_generator,
            '申万-总计',
            self.all_csv_files
        )

        self.generate_by_group(
            blog_generator,
            '申万-按指数',
            ['801001', '801002', '801003', '801005', '801300', '801853']
        )

        self.generate_mc_comparison(blog_generator)

        self.generate_by_group(
            blog_generator,
            '申万-按市值',
            ['801811', '801812', '801813'],
            ['大盘', '中盘', '小盘']
        )

        self.generate_by_group(
            blog_generator,
            '申万-按行业',
            [
                '801010', '801020', '801030', '801040', '801050',
                '801110', '801120', '801150', '801160', '801170', '801180',
                '801210', '801710', '801730', '801740', '801750', '801760', '801770', '801780', '801790'
            ]
        )

    def generate_mc_comparison(self, blog_generator):
        blog_generator.h3('申万-按市值比')
        dfs = [self.load_csv(f) for f in ['801811', '801812', '801813', '801853']]
        for df in dfs:
            df.set_index('Date', drop=False, inplace=True)
        combinations = [
            ('绩优/小盘', dfs[3], dfs[2], 'excellent_small', 'excellent/small'),
            ('大盘/小盘', dfs[0], dfs[2], 'large_small', 'large/small'),
            ('大盘/中盘', dfs[0], dfs[1], 'large_medium', 'large/medium'),
            ('中盘/小盘', dfs[1], dfs[2], 'medium_small', 'medium/small')
        ]

        for factor in ['PB', 'PE', 'ROE']:
            blog_generator.h4(factor)
            for combination in combinations:
                blog_generator.h5(combination[0])
                df1 = combination[1]
                df2 = combination[2]

                dates = df1['Date']
                values = df1[factor].astype('float') / df2[factor].astype('float')

                last_value = values[-1]
                blog_generator.line('{}统计. 当前值: {:.2f}, 1年分位数: {:.2f}, 3年分位数: {:.2f}, 5年分位数: {:.2f}, 10年分位数: {:.2f}'.format(
                    factor,
                    last_value,
                    stats.percentileofscore(values.iloc[-240:], last_value),
                    stats.percentileofscore(values.iloc[-720:], last_value),
                    stats.percentileofscore(values.iloc[-1200:], last_value),
                    stats.percentileofscore(values.iloc[-2400:], last_value)))

                for year in [1, 10]:
                    days = 240 * year
                    figure_name = 'r_{}_{}_{}.png'.format(combination[3], factor, str(year))

                    fig, axes = plt.subplots(1, 1, figsize=(16, 6))
                    ax1 = axes
                    ax1.plot(dates.iloc[-days:], pd.to_numeric(values.iloc[-days:], 'coerce', 'float'), label='{} {}'.format(combination[4], factor))
                    ax1.plot(dates.iloc[-days:], pd.to_numeric(values.iloc[-days:].rolling(60).mean(), 'coerce', 'float'), label='{} {} 60 MA'.format(combination[4], factor))
                    ax1.legend(loc='upper left')

                    figure_path = '{}{}'.format(self.blog_upload_absolute_path, figure_name)

                    plt.savefig(figure_path, bbox_inches='tight')
                    plt.close()

                    blog_generator.img('{}{}'.format(self.blog_upload_relative_path, figure_name))

    def generate_summary(self, blog_generator, section_name, csv_files):
        blog_generator.h3(section_name)

        dfs = [self.load_csv(f) for f in csv_files]

        for factor in ['PB', 'PE', 'ROE']:
            blog_generator.h4(factor)

            stat = []
            for df in dfs:
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


    def generate_by_group(self, blog_generator, section_name, csv_files, group_names = None):
        blog_generator.h3(section_name)

        dfs = [self.load_csv(f) for f in csv_files]

        if group_names is None:
            group_names = [df['Name'].iloc[-1] for df in dfs]

        for factor in ['PB', 'PE', 'ROE']:
            blog_generator.h4(factor)
            for index, group_name in enumerate(group_names):
                blog_generator.h5(group_name)
                df = dfs[index]

                last_factor_value = df[factor].iloc[-1]
                blog_generator.line('{}{}统计. 当前值: {:.2f}, 1年分位数: {:.2f}, 3年分位数: {:.2f}, 5年分位数: {:.2f}, 10年分位数: {:.2f}'.format(
                    group_name,
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
        plt.close()


    def load_csv(self, csv_file):
        columns =  ['Code', 'Name', 'Date', 'Open', 'High', 'Low', 'Close', 'Volumn', 'Amount', 'Change', 'Turnover', 'PE', 'PB', 'Payout']
        df = pd.read_csv(
            os.path.join(self.data_file_path, 'r_sw_{}.csv'.format(csv_file)),
            header=None, names=columns, parse_dates=['Date'],
            infer_datetime_format=True)

        df = df[(df['PB']!='None')&(df['PE']!='None')]
        df['ROE'] = df['PB'][df['PB']!='None'].astype('float') / df ['PE'][df['PE']!='None'].astype('float')

        return df
