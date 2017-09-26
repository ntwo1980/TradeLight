import os
import datetime
import json
import JoinQuant
import jobs.JoinQuantDownloadFilesJob
import jobs.JoinQuantWeekdaylyStatJob
import jobs.JoinQuantWeeklyStatJob
import jobs.JoinQuantMonthlyStatJob

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

    return timestamp.decode('utf-8') == datetime.datetime.now().date().strftime('%Y-%m-%d')


jq = login_jointquant()

if check_join_quant_data_time_stamp(jq):
    jobs.JoinQuantDownloadFilesJob.JoinQuantDownloadFilesJob(jq).run()

    if datetime.datetime.now().date().day % 5 == 0:
        jobs.JoinQuantWeekdaylyStatJob.JoinQuantWeekdaylyStatJob(jq,
            post_path = '{}r_{}.md'.format(blog_post_path, 'WeekdaylyReturns'),
            data_file_path = os.path.join(script_dir, 'data/r_weekdayly_returns.csv')).run()
        jobs.JoinQuantWeeklyStatJob.JoinQuantWeeklyStatJob(jq,
            post_path = '{}r_{}.md'.format(blog_post_path, 'WeeklyReturns'),
            data_file_path = os.path.join(script_dir, 'data/r_weekly_returns.csv')).run()
        jobs.JoinQuantMonthlyStatJob.JoinQuantMonthlyStatJob(jq,
            post_path = '{}r_{}.md'.format(blog_post_path, 'MonthlyReturns'),
            data_file_path = os.path.join(script_dir, 'data/r_monthly_returns.csv')).run()

    generate_blog_source()
    hexo_generate()

