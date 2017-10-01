import os
import datetime
import numpy as np
import pandas as pd
import jobs.JobBase as j
import HexoGenerator

class JoinQuantStocksDataJob(j.JobBase):
    def __init__(self, posts_dir, data_file_path):
        self.posts_dir = posts_dir
        self.data_file_path = data_file_path

    def run(self):
        df_stocks = pd.read_csv(self.data_file_path)
        df_stocks['code'] = df_stocks['code'].str.slice(0, 6)

        for _, s in df_stocks.iterrows():
            code = s['code']
            post_dir = os.path.join(self.posts_dir, 'r_{}'.format(code))
            if not os.path.exists(post_dir):
                os.makedirs(post_dir)

            blog_generator = HexoGenerator.HexoGenerator(
            os.path.join(post_dir, 'index.md'), '{} - {}'.format(code, s['name']))

            blog_generator.h3('技术面')

            indicator_names = []
            indicator_values = []
            indicator_remark = []

            indicator_names.append('收盘价')
            indicator_values.append(s['close'])
            indicator_remark.append(np.nan)

            indicator_names.append('250日内交易日数量')
            indicator_values.append(s['close_count'])
            indicator_remark.append(np.nan)

            indicator_names.append('42日均线')
            indicator_values.append(s['ma42'])
            indicator_remark.append(np.nan)

            indicator_names.append('120日均线')
            indicator_values.append(s['ma120'])
            indicator_remark.append(np.nan)

            indicator_names.append('250日均线')
            indicator_values.append(s['ma250'])
            indicator_remark.append(np.nan)

            indicator_names.append('10内最高价')
            indicator_values.append(s['max10'])
            indicator_remark.append(np.nan)

            indicator_names.append('10内最低价')
            indicator_values.append(s['min10'])
            indicator_remark.append(np.nan)

            indicator_names.append('ATR10')
            indicator_values.append(s['atr10'])
            indicator_remark.append(np.nan)

            indicator_names.append('22日EMA斜率')
            indicator_values.append(s['l_slop'])
            indicator_remark.append(np.nan)

            indicator_names.append('22日EMA斜率pvalue')
            indicator_values.append(s['l_pvalue'])
            indicator_remark.append(np.nan)

            indicator_names.append('22日EMA斜率stderror')
            indicator_values.append(s['l_stderror'])
            indicator_remark.append(np.nan)

            df_tech = pd.DataFrame({'indicator_names': indicator_names, 'indicator_values': indicator_values, 'indicator_remark': indicator_remark})

            blog_generator.data_frame(df_tech[['indicator_names', 'indicator_values', 'indicator_remark']],
                headers=[
                    '指标', '值', '备注'
                ])

            blog_generator.h3('基本面')

            blog_generator.line('统计时间：{}'.format(s['stat_date']))

            factor_names = []
            factor_values = []
            factor_ranks = []

            factor_names.append('总市值')
            factor_values.append(s['mc'])
            factor_ranks.append(np.nan)

            factor_names.append('流通市值')
            factor_values.append(s['cmc'])
            factor_ranks.append(np.nan)

            factor_names.append('市盈率')
            factor_values.append(s['pe'])
            factor_ranks.append(np.nan)

            factor_names.append('静态市盈率')
            factor_values.append(s['pe_lyr'])
            factor_ranks.append(np.nan)

            factor_names.append('市净率')
            factor_values.append(s['pb'])
            factor_ranks.append(np.nan)

            factor_names.append('市销率')
            factor_values.append(s['ps'])
            factor_ranks.append(np.nan)

            factor_names.append('市现率')
            factor_values.append(s['pcf'])
            factor_ranks.append(np.nan)

            factor_names.append('运营利润增长率')
            factor_values.append(s['iop'])
            factor_ranks.append(np.nan)

            df_fund = pd.DataFrame({'factor_name': factor_names, 'factor_value': factor_values, 'factor_rank': factor_ranks})

            blog_generator.data_frame(df_fund[['factor_name', 'factor_value', 'factor_rank']],
                headers=[
                    '指标', '值', '排序值'
                ])
            blog_generator.write()
        '''
        blog_generator = HexoGenerator.HexoGenerator(self.post_path, '主要指数月回报统计', tags=['数据统计'])

        total_df = pd.read_csv(self.data_file_path)
        dfs = np.array_split(total_df, len(total_df.index) / 12 )   # split whole dataframe into dataframes of individual index
        for df in dfs:
            blog_generator.h3(df['index_name'].iat[0])
            blog_generator.data_frame(df[['month', 'count', 'mean', 'min', 'max', 'positive_pct']],
                headers=[
                    '月', '样本数量', '平均', '最小值', '最大值', '正回报比率'
                ])

        blog_generator.write()
        '''
