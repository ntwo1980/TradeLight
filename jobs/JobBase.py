import datatime

class JobBase:
    def run():
        pass

    @staticmethod
    def get_today_str(x):
        now = datetime.datetime.now()
        return now.strftime("%Y-%m-%d")
