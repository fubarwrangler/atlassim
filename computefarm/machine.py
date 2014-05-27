#!/usr/bin/python

import logging
import itertools

from computefarm import COMPLETED, RUNNING

log = logging.getLogger('sim')


class Machine(object):
    """ Class representing one machine in a compute cluster """

    _ids = itertools.count(0)

    def __init__(self, cpus=24, memory=None, name=None):

        self.name = name if name else "node%04d" % self._ids.next()

        self.cpus = cpus
        self.totalcpus = cpus
        self.memory = memory if memory is not None else 1000 * 2 * cpus
        self.totalmemory = self.memory
        self.num_jobs = 0.0

        self._jobs = list()

    def __iter__(self):
        return iter(self._jobs)

    def start_job(self, job):
        self.cpus -= job.cpus
        self.memory -= job.memory

        job.slotid = len(self._jobs)
        job.state = RUNNING
        job.current_node = self.name

        self._jobs.append(job)
        self.num_jobs += 1

    def end_job(self, job):
        self.cpus += job.cpus
        self.memory += job.memory
        self._jobs.remove(job)
        self.num_jobs -= 1

    def advance_time(self, step):
        for job in self._jobs:
            job.advance_time(step)
            if job.state == COMPLETED:
                log.info("Job %s completed on %s", job, self)
                self.end_job(job)

    def __str__(self):

        return "%s (%d jobs) (%d/%d cpu) (%d/%d ram)" % \
               (self.name, len(self._jobs), self.cpus, self.totalcpus,
                self.memory, self.totalmemory)

    def long(self):
        s = "%s  (%d jobs) CPUs %2d (%2d) - RAM (%5d) %5d" % \
            (self.name, len(self._jobs), self.totalcpus - self.cpus, self.totalcpus,
             self.totalmemory - self.memory, self.totalmemory)
        if len(self._jobs) > 0:
            j = "\n    ".join(str(x) for x in self._jobs)
            return s + "\n    " + j
        else:
            return s
