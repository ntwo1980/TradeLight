import datetime

class JobBase:
    def run():
        pass

    @staticmethod
    def get_today_str():
        now = datetime.datetime.now()
        return now.strftime("%Y-%m-%d")
