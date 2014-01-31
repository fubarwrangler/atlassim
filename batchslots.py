#!/usr/bin/python

import os
import random


IDLE = 0
RUNNING = 1
COMPLETED = 2

class BatchExcept(Exception):
    pass

groups = {
    "prod": 3000, "mp8": 1000, "short": 600,
    "long": 600, "himem": 800, "grid": 40
}

total_quota = sum(groups.values())

siblings = [["short", "long"], ["prod", "mp8", "himem"], ["grid"]]


def get_siblings(group):
    if group not in groups:
        raise BatchExcept("Group %s not in groups" % group)
    for lst in siblings:
        if group in lst:
            return [x for x in lst if x != group]
    return []


class FarmNode(object):
    """ Class representing one machine in a compute cluster """

    def __init__(self, name, cpus=24, memory=None):

        self.name = name

        self.cpus = cpus
        self.totalcpus = cpus
        self.memory = memory if memory is not None else 1000 * 2 * cpus
        self.totalmemory = self.memory

        self._jobs = list()

    def start_job(self, job):
        self.cpus -= job.cpus
        self.memory -= job.memory

        job.slotid = len(self._jobs)
        job.state = RUNNING
        job.current_node = self.name

        self._jobs.append(job)

    def __str__(self):
        s = "%s  (%d jobs) CPUs %2d (%2d) - RAM (%5d) %5d" % \
            (self.name, len(self._jobs), self.totalcpus, self.cpus,
             self.totalmemory, self.memory)
        j = "\n    ".join(str(x) for x in self._jobs)
        return s + "\n    " + j



class BatchJob(object):
    """ Class representing one job for the batch system """

    def __init__(self, cpus=1, memory=None, group=None):
        self.cpus = cpus
        self.memory = memory if memory is not None else cpus * 2000
        self.group = group
        if group is not None and group not in groups:
            raise BatchExcept("Group %s not found" % group)

        self.current_node = None
        self.slotid = None
        self.state = IDLE

    @staticmethod
    def state_name(state):
        return ['I', 'R', 'C'][state]

    def __str__(self):
        s = "%2d-core  %5dRAM  %s" % (self.cpus, self.memory, self.state_name(self.state))
        if self.current_node and self.slotid is not None:
            s += "   (%s@%s)" % (self.slotid, self.current_node)
        return s


class JobQueue(object):

    def __init__(self):
        self._q = list()

    def add_job(self, jobobj):
        self._q.append(jobobj)

    def __str__(self):
        return "\n".join(map(str, self._q))

LinuxFarm = list()




