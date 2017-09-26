import datetime
import os
import pandas as pd
import matplotlib.pyplot as plt
import jobs.PostSectionGenerator as p

class HistoryPostSectionGenerator(p.PostSectionGenerator):
    def __init__(self, data_file_path):
        self.data_file_path = data_file_path
        self.display_indexes = ['000001.XSHG', '399001.XSHE']

    def generate(self, blog_generator):
        blog_generator.h3('历史统计')

        self.generate_quarterly_stat(blog_generator)
        self.generate_monthly_stat(blog_generator)
        self.generate_weekly_stat(blog_generator)
        self.generate_weekdayly_stat(blog_generator)


    def generate_quarterly_stat(self, blog_generator):
        now = datetime.datetime.now()
        quarter = (now.month - 1) // 3 + 1
        next_quarter = quarter + 1 if quarter < 4 else 1

        quarterly_data_file = os.path.join(self.data_file_path, 'r_quarterly_returns.csv')
        df = pd.read_csv(quarterly_data_file)
        df['quarter'] = df['quarter'] / 3
        df = df[(df['quarter']==quarter) | (df['quarter']== next_quarter)]
        df = df[df['index'].isin(self.display_indexes)]
        # df.sort_values('index', inplace = True)
        blog_generator.h4('季度回报')
        blog_generator.data_frame(df[['quarter', 'index_name', 'count', 'mean', 'min', 'max', 'positive_pct']],
            headers=[
                '季度', '指数', '样本数量', '平均', '最小值', '最大值', '正回报比率'
            ])


    def generate_monthly_stat(self, blog_generator):
        now = datetime.datetime.now()
        month = now.month
        next_month = month + 1 if month < 12 else 1

        monthly_data_file = os.path.join(self.data_file_path, 'r_monthly_returns.csv')
        df = pd.read_csv(monthly_data_file)
        df = df[(df['month']==month) | (df['month']== next_month)]
        df = df[df['index'].isin(self.display_indexes)]

        blog_generator.h4('月回报')
        blog_generator.data_frame(df[['month', 'index_name', 'count', 'mean', 'min', 'max', 'positive_pct']],
            headers=[
                '月', '指数', '样本数量', '平均', '最小值', '最大值', '正回报比率'
            ])


    def generate_weekly_stat(self, blog_generator):
        now = datetime.datetime.now()
        week = now.isocalendar()[1]
        next_week = week + 1 if week < 52 else 1

        weekly_data_file = os.path.join(self.data_file_path, 'r_weekly_returns.csv')
        df = pd.read_csv(weekly_data_file)
        df = df[(df['week']==week) | (df['week']== next_week)]
        df = df[df['index'].isin(self.display_indexes)]

        blog_generator.h4('年内周回报')
        blog_generator.data_frame(df[['week', 'index_name', 'count', 'mean', 'min', 'max', 'positive_pct']],
            headers=[
                '周', '指数', '样本数量', '平均', '最小值', '最大值', '正回报比率'
            ])


    def generate_weekdayly_stat(self, blog_generator):
        now = datetime.datetime.now()
        weekday = now.weekday() + 1
        next_weekday = weekday + 1 if weekday < 5 else 1

        weekdayly_data_file = os.path.join(self.data_file_path, 'r_weekdayly_returns.csv')
        df = pd.read_csv(weekdayly_data_file)
        df['weekday'] = df['weekday'] + 1
        df = df[(df['weekday']==weekday) | (df['weekday']== next_weekday)]
        df = df[df['index'].isin(self.display_indexes)]

        blog_generator.h4('周内日回报')
        blog_generator.data_frame(df[['weekday', 'index_name', 'count', 'mean', 'min', 'max', 'positive_pct']],
            headers=[
                '星期', '指数', '样本数量', '平均', '最小值', '最大值', '正回报比率'
            ])

