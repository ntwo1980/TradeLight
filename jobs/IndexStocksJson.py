import os
import datetime
import numpy as np
import pandas as pd
import json
import jobs.JobBase as j

class IndexStocksJson(j.JobBase):
    def __init__(self, json_dir, index_file_path):
        self.json_dir = json_dir
        self.index_file_path = index_file_path

    def run(self):
        df = pd.read_csv(self.index_file_path)
        index_json = dict()

        for index, group in df.groupby('index'):
            data = dict()
            data['name'] = group['index_name'].iloc[0]
            data['stocks'] = list(group['stock'].str[:6])

            index_json[index[0:6]] = data

        print(os.path.join(self.json_dir, 'index_stocks.json'))
        with open(os.path.join(self.json_dir, 'index_stocks.json'), 'w') as f:
            json.dump(index_json, f)
