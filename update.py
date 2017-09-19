import os
import json
import XueQiu
import datetime

now = datetime.datetime.now()
today_str = now.strftime("%Y%m%d")
script_dir = os.path.dirname(__file__)
config_file_path = os.path.join(script_dir, 'config/XueQiu.json')
with open(config_file_path, 'r') as f:
    config = json.load(f)

xq = XueQiu.XueQiu(config)

xq.login()
data_file_path = os.path.join(script_dir, 'data/XueQiu_{}.csv'.format(today_str))


all_holdings = xq.fetch_all_portfolio_positions()
all_holdings.to_csv(data_file_path)
