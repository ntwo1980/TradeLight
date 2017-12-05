import datetime
import numpy as np
import pandas as pd
import jobs.JobBase as j
import HexoGenerator

class StocksPBPEStatJob(j.JobBase):
    def __init__(self, data_path, stat_output_path):
        self.data_path = data_path
        self.stat_output_path = stat_output_path

    def run(self):
        pass
