import os
import json
import datetime
import subprocess
import shlex
import pandas as pd
import matplotlib.pyplot as plt
import XueQiu
import JoinQuant
import HexoGenerator

now = datetime.datetime.now()
today_str = now.strftime("%Y%m%d")
script_dir = os.path.dirname(__file__)
''''
config_file_path = os.path.join(script_dir, 'config/XueQiu.json')
with open(config_file_path, 'r') as f:
    config = json.load(f)

xq = XueQiu.XueQiu(config)

xq.login()
data_file_path = os.path.join(script_dir, 'data/XueQiu_{}.csv'.format(today_str))


all_holdings = xq.fetch_all_portfolio_positions()
all_holdings.to_csv(data_file_path)
'''

blog_path = '/home/luke/blogs/'
blog_source_path = os.path.join(blog_path, 'source/')
blog_post_path = os.path.join(blog_source_path, '_posts/')
blog_upload_relative_path = os.path.join('/upload/')
blog_upload_absolute_path = os.path.join(blog_source_path, blog_upload_relative_path)

def generate_blog_source():
    blog_source_path = '{}r_{}.md'.format(blog_post_path, today_str)

    blog_generator = HexoGenerator.HexoGenerator(blog_source_path, '每日提示-{}'.format(today_str), tags=['每日提示'])
    generate_blog_up_down(blog_generator)

    blog_generator.write()

def generate_blog_up_down(generator):
    generator.h3('新低新高')
    data_path = os.path.join(script_dir, 'data/r_up_down.csv')

    df = pd.read_csv(data_path, index_col='date', parse_dates=True)
    generator.line('五日内创一个月新低比例{:.2f}%, 五日内创一个月新高比例{:.2f}%。股价低于一个月前股价95%比例{:.2f}%，股价高于一个前股价95%比例{:.2f}。'
                   .format(df['low'][-1], df['high'][-1], df['down'][-1], df['up'][-1]))

    fig, axes = plt.subplots(3, 1, figsize=(16, 18))

    ax1 = axes[0]
    ax1.plot(df.index, low_pct, label='low pct')
    ax1.plot(df.index, high_pct, label='high pct')
    ax1.legend(loc='upper left')
    ax1.set_ylabel('low/high pct')
    ax3= ax1.twinx()
    ax3.plot(df.index,index_close , 'y')

    ax2 = axes[1]
    ax2.plot(df.index, up_pct, label='up pct')
    ax2.plot(df.index, down_pct, label='down pct')
    ax2.legend(loc='upper left')
    ax2.set_ylabel('up/down pct')
    ax4= ax2.twinx()
    ax4.plot(df.index,index_close , 'y')

    figure_name = (r_up_down_{}.png).format(today_str)
    figure_path = '{}{}'.format(blog_upload_absolute_path, figure_name)

    plt.savefig('figure_path', bbox_inches='tight')

    generator.img('{}{}'.format(figure_name))
    #generator.data_frame(df)

def hexo_generate():
    subprocess.call(shlex.split('hexo generate --cwd {}'.format(blog_path)))

generate_blog_source()

hexo_generate()
