import os
import pandas as pd
import matplotlib.pyplot as plt
import jobs.PostSectionGenerator as p
from scipy import stats

class IndexesCompareJob(p.PostSectionGenerator):
    def __init__(self, index_closes_file_path, index_names_file_path, blog_upload_relative_path, blog_upload_absolute_path):
        self.index_closes_file_path = index_closes_file_path
        self.index_names_file_path = index_names_file_path
        self.blog_upload_relative_path = blog_upload_relative_path
        self.blog_upload_absolute_path = blog_upload_absolute_path

    def generate(self, blog_generator):
        blog_generator.h3('指数对比')

        df_names = pd.read_csv(
            self.index_names_file_path,
            header=True,
            infer_datetime_format=True)

        df_closes = pd.read_csv(
            self.index_closes_file_path,
            header=True, parse_dates=['date'],
            infer_datetime_format=True)
