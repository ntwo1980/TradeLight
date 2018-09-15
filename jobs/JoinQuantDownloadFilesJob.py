import jobs.JoinQuantJobBase as j

class JoinQuantDownloadFilesJob(j.JoinQuantJobBase):
    def run(self):
        self.jq.fetch_file('up_down.csv', 'r_up_down.csv')
        self.jq.fetch_file('above_ma.csv', 'r_above_ma.csv')
        self.jq.fetch_file('weekdayly_returns.csv', 'r_weekdayly_returns.csv')
        self.jq.fetch_file('weekly_returns.csv', 'r_weekly_returns.csv')
        self.jq.fetch_file('quarterly_returns.csv', 'r_quarterly_returns.csv')
        self.jq.fetch_file('monthly_returns.csv', 'r_monthly_returns.csv')
        self.jq.fetch_file('monthweekly_returns.csv', 'r_monthweekly_returns.csv')
        self.jq.fetch_file('stocks.csv', 'r_stocks.csv')
        self.jq.fetch_file('stocks_closes.csv', 'r_stocks_closes.csv')
        self.jq.fetch_file('index_stocks.csv', 'r_index_stocks.csv')
        self.jq.fetch_file('securities.csv', 'r_securities.csv')
        self.jq.fetch_file('indexes.csv', 'r_indexes.csv')
        self.jq.fetch_file('future_list.csv', 'r_future_list.csv')
        self.jq.fetch_file('futures.csv', 'r_futures.csv')
        self.jq.fetch_file('futures_atr.json', 'r_futures_atr.json')
