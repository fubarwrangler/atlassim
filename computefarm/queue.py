#!/usr/bin/python

import logging
from computefarm import IDLE, RUNNING

log = logging.getLogger('sim')


class JobQueue(list):
    """ A list of job-objects with some methods for querying the queue based on
        properties of the jobs therein
    """

    def add_job(self, jobobj):
        jobobj.queue = self
        log.debug("Added job %s to queue", str(jobobj))
        self.append(jobobj)

    def __str__(self):
        return "\n".join([x.long() for x in self])

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
