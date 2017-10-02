import datetime
import numpy as np
import pandas as pd
import jobs.XueQiuJobBase as j

class XueQiuFetchWatchesJob(j.XueQiuJobBase):
    def __init__(self, xq, data_file_path):
        j.XueQiuJobBase.__init__(self, xq)
        self.data_file_path = data_file_path

    def run(self):
        watches = self.xq.fetch_my_watches()
        watches.to_csv(self.data_file_path, encoding='utf-8')
