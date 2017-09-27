import os
import datetime
import json
import argparse
import utils
import JoinQuant
from jobs import *

script_dir = os.path.dirname(__file__)
parser = argparse.ArgumentParser()

generate_parser = parser.add_argument('-g', '--generate', default='')
args = parser.parse_args()
if args.generate == 'all':
    generate_all = True
else:
    generate_all = False

now = datetime.datetime.now()
today_str = now.strftime("%Y%m%d")

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
blog_page_path = blog_source_path
blog_post_path = os.path.join(blog_source_path, '_posts/')
blog_upload_relative_path = os.path.join('/uploads/')
blog_upload_absolute_path = os.path.join(blog_source_path, blog_upload_relative_path[1:])

def login_jointquant():
    joint_quant_config_file_path = os.path.join(script_dir, 'config/JoinQuant.json')
    with open(joint_quant_config_file_path, 'r') as f:
        join_quant_config = json.load(f)

    jq = JoinQuant.JoinQuant(join_quant_config)
    succeed, reason = jq.login()
    if not succeed:
        raise Exception("login failed: " + reason)

    return jq

def check_join_quant_data_time_stamp(jq):
    timestamp = jq.fetch_file('timestamp.txt', None)

    return timestamp.decode('utf-8') == now.strftime('%Y-%m-%d')

def generate_everyday_blog_post():
    section_generators = [
        HistoryPostSectionGenerator.HistoryPostSectionGenerator(
            data_file_path = os.path.join(script_dir, 'data/')),
        UpDownPostSectionGenerator.UpDownPostSectionGenerator(
            data_file_path = os.path.join(script_dir, 'data/r_up_down.csv'),
            blog_upload_relative_path = blog_upload_relative_path,
            blog_upload_absolute_path = blog_upload_absolute_path)
    ]

    EverydayPostJob.EverydayPostJob(
        post_path = '{}r_{}.md'.format(blog_post_path, today_str),
        section_generators = section_generators
    ).run()

jq = login_jointquant()

if generate_all or check_join_quant_data_time_stamp(jq):
    # JoinQuantDownloadFilesJob.JoinQuantDownloadFilesJob(jq).run()

    if generate_all or now.date().day % 5 == 0 :
        JoinQuantWeekdaylyStatJob.JoinQuantWeekdaylyStatJob(
            post_path = os.path.join(blog_page_path, 'r_WeekdaylyReturns/', 'index.md'),
            data_file_path = os.path.join(script_dir, 'data/r_weekdayly_returns.csv')).run()
        JoinQuantWeeklyStatJob.JoinQuantWeeklyStatJob(
            post_path = os.path.join(blog_page_path, 'r_WeeklyReturns/', 'index.md'),
            data_file_path = os.path.join(script_dir, 'data/r_weekly_returns.csv')).run()
        JoinQuantMonthlyStatJob.JoinQuantMonthlyStatJob(
            post_path = os.path.join(blog_page_path, 'r_MonthlyReturns/', 'index.md'),
            data_file_path = os.path.join(script_dir, 'data/r_monthly_returns.csv')).run()
        JoinQuantMonthweeklyStatJob.JoinQuantMonthweeklyStatJob(
            post_path = os.path.join(blog_page_path, 'r_MonthweeklyReturns/', 'index.md'),
            data_file_path = os.path.join(script_dir, 'data/r_monthweekly_returns.csv')).run()
        JoinQuantQuarterlyStatJob.JoinQuantQuarterlyStatJob(
            post_path = os.path.join(blog_page_path, 'r_QuarterlyReturns/', 'index.md'),
            data_file_path = os.path.join(script_dir, 'data/r_quarterly_returns.csv')).run()

    generate_everyday_blog_post()

    HexoGeneratorJob.HexoGeneratorJob(blog_path).run()

