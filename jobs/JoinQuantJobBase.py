import jobs.JobBase as j

class JoinQuantJobBase(j.JobBase):
    def __init__(self, jq):
        self.jq = jq
