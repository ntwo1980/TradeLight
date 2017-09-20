import os
import datetime as dt
import unittest
import pandas as pd
import tushare as ts

script_dir = os.path.dirname(__file__)
data_path = os.path.join(script_dir, 'data/')

def save_shibor_data():
    df = fetch_shibor_data()

    if df is None:
        return

    shibor_file_path = os.path.join(data_path, 'shibor.csv')

    if not os.path.isfile(shibor_file_path):
        df.to_csv(shibor_file_path)
    else:
        existing_df = pd.read_csv(shibor_file_path, index_col='date', parse_dates=True)

        not_existing_df = df[~df.index.isin(existing_df.index)]
        pd.concat([not_existing_df, existing_df]).to_csv(shibor_file_path)

def fetch_shibor_data():
    df = ts.shibor_data()

    if df is None:
        return None

    df.sort_values('date', ascending=False, inplace=True)
    df.set_index('date', inplace=True)

    return df

def test():
    unittest.main()

class TuTest(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        pass

    @classmethod
    def tearDownClass(self):
        pass

    def test_tu(self):
        save_shibor_data()

if __name__ == '__main__':
    test()
