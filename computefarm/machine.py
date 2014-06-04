#!/usr/bin/python

import logging
import itertools

from computefarm import COMPLETED, RUNNING

log = logging.getLogger('sim')


class Machine(list):
    """ Class representing one machine in a compute cluster """

    _ids = itertools.count(0)

    __slots__ = ['name', 'cpus', 'totalcpus', 'memory', 'totalmemory',
                 'num_jobs']

    def __init__(self, cpus=24, memory=None, name=None):
        """ Machines have two resources, CPUs, and RAM """

        self.name = name if name else "node%04d" % self._ids.next()

        self.cpus = cpus
        self.totalcpus = cpus

        # Ram defaults to 2Gb * Cores just like in our farm
        self.memory = memory if memory is not None else 1000 * 2 * cpus
        self.totalmemory = self.memory
        self.num_jobs = 0.0

    def start_job(self, job):
        """ Start a job by deducting the job's requested resources form this
            machine's available resources and setting the job's machine pointer
        """

        if self.cpus - job.cpus < 0 or self.memory - job.memory < 0:
            raise Exception("Bad match, machine %s has too few resources to run %s" % (self, job))

        self.cpus -= job.cpus
        self.memory -= job.memory

        job.slotid = len(self)
        job.state = RUNNING
        job.current_node = self.name

        self.append(job)
        self.num_jobs += 1

    def end_job(self, job):
        """ Finish a job by recovering the resources used by the job """

        self.cpus += job.cpus
        self.memory += job.memory
        self.remove(job)
        self.num_jobs -= 1

    def advance_time(self, step):
        """ Advance simulation time for each job in this machine """

        for job in self:
            job.advance_time(step)
            if job.state == COMPLETED:
                log.info("Completed job %s on %s", job, self)
                self.end_job(job)

    def __str__(self):

        return "%s (%d jobs) (%d/%d cpu) (%d/%d ram)" % \
               (self.name, len(self), self.cpus, self.totalcpus,
                self.memory, self.totalmemory)

    def long(self):
        s = "%s  (%d jobs) CPUs %2d (%2d) - RAM (%5d) %5d" % \
            (self.name, len(self), self.totalcpus - self.cpus, self.totalcpus,
             self.totalmemory - self.memory, self.totalmemory)
        if len(self) > 0:
            j = "\n    ".join(str(x) for x in self)
            return s + "\n    " + j
        else:
            return s
