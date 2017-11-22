import jobs.JobBase as j

class SWDownloadFilesJob(j.JobBase):
    def __init__(self, sw, download_files):
        self.sw = sw
        self.download_files = download_files

    def run(self):
        for f in self.download_files:
            self.sw.fetch_file(f, 'r_sw_' + f)
