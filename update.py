import os
import sys
import json
import datetime
import subprocess
import shlex
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import XueQiu
import JoinQuant
import HexoGenerator
import utils

now = datetime.datetime.now()
today_str = now.strftime("%Y%m%d")
script_dir = os.path.dirname(__file__)
''''
xueqiu_config_file_path = os.path.join(script_dir, 'config/XueQiu.json')
with open(xueqiu_config_file_path, 'r') as f:
    xueqiu_config = json.load(f)

xq = XueQiu.XueQiu(xueqiu_config)

xq.login()
data_file_path = os.path.join(script_dir, 'data/XueQiu_{}.csv'.format(today_str))


all_holdings = xq.fetch_all_portfolio_positions()
all_holdings.to_csv(data_file_path)
'''

app_config_file_path = os.path.join(script_dir, 'config/app.json')
with open(app_config_file_path, 'r') as f:
    app_config = json.load(f)
blog_path = app_config['blogs_path']

blog_source_path = os.path.join(blog_path, 'source/')
blog_post_path = os.path.join(blog_source_path, '_posts/')
blog_upload_relative_path = os.path.join('/uploads/')
blog_upload_absolute_path = os.path.join(blog_source_path, blog_upload_relative_path[1:])

jq = None

def login_jointquant():
    global jq
    script_dir = os.path.dirname(__file__)
    joint_quant_config_file_path = os.path.join(script_dir, 'config/JoinQuant.json')
    with open(joint_quant_config_file_path, 'r') as f:
        join_quant_config = json.load(f)

    jq = JoinQuant.JoinQuant(join_quant_config)
    succeed, reason = jq.login()
    if not succeed:
        raise Exception("login failed: " + reason)

def download_joinquant_files():
    global jq

    jq.fetch_file('up_down.csv', 'r_up_down.csv')
    jq.fetch_file('weekdayly_returns.csv', 'r_weekdayly_returns.csv')
    jq.fetch_file('weekly_returns.csv', 'r_weekly_returns.csv')
    jq.fetch_file('monthly_returns.csv', 'r_monthly_returns.csv')

def generate_blog_source():
    blog_source_path = '{}r_{}.md'.format(blog_post_path, today_str)

    blog_generator = HexoGenerator.HexoGenerator(blog_source_path, '每日提示-{}'.format(today_str), tags=['每日提示'])
    generate_blog_up_down(blog_generator)

    blog_generator.write()

def generate_montly_returns_blog_source():
    blog_source_path = '{}r_{}.md'.format(blog_post_path, 'MonthlyReturns')

    blog_generator = HexoGenerator.HexoGenerator(blog_source_path, '主要指数月回报统计'.format(today_str), tags=['数据统计'])
    generate_blog_monthly_stat(blog_generator)

    blog_generator.write()

def generate_weekdayly_returns_blog_source():
    blog_source_path = '{}r_{}.md'.format(blog_post_path, 'WeekdaylyReturns')

    blog_generator = HexoGenerator.HexoGenerator(blog_source_path, '主要指数周内回报统计'.format(today_str), tags=['数据统计'])
    generate_blog_weekdayly_stat(blog_generator)

    blog_generator.write()

def generate_weekly_returns_blog_source():
    blog_source_path = '{}r_{}.md'.format(blog_post_path, 'WeeklyReturns')

    blog_generator = HexoGenerator.HexoGenerator(blog_source_path, '主要指数周回报统计'.format(today_str), tags=['数据统计'])
    generate_blog_weekly_stat(blog_generator)

    blog_generator.write()

def generate_blog_up_down(generator):
    generator.h3('新低新高')
    data_path = os.path.join(script_dir, 'data/r_up_down.csv')

    df = pd.read_csv(data_path, index_col='date', parse_dates=True)
    generator.line('五日内创一个月新低比例{:.2f}%, 五日内创一个月新高比例{:.2f}%。股价低于一个月前股价95%比例{:.2f}%，股价高于一个前股价95%比例{:.2f}。'
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

    figure_name = ('r_up_down_{}.png').format(today_str)
    figure_path = '{}{}'.format(blog_upload_absolute_path, figure_name)

    plt.savefig(figure_path, bbox_inches='tight')

    generator.img('{}{}'.format(blog_upload_relative_path, figure_name))

def generate_blog_weekdayly_stat(generator):
    data_path = os.path.join(script_dir, 'data/r_weekdayly_returns.csv')

    total_df = pd.read_csv(data_path)
    dfs = np.array_split(total_df, len(total_df.index) / 5 )   # split whole dataframe into dataframes of individual index
    for df in dfs:
        generator.h3(df['index_name'].iat[0])
        df['weekday'] = df['weekday'] + 1
        generator.data_frame(df[['weekday', 'count', 'mean', 'min', 'max', 'positive_pct']],
            headers=[
                '周几', '样本数量', '平均', '最小值', '最大值', '正回报比率'
            ])

def generate_blog_weekly_stat(generator):
    data_path = os.path.join(script_dir, 'data/r_weekly_returns.csv')

    total_df = pd.read_csv(data_path)
    dfs = np.array_split(total_df, len(total_df.index) / 53 )   # split whole dataframe into dataframes of individual index
    for df in dfs:
        generator.h3(df['index_name'].iat[0])
        df['week'] = df['week']
        generator.data_frame(df[['week', 'count', 'mean', 'min', 'max', 'positive_pct']],
            headers=[
                '周', '样本数量', '平均', '最小值', '最大值', '正回报比率'
            ])

def generate_blog_monthly_stat(generator):
    data_path = os.path.join(script_dir, 'data/r_monthly_returns.csv')

    total_df = pd.read_csv(data_path)
    dfs = np.array_split(total_df, len(total_df.index) / 12 )   # split whole dataframe into dataframes of individual index
    for df in dfs:
        generator.h3(df['index_name'].iat[0])
        generator.data_frame(df[['month', 'count', 'mean', 'min', 'max', 'positive_pct']],
            headers=[
                '月份', '样本数量', '平均', '最小值', '最大值', '正回报比率'
            ])


def hexo_generate():
    is_windows = utils.is_windows()

    subprocess.call(shlex.split('hexo generate --cwd {}'.format(blog_path)), shell = is_windows)
    if is_windows:
        subprocess.call(shlex.split('hexo deploy --cwd {}'.format(blog_path)), shell = is_windows)

def check_join_quant_data_time_stamp():
    global jq

    timestamp = jq.fetch_file('timestamp.txt', None)

    return timestamp.decode('utf-8') == datetime.datetime.now().date().strftime('%Y-%m-%d')

login_jointquant()

if check_join_quant_data_time_stamp():
    print('here')
    download_joinquant_files()

    if datetime.datetime.now().date().day % 5 == 0:
        generate_weekdayly_returns_blog_source()
        generate_montly_returns_blog_source()
        generate_weekly_returns_blog_source()

    generate_blog_source()
    hexo_generate()
