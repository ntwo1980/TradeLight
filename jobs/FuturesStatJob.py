import datetime
import numpy as np
import pandas as pd
import jobs.JobBase as j
import jobs.BlogPostGenerateJobBase as b
import HexoGenerator

class FuturesStatJob(b.BlogPostGenerateJobBase):
    def __init__(self, post_path, future_list_file_path, futures_file_path):
        b.BlogPostGenerateJobBase.__init__(self, post_path)
        self.future_list_file_path = future_list_file_path
        self.futures_file_path = futures_file_path

    def run(self):
        blog_generator = HexoGenerator.HexoGenerator(self.post_path, '商品期货 - {}'.format(j.JobBase.get_today_str()), tags=['数据统计'])
        df_future_list = pd.read_csv(
            self.future_list_file_path,
            infer_datetime_format=True)

        '''
        df_future = pd.read_csv(
            self.futures_file_path,
            names=columns, parse_dates=['Date'],
            infer_datetime_format=True)


        total_df = pd.read_csv(self.data_file_path)
        dfs = np.array_split(total_df, len(total_df.index) / 5 )   # split whole dataframe into dataframes of individual index
        for df in dfs:
            blog_generator.h3(df['index_name'].iat[0])
            df['weekday'] = df['weekday'] + 1
            blog_generator.data_frame(df[['weekday', 'count', 'mean', 'min', 'max', 'positive_pct']],
                headers=[
                    '星期', '样本数量', '平均', '最小值', '最大值', '正回报比率'
                ])

        blog_generator.write()
        '''
