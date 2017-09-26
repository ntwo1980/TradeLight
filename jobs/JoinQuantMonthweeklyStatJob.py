import datetime
import numpy as np
import pandas as pd
import jobs.BlogPostGenerateJobBase as b
import HexoGenerator

class JoinQuantMonthweeklyStatJob(b.BlogPostGenerateJobBase):
    def __init__(self, post_path, data_file_path):
        b.BlogPostGenerateJobBase.__init__(self, post_path)
        self.data_file_path = data_file_path

    def run(self):
        blog_generator = HexoGenerator.HexoGenerator(self.post_path, '主要指数月内周回报统计', tags=['数据统计'])

        total_df = pd.read_csv(self.data_file_path)
        dfs = np.array_split(total_df, len(total_df.index) / 5 )   # split whole dataframe into dataframes of individual index
        for df in dfs:
            blog_generator.h3(df['index_name'].iat[0])
            blog_generator.data_frame(df[['week', 'count', 'mean', 'min', 'max', 'positive_pct']],
                headers=[
                    '周', '样本数量', '平均', '最小值', '最大值', '正回报比率'
                ])

        blog_generator.write()
