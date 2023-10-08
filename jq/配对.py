import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import talib
import mytrade as t
import dateutil
import datetime as dt
import jqlib.technical_analysis as ta
import matplotlib.pyplot as plt
from dateutil.relativedelta import *
try:
    from kuanke.user_space_api import *
except:
    pass
from jqdata import *

pd.set_option('display.notebook_repr_html', False)
pd.set_option('display.max_rows', 9999)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)
pd.set_option('precision', 3)
pd.set_option('display.float_format', '{:.2f}'.format)

today = dt.date.today()


stocks = ['513050.XSHG',
        '159605.XSHE'
         ]


yesterday_str = (today - dt.timedelta(1)).strftime('%Y-%m-%d')
df = get_price(stocks, end_date=yesterday_str, frequency='daily', fields='close', skip_paused=False, fq='pre', count=400)['close']
#ma = pd.rolling_mean(df, 10)

#(ma.ix[:,1] / ma.ix[:,0]).plot()

(df.ix[:,1] / df.ix[:,0]).plot()
plt.show()
