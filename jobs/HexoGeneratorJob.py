import utils
import subprocess
import shlex
import jobs.JobBase as j

class HexoGeneratorJob(j.JobBase):
    def __init__(self, blog_path, deploy=False):
        self.blog_path = blog_path
        self.deploy = deploy

    def run(self):
        is_windows = utils.is_windows()

        subprocess.call(shlex.split('hexo generate --cwd {}'.format(self.blog_path)), shell = is_windows)
        if self.deploy:
            subprocess.call(shlex.split('hexo deploy --cwd {}'.format(self.blog_path)), shell = is_windows)
