import os
import json
import datetime
import subprocess
import shlex
import pandas as pd
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
blog_upload_path = os.path.join(blog_source_path, 'upload/')

def generate_blog_source():
    blog_source_path = '{}r_{}.md'.format(blog_post_path, today_str)

    blog_generator = HexoGenerator.HexoGenerator(blog_source_path, '每日提示-{}'.format(today_str), tags=['每日提示'])
    generate_blog_up_down(blog_generator)

    blog_generator.write()

def generate_blog_up_down(generator):
    generator.h3('新高新低')
    data_path = os.path.join(script_dir, 'data/r_up_down.csv')

    df = pd.read_csv(data_path, index_col='date', parse_dates=True)
    generator.line('五日内创一个月新低比例{:.2f}, 五日内创一个月新高比例{:.2f}。股价低于一个月前股价95%比例{:.2f}，股价高于一个前股价105%比例{:.2f}。'
                   .format(df['low'][-1], df['high'][-1], df['down'][-1], df['up'][-1]))
    #generator.data_frame(df)

def hexo_generate():
    subprocess.call(shlex.split('hexo generate --cwd {}'.format(blog_path)))

generate_blog_source()

hexo_generate()
