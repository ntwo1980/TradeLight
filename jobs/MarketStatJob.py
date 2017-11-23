import datetime
import numpy as np
import pandas as pd
import jobs.JobBase as j
import HexoGenerator

class MarketStatJob(j.JobBase):
    def __init__(self, post_path, section_generators=None):
        b.BlogPostGenerateJobBase.__init__(self, post_path)
        self.section_generators = section_generators if isinstance(section_generators, list) else []

    def run(self):
        now = datetime.datetime.now()
        today_str = now.strftime("%Y%m%d")

        blog_generator = HexoGenerator.HexoGenerator(self.post_path, '市场统计', tags=['数据统计'])
        for i, sg in enumerate(self.section_generators):
            if i == 1:
                blog_generator.read_more()

            sg.generate(blog_generator)

        blog_generator.write()
