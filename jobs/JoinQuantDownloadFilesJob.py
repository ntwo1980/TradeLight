import jobs.JoinQuantJobBase as j

class JoinQuantDownloadFilesJob(j.JoinQuantJobBase):
    def run(self):
        self.jq.fetch_file('up_down.csv', 'r_up_down.csv')
        self.jq.fetch_file('weekdayly_returns.csv', 'r_weekdayly_returns.csv')
        self.jq.fetch_file('weekly_returns.csv', 'r_weekly_returns.csv')
        self.jq.fetch_file('monthly_returns.csv', 'r_monthly_returns.csv')
