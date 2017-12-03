import os
import sys
import datetime
import json
import argparse
import utils
import pandas as pd
import JoinQuant
import XueQiu
import SW
from jobs import *

is_windows = utils.is_windows()
script_dir = os.path.dirname(__file__)
parser = argparse.ArgumentParser()

generate_parser = parser.add_argument('-t', '--type', default='jxs', nargs='?')
generate_parser = parser.add_argument('-l', '--local', default='', nargs='?')
args = parser.parse_args()

generate_xueqiu = False
generate_joinquant = False
generate_sw = False
only_local_file = False

if 'x' in args.type:
    generate_xueqiu = True

if 'j' in args.type:
    generate_joinquant = True

if 's' in args.type:
    generate_sw = True

if args.local is None:
    only_local_file = True

now = datetime.datetime.now()
today_str = now.strftime("%Y%m%d")
# today_str = now.strftime("20170929")

app_config_file_path = os.path.join(script_dir, 'config/app.json')
with open(app_config_file_path, 'r') as f:
    app_config = json.load(f)
blog_path = app_config['blogs_path']
blog_source_path = os.path.join(blog_path, 'source/')
blog_public_path = os.path.join(blog_path, 'public/')
blog_page_path = blog_source_path
blog_post_path = os.path.join(blog_source_path, '_posts/')
blog_upload_relative_path = os.path.join('/uploads/')
blog_upload_absolute_path = os.path.join(blog_source_path, blog_upload_relative_path[1:])
blog_public_upload_absolute_path = os.path.join(blog_public_path, blog_upload_relative_path[1:])
blog_public_upload_stocks_absolute_path = os.path.join(blog_public_path, blog_upload_relative_path[1:], 'r_stocks')
sw_files = [
        '801001', '801002', '801003', '801005', '801010', '801020', '801030', '801040', '801050', '801080',
        '801110', '801120', '801130', '801140', '801150', '801160', '801170', '801180',
        '801200', '801210', '801230', '801250', '801260', '801270', '801280', '801300',
        '801710', '801720', '801730', '801740', '801750', '801760', '801770', '801780', '801790',
        '801811', '801812', '801813', '801821', '801822', '801823', '801831', '801832', '801833', '801853',
        '801880', '801890'
        ]

if not os.path.exists(blog_public_upload_stocks_absolute_path):
    os.makedirs(blog_public_upload_stocks_absolute_path)

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

    succeed, reason = xq.login()

    if not succeed:
        raise Exception("xueqiu login failed: " + reason)

    return xq


def check_join_quant_data_time_stamp(jq):
    timestamp = jq.fetch_file('timestamp.txt', None)

    return timestamp.decode('utf-8') == now.strftime('%Y-%m-%d')

if generate_joinquant:
    if not only_local_file:
        jq = login_jointquant()

        if check_join_quant_data_time_stamp(jq):
            JoinQuantDownloadFilesJob.JoinQuantDownloadFilesJob(jq).run()
            #StocksStatJob.StocksStatJob(os.path.join(script_dir, 'data/r_stocks.csv')).run()

    StocksStatJob.StocksStatJob(
        post_path = os.path.join(blog_page_path, 'r_Stocks/', 'index.md'),
        stocks_file_path = os.path.join(script_dir, 'data/r_stocks.csv')).run()

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
    JoinQuantStocksJsonDataJob.JoinQuantStocksJsonDataJob(
        json_dir = blog_public_upload_stocks_absolute_path,
        data_file_path = os.path.join(script_dir, 'data/r_stocks.csv')).run()

if generate_xueqiu and not only_local_file:
    xq = login_xueqiu()

    portfolios_csv_path = os.path.join(script_dir, 'data/r_xq_portfolios.csv')
    XueQiuFetchPortfoliosJob.XueQiuFetchPortfoliosJob(xq, portfolios_csv_path).run()

    holdings_csv_path = os.path.join(script_dir, 'data/r_xq_holdings_{}.csv'.format(today_str))
    portfolios = xq.get_portfolios_from_csv(portfolios_csv_path)
    XueQiuFetchHoldingsJob.XueQiuFetchHoldingsJob(xq, holdings_csv_path, portfolios['code']).run()

    watches_csv_path = os.path.join(script_dir, 'data/r_xq_watches.csv')
    XueQiuFetchWatchesJob.XueQiuFetchWatchesJob(xq, watches_csv_path).run()

if generate_sw and not only_local_file:
    sw = SW.SW()
    succeed, reason = sw.init()
    if not succeed:
        raise Exception("sw init failed: " + reason)

    SWDownloadFilesJob.SWDownloadFilesJob(sw, sw_files, data_file_path = os.path.join(script_dir, 'data/')).run()

if generate_joinquant or generate_sw:
    section_generators = [
        HistoryPostSectionGenerator.HistoryPostSectionGenerator(
            data_file_path = os.path.join(script_dir, 'data/')),
        UpDownPostSectionGenerator.UpDownPostSectionGenerator(
            data_file_path = os.path.join(script_dir, 'data/r_up_down.csv'),
            blog_upload_relative_path = blog_upload_relative_path,
            blog_upload_absolute_path = blog_upload_absolute_path),
        AboveMaPostSectionGenerator.AboveMaPostSectionGenerator(
            data_file_path = os.path.join(script_dir, 'data/r_above_ma.csv'),
            blog_upload_relative_path = blog_upload_relative_path,
            blog_upload_absolute_path = blog_upload_absolute_path),
        SWStatPostSectionGenerator.SWStatPostSectionGenerator(
            data_file_path = os.path.join(script_dir, 'data/'),
            blog_upload_relative_path = blog_upload_relative_path,
            blog_upload_absolute_path = blog_upload_absolute_path)
    ]
    MarketStatJob.MarketStatJob(
        post_path = os.path.join(blog_page_path, 'r_Market/', 'index.md'),
        section_generators = section_generators
    ).run()

if generate_joinquant or generate_xueqiu or generate_sw:
    # generate_everyday_blog_post()

    # HexoGeneratorJob.HexoGeneratorJob(blog_path, is_windows).run()
    HexoGeneratorJob.HexoGeneratorJob(blog_path, False).run()
