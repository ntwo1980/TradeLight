import datetime
import os
import pandas as pd
import matplotlib.pyplot as plt
import jobs.PostSectionGenerator as p

class XueQiuStatPostSectionGenerator(p.PostSectionGenerator):
    def __init__(self, holdings_data_file_path):
        self.holdings_data_file_path = holdings_data_file_path

    def generate(self, blog_generator):
        if not os.path.isfile(self.holdings_data_file_path):
            return

        blog_generator.h3('雪球组合统计')

        df = pd.read_csv(self.holdings_data_file_path)
        df = df[df['code'].str.len() == 8]

        portfolios_count = df.groupby('code')['weight'].count()
        avg_weight = df.groupby('code')['weight'].sum() / portfolios_count
        df_stat = pd.DataFrame({'portfolios_count': portfolios_count, 'avg_weight': avg_weight})


        df_stat = df_stat.join(df[['code', 'name']].set_index('code').groupby(level=0).first())
        df_stat.sort_values(['portfolios_count', 'avg_weight'], ascending=False, inplace=True)
        df_stat.reset_index(inplace=True)
        df_stat['code'] = df_stat['code'].str.slice(2, 8)
        df_stat['name'] = [blog_generator.get_url_str(name, 'http://finance.sina.com.cn/realstock/company/' + ('sh' if code.startswith('6') else 'sz') + code + '/nc.shtml' )
                                for (code, name) in zip(df_stat['code'], df_stat['name'])]
        df_stat['code'] = df_stat['code'].map(lambda x: blog_generator.get_url_str(x, '/stocks/?code=' + x))

        blog_generator.data_frame(df_stat[['code', 'name', 'portfolios_count',  'avg_weight']],
            headers=[
                '代码', '名称', '持仓组合数量', '平均仓位'
            ])
