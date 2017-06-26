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
with open(data_file_path, 'w') as w:
    for portfolio_id, holdings in xq.get_all_portfolio():
        for holding in holdings:
            w.write('{},{},{},{},{}\n'.format(portfolio_id, holding.code,
                                              holding.name, holding.industry,
                                              holding.weight))
# xq.get_portfolio('')
