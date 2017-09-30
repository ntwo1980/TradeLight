import os
import sys
import datetime
import json
import argparse
import utils
import JoinQuant
import XueQiu
from jobs import *

script_dir = os.path.dirname(__file__)
parser = argparse.ArgumentParser()

generate_parser = parser.add_argument('-t', '--type', default='jx', nargs='?')
args = parser.parse_args()

generate_xueqiu = False
generate_joinquant = False

if 'x' in args.type:
    generate_xueqiu = True

if 'j' in args.type:
    generate_joinquant = True

now = datetime.datetime.now()
today_str = now.strftime("%Y%m%d")

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
        raise Exception("joinquant login failed: " + reason)

    return jq

def login_xueqiu():
    xueqiu_config_file_path = os.path.join(script_dir, 'config/XueQiu.json')
    with open(xueqiu_config_file_path, 'r') as f:
        xueqiu_config = json.load(f)

    xq = XueQiu.XueQiu(xueqiu_config)

    xq.login()
    succeed, reason = xq.login()

    if not succeed:
        raise Exception("xueqiu login failed: " + reason)

    return xq


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
            blog_upload_absolute_path = blog_upload_absolute_path),
        XueQiuStatPostSectionGenerator.XueQiuStatPostSectionGenerator(
            holdings_data_file_path=os.path.join(script_dir, 'data/r_xq_holdings_{}.csv'.format(today_str)))
    ]

    EverydayPostJob.EverydayPostJob(
        post_path = '{}r_{}.md'.format(blog_post_path, today_str),
        section_generators = section_generators
    ).run()


if generate_joinquant:
    jq = login_jointquant()

    if check_join_quant_data_time_stamp(jq):
        JoinQuantDownloadFilesJob.JoinQuantDownloadFilesJob(jq).run()

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

if generate_xueqiu:
    xq = login_xueqiu()

    portfolios_csv_path = os.path.join(script_dir, 'data/r_xq_portfolios.csv')
    XueQiuFetchPortfoliosJob.XueQiuFetchPortfoliosJob(xq, portfolios_csv_path).run()

    holdings_csv_path = os.path.join(script_dir, 'data/r_xq_holdings.csv')
    portfolios = xq.get_portfolios_from_csv(portfolios_csv_path)
    XueQiuFetchHoldingsJob.XueQiuFetchHoldingsJob(xq, holdings_csv_path, portfolios['code']).run()

if generate_joinquant or generate_xueqiu:
        generate_everyday_blog_post()

        HexoGeneratorJob.HexoGeneratorJob(blog_path).run()

