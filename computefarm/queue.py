#!/usr/bin/python


class JobQueue(object):

    def __init__(self):
        self._q = list()

    def add_job(self, jobobj):
        jobobj.queue = self._q
        self._q.append(jobobj)

    def __getitem__(self, n):
        return self._q[n]

    def __str__(self):
        return "\n".join([x.long() for x in self._q])

    def match_jobs(self, query):

        def check_job(job, query):
            for k, v in query.iteritems():
                if getattr(job, k) != v:
                    return False
            return True

        return (x for x in self if check_job(x, query))

    def __len__(self):
        return len(self._q)

    def __iter__(self):
        return iter(self._q)
