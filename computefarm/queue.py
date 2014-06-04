#!/usr/bin/python

import logging
from computefarm import IDLE, RUNNING

log = logging.getLogger('sim')


class JobQueue(object):
    """ A list of job-objects with some methods for querying the queue based on
        properties of the jobs therein
    """

    def __init__(self):
        self._q = list()

    def add_job(self, jobobj):
        jobobj.queue = self._q
        log.debug("Added job %s to queue", str(jobobj))
        self._q.append(jobobj)

    def __getitem__(self, n):
        return self._q[n]

    def __str__(self):
        return "\n".join([x.long() for x in self._q])

    def match_jobs(self, query):
        """ Return an iterator of all job objects where the properties match the
            values represented in @query.

            @query is a mapping of {'key': value}, like
                {'group': 'short', 'state': IDLE}
            which would return all idle short jobs
        """

        def check_job(job, query):
            for k, v in query.iteritems():
                if getattr(job, k) != v:
                    return False
            return True

        return (x for x in self if check_job(x, query))

    def get_group_idle(self, group):
        return len([x for x in self if x.state == IDLE and x.group == group])

    def get_group_running(self, group):
        return len([x for x in self if x.state == RUNNING and x.group == group])

    def __len__(self):
        return len(self._q)

    def __iter__(self):
        return iter(self._q)
