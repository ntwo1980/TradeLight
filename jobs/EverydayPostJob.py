import datetime
import numpy as np
import pandas as pd
import jobs.BlogPostGenerateJobBase as b
import HexoGenerator

class EverydayPostJob(b.BlogPostGenerateJobBase):
    def __init__(self, post_path, section_generators=None):
        b.BlogPostGenerateJobBase.__init__(self, post_path)
        self.section_generators = section_generators if isinstance(section_generators, list) else []

    def run(self):
        now = datetime.datetime.now()
        today_str = now.strftime("%Y%m%d")

        blog_generator = HexoGenerator.HexoGenerator(self.post_path, '每日提示-{}'.format(today_str), tags=['每日提示'])
        for sg in self.section_generators:
            sg.generate(blog_generator)

        blog_generator.write()
