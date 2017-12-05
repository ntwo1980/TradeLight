import datetime
import os
import glob
import numpy as np
import pandas as pd
import jobs.JobBase as j
import HexoGenerator

class StocksPBPEStatJob(j.JobBase):
    def __init__(self, data_path, stat_output_path):
        self.data_path = data_path
        self.stat_output_path = stat_output_path

    def run(self):
        files = glob.glob(os.path.join(self.data_path, 'r_zz_*.csv'))

        print(len(files))
        for f in files:
            print(f)

