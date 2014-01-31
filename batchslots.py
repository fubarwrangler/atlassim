#!/usr/bin/python

import os


IDLE = 0
RUNNING = 1
COMPLETED = 2

class BatchExcept(Exceptio):
    pass

groups = set(["prod", "mp8", "short", "long", "himem", "grid"])

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

    def __init__(self, cpus=24, memory=None):

        self.cpus = cpus
        self.totalcpus = cpus
        self.memory = memory if memory is not None else 1000 * 2 * cpus
        self.totalmemory = self.memory


class JobQueue(object):

    def __init__(self):
        self._q = list()

    def add_job(self, jobobj):
        self._q.append(jobobj)

    def


class BatchJob(object):
    """ Class representing one job for the batch system """
    def __init__(self, cpus=1, memory=2000, groups):
        self.cpus = cpus
        self.memory = memory
        self.state = IDLE





