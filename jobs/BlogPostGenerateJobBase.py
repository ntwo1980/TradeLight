import jobs.JobBase as j

class BlogPostGenerateJobBase(j.JobBase):
    def __init__(self, post_path):
        self.post_path = post_path
