import datetime
import numpy as np
import pandas as pd
import jobs.JobBase as j
import HexoGenerator

class IndexStocksJson(j.JobBase):
    def __init__(self, json_dir, index_file_path):
        self.json_dir = json_dir
        self.index_file_path = index_file_path

    def run(self):
        df = pd.read_csv(self.index_file_path)
        print(df)

